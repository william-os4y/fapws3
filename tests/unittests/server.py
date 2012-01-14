#!/usr/bin/env python
# -*- coding: utf-8 -*-

import fapws._evwsgi as evwsgi
from fapws import base
import time
import sys
from fapws.contrib import views, zip, log
import mybase


def env(environ, start_response):
    start_response('200 OK', [('Content-Type','text/html')])
    res=[]
    print("PY env",environ)
    for key,val in environ.items():
        val=str(val).replace('\r','\\r')
        val=val.replace('\n','\\n')
        res.append(bytes("%s:%s\n" % (key,val),"utf-8"))
    print("PY RES:%s" % res)
    return res

def hello(environ, start_response):
    start_response('200 OK', [('Content-Type','text/html')])
    return [b"Hello",b" world!!"]

def iteration(environ, start_response):
    start_response('200 OK', [('Content-Type','text/plain')])
    yield b"Hello"
    yield b" "
    yield b"world!!"

def tuplehello(environ, start_response):
    start_response('200 OK', [('Content-Type','text/html')])
    return (b"Hello",b" world!!")

@log.Log()
def staticlong(environ, start_response):
    try:
        f=open("long.txt", "rb")
    except:
        f=[b"Page not found"]
    start_response('200 OK', [('Content-Type','text/html')])
    return f

def embedlong(environ, start_response):
    try:
        c=open("long.txt", "rb").read()
    except:
        c=[b"Page not found"]
    start_response('200 OK', [('Content-Type','text/html')])
    return base.split_len(c,32768)

def staticshort(environ, start_response):
    f=open("short.txt", "rb")
    start_response('200 OK', [('Content-Type','text/html')])
    return f

def testpost(environ, start_response):
    print(environ)
    if "multipart/form-data" in environ['HTTP_CONTENT_TYPE']:
        res=environ["wsgi.input"].getvalue()
    elif "application/x-www-form-urlencoded" in environ['HTTP_CONTENT_TYPE']:
        res=environ["fapws.params"]
    else:
        res={}
    return [bytes("OK. params are:%s" % (res),"utf-8")]

@zip.Gzip()    
def staticlongzipped(environ, start_response):
    try:
        f=open("long.txt", "rb")
    except:
        f=[b"Page not found"]
    start_response('200 OK', [('Content-Type','text/html')])
    return f

def badscript(environ, start_response):
    start_reponse('200 OK', [('Content-Type','text/html')])
    return [b"Hello world!!"]




def start():
    evwsgi.start("0.0.0.0", "8080")
    evwsgi.set_base_module(mybase)
    
 
    evwsgi.wsgi_cb(("/env", env))
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

    evwsgi.set_debug(1)    
    evwsgi.run()
    

if __name__=="__main__":
    start()
