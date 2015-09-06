from flask import request
from flask.ext.cache import Cache
from config import cache_config

cache = Cache(config=cache_config)

def make_key():
    key = { 'path': request.path }
    # Which params to use (to avoid DoS); TODO we'll probably want to further whitelist allowed values in some way
    for arg in ['sort']:
        key['get_' + arg] = request.args.get(arg, None)
    return str(hash(frozenset(key.items())))
