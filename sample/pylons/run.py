import os
import os.path
import paste.deploy
import fapws._evwsgi as evwsgi
from fapws import base
import sys
sys.setcheckinterval(100000) # since we don't use threads, internal checks are no more required

config_path = os.path.abspath(os.path.dirname(_args[0]))
path = '%s/%s' % (config_path, 'development.ini')
wsgi_app = paste.deploy.loadapp('config:%s' % path)

def start():
    evwsgi.start("0.0.0.0", 5000)
    evwsgi.set_base_module(base)
    
    def app(environ, start_response):
        environ['wsgi.multiprocess'] = False
        return wsgi_app(environ, start_response)

    evwsgi.wsgi_cb(('',app))
    evwsgi.run()

if __name__=="__main__": 
    start()
