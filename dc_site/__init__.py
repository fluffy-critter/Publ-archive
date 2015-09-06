from flask import Flask, send_from_directory, render_template
from dc_common import model
from dc_site.caching import cache, make_key
import os
import config
import base64
import logging
import logging.handlers

app = Flask(__name__.split('.')[0], static_folder=config.static_root_dir, static_url_path=config.static_url_path)
cache.init_app(app)

# Set up the logger
log_handler = logging.handlers.TimedRotatingFileHandler('tmp/flask.log')
log_handler.setLevel(logging.DEBUG)
log_handler.setFormatter(logging.Formatter(
    '%(asctime)s %(levelname)s: %(message)s '
    '[in %(pathname)s:%(lineno)d]'
))
app.logger.addHandler(log_handler)

# Set the session key
app.secret_key = model.Global.get_or_create(key='sessionKey', defaults={
    "string_value": base64.b64encode(os.urandom(24))
    })[0].string_value

### Add your routing rules here

@app.route('/')
@cache.cached(timeout=3600,key_prefix=make_key)
def main_page():
    return render_template('index.html')



# Fallback for static content; note that this is just for local server development, as in the Dreamhost
# environment the existence of the static content will override Passenger entirely.
@app.route('/<path:filename>')
def static_content(filename):
    return send_from_directory(config.static_root_dir, filename)
