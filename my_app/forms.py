from flask_wtf import FlaskForm
from wtforms import fields 
from wtforms.validators import Length, EqualTo, DataRequired, ValidationError, Email
from boto3.dynamodb.conditions import Key
from my_app import client, resource
import re
from my_app.function import *

class CreateTableForm(FlaskForm):

	def validate_table_name(self, table_name_to_check):
		regex = re.compile("[^a-zA-Z0-9_.-]")
		match = regex.match(table_name_to_check)
		if match:
			raise ValidationError("Invalid input")


	table_name = fields.StringField(label='Table name', validators=[DataRequired(), Length(min=3, max=255)])
	partition_key = fields.StringField(label='Partition Key', validators=[DataRequired(), Length(min=1, max=255)])
	partition_key_type = fields.SelectField("Type: ", choices=[('S','String'), ('N','Number'), ('B','Binary')])
	sort_key = fields.StringField(label='Sort Key - Optional', validators=[Length(min=0, max=255)])
	sort_key_type = fields.SelectField("Type: ", choices=[('S','String'), ('N','Number'), ('B','Binary')])
	submit = fields.SubmitField(label='Lưu')


class RegisterForm(FlaskForm):

	def validate_username(self, username_to_check):
		user = query_table(table_name='user_table', key='user_name', value=username_to_check.data).get('Count')
		if user:
			raise ValidationError('Username already exists! Please try a different username')

	def validate_email_address(self, email_address_to_check):
		table = resource.Table('user_table')
		email_address = table.query(
			IndexName='email_address-index',
			KeyConditionExpression=Key('email_address').eq(email_address_to_check.data)
		).get('Count')
		if email_address:
			raise ValidationError('Email Address already exists! Please try a different email address')


	username = fields.StringField(label='User Name', validators=[Length(min=2, max=30), DataRequired()])
	email_address = fields.StringField(label='Email Address', validators=[Email(), DataRequired()])
	password = fields.PasswordField(label='Password', validators=[Length(min=8, max=60), DataRequired()])
	confirm_password = fields.PasswordField(label='Confirm Password', validators=[EqualTo('password'), DataRequired()])
	submit = fields.SubmitField(label='Sign up now.')

class LoginForm(FlaskForm):
	email_address = fields.StringField(label='Email Address', validators=[DataRequired()])
	password = fields.PasswordField(label='Password:', validators=[Length(min=8, max=60), DataRequired()])
	submit = fields.SubmitField(label='Sign in')

