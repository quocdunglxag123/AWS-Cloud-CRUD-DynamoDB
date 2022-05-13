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




def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if session.get('access-token') is not None:
            token = session['access-token']

        if not token:
            
            return redirect(url_for('login_page'))

        try:
            data = jwt.decode(token, app.config['SECRET_KEY'])
            table = resource.Table('user_table')
            current_user = table.get_item(
                Key={
                    'user_name': data['user_name'],
                    'public_id': data['public_id']
                }
            )
            if request.path.split('/')[1] == 'admin':
                pass
            else:
                if current_user['Item']['is_admin']:
                    return redirect(url_for('admin.index'))
        except:
            flash(f'Login session has expired!!! please login again.', category='danger')
            return redirect(url_for('login_page'))

        return f(current_user['Item'], *args, **kwargs)
    return decorated

@app.route("/register", methods=['GET', 'POST'])
def register_page():
    form = RegisterForm()
    if form.validate_on_submit():
        public_id = str(uuid.uuid4())
        hashed_password = generate_password_hash(form.password.data, method='sha256')
        response = create_user(user_name=form.username.data, public_id=public_id, email_address=form.email_address.data, password=hashed_password)
        if response['ResponseMetadata']['HTTPStatusCode'] == 200:
            flash(f'Account created successfully! Please log in.', category='success')
            return redirect(url_for('login_page'))
        flash(f'Error! An error occurred. Please try again later', category='danger')
        return render_template('register.html', form=form)
    if form.errors != {}:
        for err_msg in form.errors.values():
            flash(f'There was an error with creating a user: {err_msg}', category='danger')
    return render_template('register.html', form=form)

@app.route("/login", methods=['GET', 'POST'])
def login_page():
    form = LoginForm()
    if form.validate_on_submit():
        table = resource.Table('user_table')
        user = table.query(
            IndexName='email_address-index',
            KeyConditionExpression=Key('email_address').eq(form.email_address.data)
        )
        if user.get('Count') and check_password_hash(user.get('Items')[0]['password'], form.password.data):
            user = user.get('Items')[0]
            token = jwt.encode({
                'public_id': user['public_id'],
                'user_name': user['user_name'],
                'exp': datetime.utcnow() + timedelta(minutes=60)
            }, app.config['SECRET_KEY'])
            session['logged-in'] = True
            session['access-token'] = token
            session.permanent = True
            
            flash(f'Success! You are logged in as: {user["user_name"]}', category='success')
            if user['is_admin']:
                return redirect(url_for('admin.index'))
            else:
                return redirect(url_for('home_page'))
        else:
            flash('Username and password are not match! Please try again', category='danger')
    
    return render_template('login.html', form=form)

@app.route("/logout")
def logout():
    if session.get('logged-in') is not None and session.get('access-token') is not None:
        session['logged-in'] = False
        session.pop('access-token')
        flash("You have been logged out! ", category='info')
    return redirect(url_for("home_page"))



@app.route("/")
@app.route("/tables")
@login_required
def home_page(current_user):
    user_name = current_user['user_name']
    return render_template('index.html', current_user=current_user)

@app.route("/tables/ajax-get", methods=['GET'])
@login_required
def ajax_load_tables(current_user):
    list_tables = get_tables(current_user)
    return dict(html=render_template('components/load-table.html', tables=list_tables), tables=list_tables)
    



@app.route("/tables/ajax-delete", methods=['POST'])
@login_required
def delete_tables(current_user):
    data = request.json
    public_id = current_user['public_id']
    url = 'https://sqs.us-east-1.amazonaws.com/477816458425/DeleteDynamoTableQueueProject'
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    for table in data['tables']:

        payload = {
                "tablename": str(table + '-' + public_id)
        }
        payload = quote(str(payload))
        params = {
            'Action': 'SendMessage',
            'MessageBody': payload
        }
        send = requests.post(url, headers=headers, params=params)

        log_table = resource.Table('log_table')
        response = log_table.delete_item(
            Key={
                'public_id': public_id,
                'table_name': table
            }
        )
        
    list_tables = get_tables(current_user)
    return dict(html=render_template('components/load-table.html', tables=list_tables), tables=list_tables)




@app.route('/items', methods=['POST'])
@login_required
def ajax_base_html_table(current_user):
    table_name = request.json['table_name']
    public_id = current_user['public_id']
    if table_name:
        get_items = get_items_table(table_name,public_id)
        return dict(html=render_template('components/load-data-table.html', table_name=get_items['table_name']))
    else:
        return Response(
            json.dumps({'error': 'invalid'}),
            status=400,
            mimetype='application/json'
        )
@app.route('/items/get-data', methods=['POST'])
@login_required
def ajax_load_items_table(current_user):
    table_name = request.json['table_name']
    public_id = current_user['public_id']
    if table_name:
        get_items = get_items_table(table_name, public_id)
        return dict(html=render_template('components/reload-items-table.html', table=get_items['table'], columns=get_items['columns'], table_name=get_items['table_name']), table=get_items['table'], columns=get_items['columns'])
    else:
        return Response(
            json.dumps({'error': 'invalid'}),
            status=400,
            mimetype='application/json'
        )



@app.route('/items')
@login_required
def items_page(current_user):
    list_tables = get_all_table_by_public_id(current_user['public_id'])
    return render_template('items.html', list_tables=list_tables, current_user=current_user)

