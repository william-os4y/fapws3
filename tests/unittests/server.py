#!/usr/bin/env python
# -*- coding: utf-8 -*-

import fapws._evwsgi as evwsgi
from fapws import base
import time
import sys
from fapws.contrib import views, zip, log
import mybase

if len(sys.argv)>1 and sys.argv[1]=="socket":
  import socket
  socket_server = True
else:
  socket_server = False


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
    return ["Hello"," world!!"]

class helloclass(object):
    def __init__(self, txt=None):
        self.content = ["Hello from class %s" % txt]
    def __call__(self, environ, start_response):
        start_response('200 OK', [('Content-Type','text/html')])
        return self.content

def iteration(environ, start_response):
    start_response('200 OK', [('Content-Type','text/plain')])
    yield "Hello"
    yield " "
    yield "world!!"

def tuplehello(environ, start_response):
    start_response('200 OK', [('Content-Type','text/html')])
    return ("Hello"," world!!")

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
    if "multipart/form-data" in environ['HTTP_CONTENT_TYPE']:
        res=environ["wsgi.input"].getvalue()
    elif "application/x-www-form-urlencoded" in environ['HTTP_CONTENT_TYPE']:
        res=environ["fapws.params"]
    else:
        res={}
    return ["OK. params are:%s" % (res)]

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

def returnnone(environ, start_response):
    start_response('200 OK', [('Content-Type','text/html')])
    return None

def returnnull(environ, start_response):
    print environ
    start_response('200 OK', [('Content-Type','text/html')])

def returniternull(environ, start_response):
    print environ
    start_response('200 OK', [('Content-Type','text/html')])
    yield "start"
    yield None
    yield "tt"




def start():
    if socket_server:
        evwsgi.start("\0/org/fapws3/server", "unix")
    else:
        evwsgi.start("0.0.0.0", "8080")
    evwsgi.set_base_module(mybase)
    
 
    evwsgi.wsgi_cb(("/env", env))
    evwsgi.wsgi_cb(("/helloclass", helloclass("!!!")))
    evwsgi.wsgi_cb(("/hello", hello))
    evwsgi.wsgi_cb(("/tuplehello", tuplehello))
    evwsgi.wsgi_cb(("/iterhello", iteration))
    evwsgi.wsgi_cb(("/longzipped", staticlongzipped))
    evwsgi.wsgi_cb(("/long", staticlong))
    evwsgi.wsgi_cb(("/elong", embedlong))
    evwsgi.wsgi_cb(("/short", staticshort))
    staticform=views.Staticfile("test.html")
    evwsgi.wsgi_cb(("/staticform", staticform))
    evwsgi.wsgi_cb(("/testpost", testpost))
    evwsgi.wsgi_cb(("/badscript", badscript))
    evwsgi.wsgi_cb(("/returnnone", returnnone))
    evwsgi.wsgi_cb(("/returnnull", returnnull))
    evwsgi.wsgi_cb(("/returniternull", returniternull))

    evwsgi.set_debug(1)    
    evwsgi.run()
    

if __name__=="__main__":
    start()
