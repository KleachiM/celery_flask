from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import config
# from celery import Celery

app = Flask(__name__)
app.config.from_mapping(SQLALCHEMY_DATABASE_URI=config.POSTGRE_URI)
db = SQLAlchemy(app)
