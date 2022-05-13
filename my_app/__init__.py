from flask import Flask, jsonify, request, render_template, Response, json, jsonify, redirect, url_for
import boto3
import botocore
from datetime import datetime, timedelta

app = Flask(__name__)
app.config['SECRET_KEY'] = '1fabace46bcf5b6eebda3de7'
app.config['PERMANENT_SESSION_LIFETIME'] =  timedelta(minutes=30)

app.config['AWS_CONFIGURE'] = {
    "aws_access_key_id": "ASIAW6QAURS4XRXRW4XU",
    "aws_secret_access_key": "Xwuyt0CQ03CJuqqqYf61mDZAdpYLQPvY0YkCkHe5",
    "aws_session_token": "FwoGZXIvYXdzEJH//////////wEaDKfb9zvQufwQT5gJTiLPAWdbqR1KeJkTBYsukMHGkaJZpmoExaol03N8LQRpBJHWxAYK02QYPNKF5cTkDZy+lLmhujkag69qCbpHdsBdbo9xZdsylkxpKaArLgHFyrHUBhCFHR+TI+iAofpDCyHlNIH60tfa1YoP1ckUMHIosYdWy5ZVAvfyhZibUuSItwEjz9A2yH7GagA+dfAkfZwV4GPGwbR36fdN+ZTGPH/jZFgetjDc4S+Srs0xSN5hWFikylm+WNPrWci8ZQV8YZ7OkVnjNsKjBygxXAD9bg8A1yj3kfiTBjItpCCNmqmLLT6znSH0uKmphiOPuW1jKu9YlU2sQxmYNyOlWEdNX99DNbpDeM2j",
    'region_name': 'us-east-1'
}


client = boto3.client('dynamodb',aws_access_key_id=app.config["AWS_CONFIGURE"]["aws_access_key_id"], 
    aws_secret_access_key=app.config["AWS_CONFIGURE"]["aws_secret_access_key"], 
    aws_session_token=app.config["AWS_CONFIGURE"]["aws_session_token"], 
    region_name=app.config["AWS_CONFIGURE"]["region_name"]
)
resource = boto3.resource('dynamodb',aws_access_key_id=app.config["AWS_CONFIGURE"]["aws_access_key_id"], 
    aws_secret_access_key=app.config["AWS_CONFIGURE"]["aws_secret_access_key"], 
    aws_session_token=app.config["AWS_CONFIGURE"]["aws_session_token"], 
    region_name=app.config["AWS_CONFIGURE"]["region_name"]
)


from my_app import routes
from my_app import api
from my_app import admin
from my_app import first_init

