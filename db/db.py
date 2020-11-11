import os
import threading

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

store = {}

basedir = os.path.abspath(os.path.dirname(__file__))
engine = create_engine('sqlite:///' + os.path.join(basedir, 'db.sqlite'))

Session = sessionmaker(bind=engine)
session = Session()

Base = declarative_base()

def create_session():
    """used to create a session in the same thread
    ued for api and concurrency
    """

    # store session based on thread id
    tid = threading.get_ident()
    if tid not in store:
        basedir = os.path.abspath(os.path.dirname(__file__))
        engine = create_engine('sqlite:///' + os.path.join(basedir, 'db.sqlite'))

        Session = sessionmaker(bind=engine)
        session = Session()

        Base = declarative_base()
        store[tid] = session
    return store[tid]