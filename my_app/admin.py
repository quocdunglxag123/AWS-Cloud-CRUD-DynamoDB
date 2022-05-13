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
from flask_admin import Admin
from my_app import admin
from flask_admin import AdminIndexView, expose, BaseView
from my_app.routes import login_required

class MyAdminIndexView(AdminIndexView):
	def is_visible(self):
		return False

	@expose('/')
	def index(self):	
		return redirect(url_for('tables.index')) 

class MyBaseView(BaseView):
	def render(self, template, **kwargs):
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
				if current_user['Item']['is_admin'] == False:
					return redirect(url_for('home_page'))
			self._template_args['current_user'] = current_user['Item']
			return super(MyBaseView,self).render(template, **kwargs)
		except:
			flash(f'Login session has expired!!! please login again.', category='danger')
			return redirect(url_for('login_page'))

class TableView(MyBaseView):
	@expose('/', methods=['GET'])
	def index(self):
		list_tables = get_all_tables()
		self._template_args['tables'] = list_tables
		return self.render('admin/index.html')

	@expose("/ajax-load-tables", methods=['GET'])
	def ajax_load_tables(self):
		return dict(html=self.render('admin/components/load-table.html'))
		

	def render(self, template, **kwargs):
		list_tables = get_tables_by_user()
		kwargs['log_table'] = list_tables
		return super(TableView,self).render(template, **kwargs)

class UserView(MyBaseView):
	@expose('/', methods=['GET'])
	def index(self):
		dict_all_user = get_all_user()
		list_users = []
		for key,value in dict_all_user.items():
			list_users.append(value)
		self._template_args['list_users'] = list_users
		return self.render('admin/list-user.html')

admin = Admin(app, name='Admin', index_view=MyAdminIndexView(), base_template='master.html', template_mode='bootstrap4')
admin.add_view(TableView(name='Tables', url='/admin/tables', endpoint='tables', menu_icon_type="ti", menu_icon_value="ti-server"))
admin.add_view(UserView(name='Users', url='/admin/list-user', endpoint='users', menu_icon_type="ti", menu_icon_value="ti-user"))

