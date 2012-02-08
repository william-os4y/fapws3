# -*- coding: utf-8 -*-

import os.path
import string
import time
from cgi import parse_qs
import urllib
import sys
if sys.version_info[0] > 2:
    import http.client as http_client
else:
    import httplib as http_client

from fapws.contrib.headers import redirect

repository = "repository"
menu = """<a href="/index"><img border="0" src="/static/img/house.png" title="Back to home page"/></a>"""
def get_status(code):
    return "%s %s" % (code, http_client.responses[code])

def convert2str(data):
    if sys.version_info[0] > 2:
        return data.decode('utf-8')
    else:
        return data

def display(environ, start_response):
    page = convert2str(environ['PATH_INFO'])
    page = os.path.normpath(page.replace('..',''))
    if page[0] not in string.ascii_letters:
        errormsg = b"Error: the asked page does not exist"
        #put message in a session
        print(errormsg)
        return redirect(start_response, '/')
    filepage = os.path.join(repository,page)
    if not os.path.isfile(filepage):
        return redirect(start_response, '/edit?page=%s' % page)
    content = open(filepage,"rb").read()
    scontent = convert2str(content)
    mnu = menu + """, <a href="/edit?page=%s"><img border="0" src="/static/img/application_edit.png"title="Edit this page"/></a>""" % page
    tmpl = string.Template(open('template/display.html').read()).safe_substitute({'content':scontent,'page':page,'menu':mnu})
    start_response(get_status(200), [('Content-Type',"text/html; charset=utf-8")])
    return [tmpl]

class Edit:
    def __call__(self, environ, start_response):
        self.start_response = start_response
        self.environ = environ
        if environ['REQUEST_METHOD'] == b"POST":
            params=environ['fapws.params']
            page = params.get(b'page', [b''])[0]
            spage = convert2str(page)
            content = params.get(b'content', [b''])[0]
            return self.POST(spage,content)
        else:
            page = environ['fapws.params'].get(b'page', [b''])[0]
            spage = convert2str(page)
            return self.GET(spage)
    def POST(self, page="", content=b""):
        if page.strip() == "":
            msg = "ERROR!! Page cannot be empty"
            print("ERROR PAGE empty")
            return self.GET(page,msg)
        else:
            if content.strip() == b"":
                if os.path.isfile(os.path.join(repository, page)):
                    os.unlink(os.path.join(repository,page))
                return redirect(self.start_response, "/")
            else:
                fpath = os.path.join(repository,page)
                try:
                    f = open(fpath,"wb").write(content)
                except:
                    msg = "Error, wrong page name"
                    return self.GET(page,msg)
                return redirect(self.start_response, "/display/%s" % page)
    def GET(self, page="",msg=""):
        mnu = menu
        if page:
            mnu += """, <a href="/display/%s"><img border="0" src="/static/img/cancel.png" title="Cancel the editing" /></a>""" % page
        content = b""
        if page and os.path.isfile(os.path.join(repository,page)):
            content = open(os.path.join(repository,page),"rb").read()
        else:
            msg = "This page does not exist, do you want to create it?"
        scontent = convert2str(content)
        tmpl = string.Template(open('template/edit.html').read()).safe_substitute({'menu':mnu,'content':scontent,'page':page,'msg':msg})
        self.start_response(get_status(200), [('Content-Type','text/html; charset=utf-8')])    
        return [tmpl]

def index(environ, start_response):
    mnu = menu+ """, <a href="/new"><img border="0" src="/static/img/add.png" title="Add a new page"/></a>"""
    elems = ""
    for e in os.listdir(repository):
        if os.path.isfile(os.path.join(repository,e)):
            elems += """<li><a href="/display/%s">%s</a></li>""" % (e,e)
    tmpl = string.Template(open('template/index.html').read()).safe_substitute({'elems':elems,'menu':mnu})
    start_response(get_status(200), [('Content-Type','text/html')])
    return [tmpl]

