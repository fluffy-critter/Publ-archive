#!env/bin/python
# This might not be right, I'm just putting it together as an example for later
# see http://wiki.dreamhost.com/Flask for what looks like outdated information

import sys, os
INTERP = os.path.join(os.getcwd(), 'env', 'bin', 'python')
if sys.executable != INTERP:
    os.execl(INTERP, INTERP, *sys.argv)
sys.path.append(os.getcwd())
from dc_site import app

# hackish way to make Passenger urldecode the same way WSGI does
import urllib2
def application(environ, start_response):
    environ["PATH_INFO"] = urllib2.unquote(environ["PATH_INFO"])
    return app(environ, start_response)

# Uncomment next two lines to enable debugging
# from werkzeug.debug import DebuggedApplication
# application = DebuggedApplication(application, evalex=True)
