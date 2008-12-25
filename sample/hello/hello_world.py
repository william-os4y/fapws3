#!/usr/bin/env python

import fapws._evwsgi as evwsgi
from fapws import base
import time
import sys
from fapws.contrib import views, zip, log

def start():
    evwsgi.start("0.0.0.0", 8080)
    evwsgi.set_base_module(base)
    
    def hello(environ, start_response):
        start_response('200 OK', [('Content-Type','text/html')])
        return ["hello world!!"]

    @log.Log()
    def staticlong(environ, start_response):
        try:
            f=open("long.txt", "rb")
        except:
            f=["Page not found"]
        start_response('200 OK', [('Content-Type','text/html')])
        return f
    def staticshort(environ, start_response):
        f=open("short.txt", "rb")
        start_response('200 OK', [('Content-Type','text/html')])
        return f
    def testpost(environ, start_response):
        print environ
        print "INPUT DATA",environ["wsgi.input"].getvalue()
        return ["OK. params are:%s" % (environ["fapws.params"])]

    @log.Log()
    @zip.Gzip()    
    def staticlongzipped(environ, start_response):
        try:
            f=open("long.txt", "rb")
        except:
            f=["Page not found"]
        start_response('200 OK', [('Content-Type','text/html')])
        return f
        

    
    evwsgi.wsgi_cb(("/hello", hello))
    evwsgi.wsgi_cb(("/longzipped", staticlongzipped))
    evwsgi.wsgi_cb(("/long", staticlong))
    evwsgi.wsgi_cb(("/short", staticshort))
    staticform=views.Staticfile("test.html")
    evwsgi.wsgi_cb(("/staticform", staticform))
    evwsgi.wsgi_cb(("/testpost", testpost))

    evwsgi.set_debug(0)    
    evwsgi.run()
    

if __name__=="__main__":
    start()