#!/usr/bin/env python
# -*- coding: utf-8 -*-

import fapws._evwsgi as evwsgi
from fapws import base
import time
import sys
from fapws.contrib import views, zip, log



def env(environ, start_response):
    print environ
    start_response('200 OK', [('Content-Type','text/html')])
    res=[]
    for key,val in environ.items():
        val=str(val).replace('\r','\\r')
        val=val.replace('\n','\\n')
        res.append("%s:%s\n" % (key,val))
    return res

def hello(environ, start_response):
    start_response('200 OK', [('Content-Type','text/html')])
    return ["Hello world!!"]

def iteration(environ, start_response):
    start_response('200 OK', [('Content-Type','text/plain')])
    yield "Hello"
    yield " "
    yield "world!!"

@log.Log()
def staticlong(environ, start_response):
    try:
        f=open("long.txt", "rb")
    except:
        f=["Page not found"]
    start_response('200 OK', [('Content-Type','text/html')])
    return f

def embedlong(environ, start_response):
    try:
        c=open("long.txt", "rb").read()
    except:
        c=["Page not found"]
    start_response('200 OK', [('Content-Type','text/html')])
    return base.split_len(c,32768)

def staticshort(environ, start_response):
    f=open("short.txt", "rb")
    start_response('200 OK', [('Content-Type','text/html')])
    return f

def testpost(environ, start_response):
    print environ
    print "INPUT DATA",environ["wsgi.input"].getvalue()
    return ["OK. params are:%s" % (environ["fapws.params"])]

@zip.Gzip()    
def staticlongzipped(environ, start_response):
    try:
        f=open("long.txt", "rb")
    except:
        f=["Page not found"]
    start_response('200 OK', [('Content-Type','text/html')])
    return f

def badscript(environ, start_response):
    start_reponse('200 OK', [('Content-Type','text/html')])
    return ["Hello world!!"]




def start():
    evwsgi.start("0.0.0.0", "8080")
    evwsgi.set_base_module(base)
    
 
    evwsgi.wsgi_cb(("/env", env))
    evwsgi.wsgi_cb(("/hello", hello))
    evwsgi.wsgi_cb(("/iterhello", iteration))
    evwsgi.wsgi_cb(("/longzipped", staticlongzipped))
    evwsgi.wsgi_cb(("/long", staticlong))
    evwsgi.wsgi_cb(("/elong", embedlong))
    evwsgi.wsgi_cb(("/short", staticshort))
    staticform=views.Staticfile("test.html")
    evwsgi.wsgi_cb(("/staticform", staticform))
    evwsgi.wsgi_cb(("/testpost", testpost))
    evwsgi.wsgi_cb(("/badscript", badscript))

    evwsgi.set_debug(0)    
    evwsgi.run()
    

if __name__=="__main__":
    start()
