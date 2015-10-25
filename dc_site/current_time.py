from flask import request
import datetime
import pytz

def current_time():
    return datetime.datetime.now(pytz.utc)
