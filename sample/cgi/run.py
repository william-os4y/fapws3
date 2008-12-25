#!/usr/bin/env python

import fapws._evwsgi as evwsgi
from fapws import base
import time
import sys
sys.setcheckinterval=100000 # since we don't use threads, internal checks are no more required

from fapws.contrib import views, cgiapp

def start():
    evwsgi.start("0.0.0.0", 8080)
    
    evwsgi.set_base_module(base)
    
    hello=cgiapp.CGIApplication("./test.cgi")
    evwsgi.wsgi_cb(("/hellocgi",hello))
    testphp=cgiapp.CGIApplication("/tmp/test.php")
    evwsgi.wsgi_cb(("/testphp",testphp))
    
        
    evwsgi.run()
    

if __name__=="__main__":
    start()
