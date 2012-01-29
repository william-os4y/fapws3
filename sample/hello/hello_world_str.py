#!/usr/bin/env python
# -*- coding: utf-8 -*-

import fapws._evwsgi as evwsgi
from fapws import basestr

def hello(environ, start_response):
    print(environ)
    start_response(b'200 OK', [(b'Content-Type',b'text/html')])
    return [b"Hello",b" world!!"]


def start():
    evwsgi.start("0.0.0.0", "8080")
    evwsgi.set_base_module(basestr)
    
 
    evwsgi.wsgi_cb((b"/hello", hello))

    evwsgi.set_debug(0)    
    evwsgi.run()
    

if __name__=="__main__":
    start()
