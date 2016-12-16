# -*- coding: utf-8 -*-
from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
import os
from os import listdir
from os.path import isfile, join
import random
import datetime

def files_in_dir(directory):
    """
    :param directory: The directory
    :return: List of all files in directory
    """
    return [f for f in listdir(directory) if isfile(join(directory,f))]

def random_string(length):
    """
    :param length: Legnth of the returned string
    :return: String og random characters
    """
    chars = 'QAZWSXEDCRFVTGBYHNUJMKLP23456789'
    return ''.join([random.choice(chars) for i in range(length)])

def is_christmas():
    now = datetime.datetime.now()
    if now.month != 12:
        return False
    if now.day < 30 and now.day > 10:
        return True
    return False
    
    
basedir = os.path.abspath(os.path.dirname(__file__))


app = Flask(__name__)

#app.config['CSRF_ENABLED'] = True
app.config['SECRET_KEY'] = '5d6d3e2u8d5g2D4S5DSF2sdf5s1df531sef'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'database.db')

db = SQLAlchemy(app)

app.jinja_env.globals.update(enumerate=enumerate, is_christmas=is_christmas)

from . import views, models

# Create database if it's not there
for file in files_in_dir(basedir):
    if 'database.db' in file:
        break
else:
    db.create_all()
    print('No DB. Creating....')

