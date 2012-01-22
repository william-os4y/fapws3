#!/usr/bin/env python
# -*- coding: utf-8 -*-

import fapws._evwsgi as evwsgi
from fapws import base
import time
import sys
from fapws.contrib import views, zip, log
import mybase


def env(environ, start_response):
    start_response(b'200 OK', [(b'Content-Type',b'text/html')])
    res=[]
    print("PY env",environ)
    for key,val in environ.items():
        val=str(val).replace('\r','\\r')
        val=val.replace('\n','\\n')
        res.append(bytes("%s:%s\n" % (key,val),"utf-8"))
    print("PY RES:%s" % res)
    return res

def hello(environ, start_response):
    start_response(b'200 OK', [(b'Content-Type',b'text/html')])
    return [b"Hello",b" world!!"]

def iteration(environ, start_response):
    start_response('200 OK', [('Content-Type','text/plain')])
    yield b"Hello"
    yield b" "
    yield b"world!!"

def tuplehello(environ, start_response):
    start_response(b'200 OK', [(b'Content-Type',b'text/html')])
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
    if b"multipart/form-data" in environ[b'HTTP_CONTENT_TYPE']:
        res=environ[b"wsgi.input"].getvalue()
    elif b"application/x-www-form-urlencoded" in environ[b'HTTP_CONTENT_TYPE']:
        res=environ[b"fapws.params"]
    else:
        res={}
    ret = "OK. params are:%s" % (res)
    return [bytes(ret,"utf-8")]

@zip.Gzip()    
def staticlongzipped(environ, start_response):
    try:
        f=open("long.txt", "rb")
    except:
        f=[b"Page not found"]
    start_response(b'200 OK', [(b'Content-Type',b'text/html')])
    return f

def badscript(environ, start_response):
    start_reponse('200 OK', [('Content-Type','text/html')])
    return [b"Hello world!!"]




def start():
    evwsgi.start("0.0.0.0", "8080")
    evwsgi.set_base_module(mybase)
    
 
    evwsgi.wsgi_cb((b"/env", env))
    evwsgi.wsgi_cb((b"/hello", hello))
    evwsgi.wsgi_cb((b"/tuplehello", tuplehello))
    evwsgi.wsgi_cb((b"/iterhello", iteration))
    evwsgi.wsgi_cb((b"/longzipped", staticlongzipped))
    evwsgi.wsgi_cb((b"/long", staticlong))
    evwsgi.wsgi_cb((b"/elong", embedlong))
    evwsgi.wsgi_cb((b"/short", staticshort))
    staticform=views.Staticfile(b"test.html")
    evwsgi.wsgi_cb((b"/staticform", staticform))
    evwsgi.wsgi_cb((b"/testpost", testpost))
    evwsgi.wsgi_cb((b"/badscript", badscript))

    evwsgi.set_debug(0)    
    evwsgi.run()
    

if __name__=="__main__":
    start()
