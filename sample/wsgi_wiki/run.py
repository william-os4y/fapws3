#!/usr/bin/env python

import fapws._evwsgi as evwsgi
import fapws
import fapws.base
import fapws.contrib
import fapws.contrib.views
import sys
sys.setcheckinterval=100000 # since we don't use threads, internal checks are no more required

import views

def start():
    evwsgi.start("0.0.0.0", 8085)
    
    evwsgi.set_base_module(fapws.base)
    
    #def generic(environ, start_response):
    #    return ["page not found"]
    
    def index(environ, start_response):
        print "GET:", environ['fapws.uri']
        return views.index(environ, start_response)
    
    def display(environ, start_response):
        print "GET:", environ['fapws.uri']
        return views.display(environ, start_response)
    def edit(environ, start_response):
        #print environ['fapws.params']
        print "GET:", environ['fapws.uri']
        r=views.Edit()
        return r(environ, start_response)
    favicon=fapws.contrib.views.Staticfile("static/img/favicon.ico")
    def mystatic(environ, start_response):
        print "GET:", environ['fapws.uri']
        s=fapws.contrib.views.Staticfile("static/")
        return s(environ, start_response)
    evwsgi.wsgi_cb(("/display/",display))
    evwsgi.wsgi_cb(("/edit", edit))
    evwsgi.wsgi_cb(("/new", edit))
    evwsgi.wsgi_cb(("/static/",mystatic))
    #evwsgi.wsgi_cb(('/favicon.ico',favicon)),

    evwsgi.wsgi_cb(("/", index))
    #evhttp.gen_http_cb(generic)
    evwsgi.set_debug(0)    
    evwsgi.run()
    

if __name__=="__main__":
    start()