@app.route("/edit-item")
@login_required
def edit_item_page(current_user):
    table_name_origin = request.args.get('table-name')
    public_id = current_user['public_id']
    table_name = table_name_origin.split('-' + public_id)[0]
    all_columns = get_all_columns(table_name,public_id)
    data = client.describe_table(TableName=table_name_origin)
    data = data['Table']
    list_key = []
    for keySchema in data['KeySchema']:
        for attr in reversed(data['AttributeDefinitions']):
            if keySchema['AttributeName'] == attr['AttributeName']:
                key = {}
                key['AttributeName'] = keySchema['AttributeName']
                key['AttributeType'] = attr['AttributeType']
                list_key.append(key)
                break

    return render_template('edit-item.html',table_name=table_name, data=data, list_key=list_key, all_columns=all_columns, current_user=current_user)  

@app.route("/edit-item/ajax-delete-item", methods=['POST'])
@login_required
def ajax_delete_item(current_user):
    data = request.json
    indexes = data['items']
    table = resource.Table(data['table_name'])
    response = table.scan()
    items = response['Items']

    rows = []
    for i in indexes:
        rows.append(items[int(i)])

    all_columns = data['columns']
    # Get all columns exists in list rows deleted
    cols = []
    for row in rows:
        for key, value in row.items():
            if key in cols:
                continue
            else:
                cols.append(key)
    records_to_delete = []
    for row in rows:
        record = {}
        for i in range(0,2):
            record[all_columns[i]] = row[all_columns[i]]
        records_to_delete.append(record)
    
    table = resource.Table(data['table_name'])
    for record in records_to_delete:
        try:
            response = table.delete_item(Key=record)

        except botocore.exceptions.ClientError as err:

            return Response(
                json.dumps({'Error Message': err.response['Error']['Message']}),
                status=err.response['ResponseMetadata']['HTTPStatusCode'],
                mimetype='application/json'
            )
    # if delete rows successfully, delete columns not have data in table
    if response['ResponseMetadata']['HTTPStatusCode'] == 200:
        delete_cols = not_exist_col(data['table_name'], cols)
        if len(delete_cols) != 0:
            response = delete_cols_not_exist_data(data['table_name'],current_user['public_id'], delete_cols, all_columns)

        return Response(
            json.dumps({'msg': "Deleted a record successfully", 'category_msg': 'success'}),
            status=200,
            mimetype='application/json'
        )


@app.route("/edit-item/ajax-edit-item", methods=['POST'])
@login_required
def ajax_edit_item(current_user):
    data = request.json
    public_id = current_user['public_id']
    table_name = str(data['table_name'] + '-' + public_id)
    existing_tables = client.list_tables()['TableNames']
    # Get all columns current in table target
    all_columns_current = get_all_columns(data['table_name'], public_id)
    new_cols = []
    for attribute,value in data['data'].items():
        if attribute not in all_columns_current:   
            new_cols.append(attribute)

    if table_name in existing_tables:
        table = resource.Table(table_name)
        if request.method == 'POST' or request.method == 'PUT':
            try:
                response = table.put_item(Item=data['data'])
                # check if user input new attibute to table
                if len(new_cols) > 0:
                    append = append_new_col_to_table(new_cols, data['table_name'], public_id)
                # if append return true, success add new col to log table
                
                return Response(
                    json.dumps({'response': 'response'}),
                    status=200,
                    mimetype='application/json'
                )
            except botocore.exceptions.ClientError as err:

                return Response(
                    json.dumps({'Error Message': err.response['Error']['Message']}),
                    status=err.response['ResponseMetadata']['HTTPStatusCode'],
                    mimetype='application/json'
                )
        else:
            return Response(
                json.dumps({"Error Message": "bad request."}),
                status=400,
                mimetype='application/json'
            ) 
    else:
        return Response(
            json.dumps({"Error Message": "table not existings."}),
            status=400,
            mimetype='application/json'
        )

@app.route("/create-tables", methods=["POST", "GET"])
@login_required
def create_tables_page(current_user):
    form = CreateTableForm()
    
    if request.method == "POST":
        table_name = request.form.get('table_name') + '-' + current_user['public_id']
        existing_tables = client.list_tables()['TableNames']
        if table_name not in existing_tables:
            partition_key = request.form.get('partition_key')
            sort_key = request.form.get('sort_key')
            columns = []

            columns.append(partition_key)
            if sort_key != '':
                columns.append(sort_key)

            log_table = resource.Table('log_table')
            response = log_table.put_item(
                Item={
                    'public_id': current_user['public_id'],
                    'table_name': request.form.get('table_name'),
                    'columns': columns
                }
            )

            url = "https://sqs.us-east-1.amazonaws.com/477816458425/CreateDynamoTableQueueProject"
            headers = {"Content-Type": "application/x-www-form-urlencoded"}
            
            payload = {
                "tablename": table_name,
                "keyHash": partition_key,
                "keyHash_type": "HASH",
                "PartitionKey": partition_key,
                "PartitionKey_type": request.form.get('partition_key_type'),
                "keyRange": sort_key,
                "keyRange_type": "RANGE",
                "SortKey": sort_key,
                "SortKey_type": request.form.get('sort_key_type')
            }
            payload = quote(str(payload))
            params = {
                'Action': 'SendMessage',
                'MessageBody': payload
            }
            
            send = requests.post(url, headers=headers, params=params)

            
            return redirect(url_for('home_page'))
            
        else:
            flash(f'A table with the same name already exists. Table names in the same account and same AWS Regions must be unique.', category='danger')
        
    return render_template('create-tables.html', form=form, current_user=current_user)    


from my_app import admin