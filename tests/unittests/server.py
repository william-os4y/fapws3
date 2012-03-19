#!/usr/bin/env python
# -*- coding: utf-8 -*-

import fapws
import fapws._evwsgi as evwsgi
from fapws import base
import time
import sys
from fapws.contrib import views, zip, log
import mybase
import pprint
import platform

if len(sys.argv)>1 and sys.argv[1]=="socket":
  import socket
  socket_server = True
else:
  socket_server = False

def displaysystem(environ, start_response):
    start_response(b'200 OK', [(b'Content-Type',b'text/html')])
    res="""System: %s<br/>\nPython: %s<br/>\nFapws3: %s"""
    uname = " ".join(platform.uname())
    pyversion = platform.python_version()
    fapwsversion = fapws.version
    return [res % (uname, pyversion, fapwsversion)] 
    
def env(environ, start_response):
    start_response(b'200 OK', [(b'Content-Type',b'text/html')])
    res=[]
    pprint.pprint(environ)
    for key,val in environ.items():
        val=str(val).replace('\r','\\r')
        val=val.replace('\n','\\n')
        if sys.version_info[0] > 2:
            res.append(bytes("%s:%s\n" % (key,val), "utf-8"))
        else:
            res.append("%s:%s\n" % (key,val))
    return res

def hello(environ, start_response):
    start_response(b'200 OK', [(b'Content-Type',b'text/html')])
    return [b"Hello",b" world!!"]

class helloclass(object):
    def __init__(self, txt=None):
        self.content = ["Hello from class %s" % txt]
    def __call__(self, environ, start_response):
        start_response('200 OK', [('Content-Type','text/html')])
        return self.content

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
    if b"multipart/form-data" in environ['HTTP_CONTENT_TYPE']:
        environ["wsgi.input"].flush()
        environ["wsgi.input"].seek(0)
        res=environ["wsgi.input"].read()
    elif b"application/x-www-form-urlencoded" in environ['HTTP_CONTENT_TYPE']:
        res=environ["fapws.params"]
    else:
        res={}
    environ["wsgi.input"].close()
    ret = "OK. params are:%s" % (res)
    if sys.version_info[0] > 2:
        return [bytes(ret, "utf-8")]
    else:
        return [ret]

@zip.Gzip()    
def staticlongzipped(environ, start_response):
    try:
        f=open("long.txt", "rb")
    except:
        f=[b"Page not found"]
    start_response(b'200 OK', [(b'Content-Type',b'text/html')])
    return f

def badscript(environ, start_response):
    start_reponse(b'200 OK', [(b'Content-Type',b'text/html')])
    return [b"Hello world!!"]

def returnnone(environ, start_response):
    start_response(b'200 OK', [(b'Content-Type',b'text/html')])
    return None

def returnnull(environ, start_response):
    start_response(b'200 OK', [(b'Content-Type',b'text/html')])

def returniternull(environ, start_response):
    start_response(b'200 OK', [(b'Content-Type',b'text/html')])
    yield b"start"
    yield None
    yield b"tt"




def start():
    if socket_server:
        evwsgi.start("\0/org/fapws3/server", "unix")
    else:
        evwsgi.start("0.0.0.0", "8080")
    evwsgi.set_base_module(mybase)
    
 
    evwsgi.wsgi_cb((b"/env", env))
    evwsgi.wsgi_cb((b"/helloclass", helloclass("!!!")))
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
    evwsgi.wsgi_cb((b"/returnnone", returnnone))
    evwsgi.wsgi_cb((b"/returnnull", returnnull))
    evwsgi.wsgi_cb((b"/returniternull", returniternull))
    evwsgi.wsgi_cb((b"/system", displaysystem))

    evwsgi.set_debug(0)    
    evwsgi.run()
    

if __name__=="__main__":
    start()
