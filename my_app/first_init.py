from my_app import app, client, resource
from flask import Flask, flash, jsonify, request, render_template, Response, json, jsonify, redirect, url_for, make_response,session
import urllib3
import requests
from urllib.parse import quote

def create_log_table():
	table_name = 'log_table'
	existing_tables = client.list_tables()['TableNames']
	if table_name not in existing_tables:
		
		try:
			response = client.create_table(
				AttributeDefinitions=[
					{
						'AttributeName': 'public_id',
						'AttributeType': 'S'
					},
					{
						'AttributeName': 'table_name',
						'AttributeType': 'S'
					},
				],
				TableName=table_name,
				KeySchema=[
					{
						'AttributeName': 'public_id',
						'KeyType': 'HASH'
					},
					{
						'AttributeName': 'table_name',
						'KeyType': 'RANGE'
					}
				],
				BillingMode='PAY_PER_REQUEST',
			)
			print("Created table log_table successfully")
			return response
		except Exception as e:
			print(e)
	else:
		print('A table with the same name already exists. Table names in the same account and same AWS Regions must be unique.')

def create_user_table():
	table_name = 'user_table'
	existing_tables = client.list_tables()['TableNames']
	if table_name not in existing_tables:
		partition_key = 'user_name'
		sort_key = 'public_id'
		try:
			response = client.create_table(
				AttributeDefinitions=[
					{
						'AttributeName': 'user_name',
						'AttributeType': 'S'
					},
					{
						'AttributeName': 'public_id',
						'AttributeType': 'S'
					},
					{
						'AttributeName': 'email_address',
						'AttributeType': 'S'
					}
				],
				TableName=table_name,
				KeySchema=[
					{
						'AttributeName': 'user_name',
						'KeyType': 'HASH'
					},
					{
						'AttributeName': 'public_id',
						'KeyType': 'RANGE'
					}
				],
				GlobalSecondaryIndexes=[
					{
						'IndexName': 'email_address-index',
						'KeySchema': [
							{
								'AttributeName': 'email_address',
								'KeyType': 'HASH'
							},
						],
						'Projection': {
							'ProjectionType': 'ALL',
						},
						
					},
				],
				BillingMode='PAY_PER_REQUEST',
			)
			print("Created table user_table successfully")
			return response
		except Exception as e:
			print(e)
	else:
		print('A table with the same name already exists. Table names in the same account and same AWS Regions must be unique.')

def run():
	create_user_table()
	create_log_table()
	  