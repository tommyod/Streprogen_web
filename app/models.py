# -*- coding: utf-8 -*-
from app import db

class Program(db.Model):
    id = db.Column(db.Integer(), primary_key = True)
    unique_id = db.Column(db.String(32))
    date_creation = db.Column(db.DateTime())
    date_lastviewed = db.Column(db.DateTime())
    pickle = db.Column(db.PickleType())