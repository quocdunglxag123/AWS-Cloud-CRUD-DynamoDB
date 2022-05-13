from my_app import app, client, resource
from flask import Flask, flash, jsonify, request, render_template, Response, json, jsonify, redirect, url_for, make_response,session
import urllib3
import requests
from urllib.parse import quote
from my_app.forms import CreateTableForm
from boto3.dynamodb.conditions import Key
import botocore
from my_app.forms import *
import uuid
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from datetime import datetime, timedelta
from functools import wraps
from my_app.function import *




def token_required(f):
	@wraps(f)
	def decorated(*args, **kwargs):
		token = None

		if 'x-access-token' in request.headers:
			token = request.headers['x-access-token']

		if not token:
			return jsonify({'message': 'Token is missing'}), 401

		try:
			data = jwt.decode(token, app.config['SECRET_KEY'])
			table = resource.Table('user_table')
			current_user = table.get_item(
				Key={
					'user_name': data['user_name'],
					'public_id': data['public_id']
				}
			)
		except:
			return jsonify({'message': 'Token is invalid!'}),401

		return f(current_user['Item'], *args, **kwargs)

	return decorated


@app.route("/api/table/<table_name>", methods=['GET'])
@token_required
def api_get_items(current_user,table_name):
	table_name = str(table_name + '-' + current_user['public_id'])
	if table_already_exists(table_name):
		table = resource.Table(table_name)
		response = table.scan()
		data = response['Items']
		return jsonify({'Items': data})
	return jsonify({'message': 'Not found table'}),404

@app.route('/api/table/<table_name>', methods=["DELETE"])
@token_required
def api_delete_items(current_user, table_name):
	data = request.json
	table_name_origin = str(table_name + '-' + current_user['public_id'])
	
	if table_already_exists(table_name_origin):
		table = resource.Table(table_name_origin)
		try:
			response = table.get_item(Key=data)
			if response.get('Item') is not None:
				item_deleted = response.get('Item')
				all_columns = get_all_columns(table_name, current_user['public_id'])
				cols = []
				for key, value in item_deleted.items():
					cols.append(key)

				try:
					response = table.delete_item(Key=data)
					delete_cols = not_exist_col(table_name_origin, cols)
					if len(delete_cols) != 0:
						response = delete_cols_not_exist_data(table_name, current_user['public_id'], delete_cols, all_columns)
					return jsonify({'message': 'Deleted a record successfully'}), 200
				except botocore.exceptions.ClientError as err:
					return jsonify({'Error Message': err.response['Error']['Message']}),err.response['ResponseMetadata']['HTTPStatusCode']

			else:
				return jsonify({'message': 'Not found item to delete'}), 404
		except botocore.exceptions.ClientError as err:
			return jsonify({'Error Message': err.response['Error']['Message']}),err.response['ResponseMetadata']['HTTPStatusCode']

	else:
		return jsonify({'message': 'Not found table'}),404

@app.route('/api/table/<table_name>', methods=["POST", "PUT"])
@token_required
def api_edit_items(current_user, table_name):
	data = request.json
	all_columns_current = get_all_columns(table_name, current_user['public_id'])
	new_cols = []
	for attribute,value in data.items():
		if attribute not in all_columns_current:   
			new_cols.append(attribute)

	table_name_origin = str(table_name + '-' + current_user['public_id'])
	if table_already_exists(table_name_origin):
		table = resource.Table(table_name_origin)
		try:
			response = table.put_item(Item=data)
			if len(new_cols) > 0:
				append = append_new_col_to_table(new_cols, table_name, current_user['public_id'])
			return Response(
				json.dumps({"message": 'Edited successfully'}),
				status=200,
				mimetype='applicationl/json'
			)
		except botocore.exceptions.ClientError as err:
			return jsonify({'Error Message': err.response['Error']['Message']}),err.response['ResponseMetadata']['HTTPStatusCode']
	else:
			
		return jsonify({'message': 'Not found table'}),404

@app.route("/api/authorization")
def api_auth():
	auth = request.authorization

	if not auth or not auth.username or not auth.password:
		return make_response('Could not verify', 401, {"WWW-Authenticate": 'Basic realm="Login required!"'})

	table = resource.Table('user_table')
	user = table.query(
		IndexName='email_address-index',
		KeyConditionExpression=Key('email_address').eq(auth.username)
	)
	if user.get('Count') and check_password_hash(user.get('Items')[0]['password'], auth.password):
		user = user.get('Items')[0]
		token = jwt.encode({
			'public_id': user['public_id'],
			'user_name': user['user_name'],
			'exp': datetime.utcnow() + timedelta(minutes=60)
		}, app.config['SECRET_KEY'])

		return jsonify({'token': token.decode('UTF-8')})

	return make_response('Could not verify', 401, {'WWW-Authenticate': 'Basic realm="Login required!"'})
