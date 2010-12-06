#!/usr/bin/env python
# -*- coding: utf-8 -*-

from time import time
import fapws._evwsgi as evwsgi
from fapws import base

def start():
    evwsgi.start("0.0.0.0", "8080")
    evwsgi.set_base_module(base)

    def return_file(environ, start_response):
        start_response('200 OK', [('Content-Type','text/html')])
        return open('big-file')

    def return_tuple(environ, start_response):
        start_response('200 OK', [('Content-Type','text/plain')])
        return ('Hello,', " it's me ", 'Bob!')

    def return_rfc_time(environ, start_response):
        start_response('200 OK', [('Content-Type','text/plain')])
        return [evwsgi.rfc1123_date(time())]

    evwsgi.wsgi_cb(("/file", return_file))
    evwsgi.wsgi_cb(("/tuple", return_tuple))
    evwsgi.wsgi_cb(("/time", return_rfc_time))

    evwsgi.run()

if __name__=="__main__":
    try:
        open('big-file')
    except IOError:
        open('big-file', 'w').write('\n'.join('x'*1024 for i in range(1024)))
    start()
