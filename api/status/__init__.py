import os
from functools import wraps

from flask import Blueprint, jsonify, request
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from db.models import ChimeraConfig

status_bp = Blueprint('status_bp', __name__)


basedir = os.path.join(os.path.dirname(__file__), '..', '..', 'db')
engine = create_engine('sqlite:///' + os.path.join(basedir, 'db.sqlite?check_same_thread=False'))
session = scoped_session(sessionmaker(bind=engine))

cc = session.query(ChimeraConfig).first()
API_TOKEN = cc.api_token

def tokenrequired(f):
    # this should be in api.__init__
    @wraps(f)
    def wrap(*args, **kwargs):
        token = request.headers.get('X-Auth-Token')
        if token:
            if token == API_TOKEN:
                return f(*args, **kwargs)
        return jsonify(error='INVALID API TOKEN')
    return wrap


from . import views