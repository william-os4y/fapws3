# -*- coding: utf-8 -*-
import fapws._evwsgi as evwsgi
from fapws import base

import time

count=0

def toto(v):
    global count
    time.sleep(v)
    count+=1
    print "defer sleep %s, counter %s, %s" % (v,count,evwsgi.defer_queue_size())

def application(environ, start_response):
    response_headers = [('Content-type', 'text/plain')]
    start_response('200 OK', response_headers)
    print "before defer", time.time()
    evwsgi.defer(toto, 0.2, False)
    #evwsgi.defer(toto, 1, True)
    print "after defer", time.time()
    return ["hello word!!"]
    
if __name__=="__main__":

    evwsgi.start("0.0.0.0", "8080")
    evwsgi.set_base_module(base)
    evwsgi.wsgi_cb(("/", application))
    evwsgi.set_debug(0)
    evwsgi.run()
