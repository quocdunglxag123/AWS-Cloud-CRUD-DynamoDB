from my_app import app, client, resource
from flask import Flask, flash, jsonify, request, render_template, Response, json, jsonify, redirect, url_for, make_response,session
from boto3.dynamodb.conditions import Key


def table_already_exists(table_name):
	existing_tables = client.list_tables()['TableNames']
	if table_name not in existing_tables:
		return False
	return True

def query_table(table_name, key=None, value=None):
	table = resource.Table(table_name)
	if key is not None and value is not None:
		filtering_exp = Key(key).eq(value)
		return table.query(KeyConditionExpression=filtering_exp)

	raise ValueError('Parameter missing or invalid')

def create_user(user_name, public_id, email_address, password):
    table = resource.Table('user_table')
    response = table.put_item(
        Item={
            'user_name': user_name,
            'public_id': public_id,
            'email_address': email_address,
            'password': password,
            'is_admin': False
        }
    )
    return response

# def get_tables(current_user):
#     public_id = current_user['public_id']
#     get_tables = get_all_table_by_public_id(public_id)
#     list_tables = []
#     for table in get_tables:
#         item = client.describe_table(TableName=str(table['table_name'] + '-' + public_id))
#         item['Table']['TableName'] = item['Table']['TableName'].split('-' + public_id)[0]
#         list_tables.append(item)

#     return list_tables

def get_tables(current_user):
    public_id = current_user['public_id']
    existing_tables = client.list_tables()['TableNames']
    list_tables = []
    for table_name in existing_tables:
        sep = table_name.split('-' + public_id)
        if len(sep) > 1 and sep[1] == '':
            item = client.describe_table(TableName=table_name)
            item['Table']['TableName'] = item['Table']['TableName'].split('-' + public_id)[0]
            list_tables.append(item)
    return list_tables

def get_all_tables():
    existing_tables = client.list_tables()['TableNames']
    list_tables = []
    for table_name in existing_tables:
        item = client.describe_table(TableName=table_name)
        list_tables.append(item)
    return list_tables

def get_log_table():
    table = resource.Table('log_table')
    response = table.scan()
    data = response['Items']
    return data

def get_tables_by_user():
    all_tables = get_log_table()
    all_users = get_all_user()
    array = []
    except_table = ['user_table']
    for table in all_tables:
        u = {}
        if table['table_name'] not in except_table:
            u['Table'] = client.describe_table(TableName=table['table_name'] + '-' + table['public_id'])['Table']
            u['Created_by'] = all_users[table['public_id']]
            array.append(u)
        else:
            continue
    return array

def get_all_user():
    table = resource.Table('user_table')
    response = table.scan()
    data = response['Items']
    dict_all_user = {}
    for user in data:
        dict_all_user[user['public_id']] = user
    return dict_all_user


def not_exist_col(table_name, cols_in_rows_deleted):
    table = resource.Table(table_name)
    response = table.scan()
    data = response['Items']
    cols_not_exist = []
    for col in cols_in_rows_deleted:
        cols_not_exist.append(col)
        for item in response['Items']:
            if col in item:
                cols_not_exist.pop()
                break
    return cols_not_exist

def delete_cols_not_exist_data(table_name, public_id, cols, all_columns_current):
    table = resource.Table('log_table')
    for col in cols:
        if col in all_columns_current:
            all_columns_current.remove(col)
    table_name = table_name.split('-' + public_id)[0]
    response = table.put_item(
        Item={
            'public_id': public_id,
            'table_name': table_name,
            'columns': all_columns_current
        }
    )
    return response

def append_new_col_to_table(new_cols, table_name, public_id):
    table = resource.Table('log_table')
    result = table.update_item(
        TableName='log_table',
        Key={
            'public_id': public_id,
            'table_name': table_name
        },
        UpdateExpression='SET #attr= list_append(if_not_exists(#attr, :empty_list), :my_value)',
        ExpressionAttributeValues={
            ":my_value": new_cols,
            ":empty_list": []
        },
        ExpressionAttributeNames={
            "#attr": 'columns',
        },
        ReturnValues='UPDATED_NEW'
    )
    if result['ResponseMetadata']['HTTPStatusCode'] == 200 and 'Attributes' in result:
        return True
    else:
        return False

def get_all_table_by_public_id(public_id=None):
	query = query_table(table_name='log_table',key='public_id',value=public_id)
	return query.get('Items')
   



def get_all_columns(table_name, public_id):
    table = resource.Table('log_table')
    response = table.get_item(
        Key = {
            'public_id': public_id,
            'table_name': table_name
        }
    )
    return response['Item']['columns']

def get_items_table(table_name, public_id):
    table_name = table_name.split('-' + public_id)[0]
    table_name_origin = str(table_name + '-' + public_id)
    table = resource.Table(table_name_origin)
    response = table.scan()
    data = response['Items']
    columns = get_all_columns(table_name, public_id)
    return {'table': data, 'columns': columns, 'table_name': table_name_origin}
