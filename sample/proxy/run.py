# -*- coding: utf-8 -*-

#This is just an example of proxy with Fapws. 
#Just start it and add his adress (host:port) to the proxy parameter of your browser
#I've test it successfully with FireFox-3.6
#WARNING: does not work with Youtube videos


import fapws._evwsgi as evwsgi
import fapws
import fapws.basestr
import fapws.contrib
import fapws.contrib.views
import sys
import http.client
from fapws.compat import convert_to_bytes
import gzip


TIMEOUT=20


def get_header(head):
    headers={}
    lines=head.split("\n")
    lines.pop(0)
    for line in lines:
        line=line.strip()
        if line and ":" in line:
            key,val=line.split(":",1)
            headers[key.strip()]=val.strip()
    return headers



def generic(environ, start_response):
    if ":" in environ["HTTP_HOST"]:
        host,port=environ["HTTP_HOST"].split(":")
    else:
        host=environ["HTTP_HOST"]
        port=80
    con=http.client.HTTPConnection(host,port, timeout=TIMEOUT)
    print(environ["fapws.uri"])
    path=environ["fapws.uri"][len(host)+len(environ["wsgi.url_scheme"])+3:]
    params=environ["wsgi.input"].read()
    params=params.decode('utf8')
    headers=get_header(environ['fapws.raw_header'])
    #print("request methode  ", environ['REQUEST_METHOD'])
    #print("path             ", path)
    #print("PARAMS           ", params)
    #print("HEADERS          ", headers)
    con.connect()
    con.request(environ["REQUEST_METHOD"],path, params, headers)
    res=con.getresponse()
    content=res.read()
    resp_headers={}
    blocked=False
    for key,val in res.getheaders():
        resp_headers[key.upper()]=val
    if resp_headers.get('CONTENT-TYPE','').lower().startswith("text/html") and res.status==200:
        if "gzip" in resp_headers.get('CONTENT-ENCODING',''):
            data = gzip.decompress(content)
        else:
            data = content 
        if b"sex" in data: #we just block the page if the bad word is in it. It will not block compressed pages
            blocked = True
    if blocked:
        content=b"Page blocked"
    else:
        #we send back headers has we have received them
        start_response.status_code=convert_to_bytes(res.status) 
        start_response.status_reasons=convert_to_bytes(res.reason)
        for key, val in resp_headers.items():
            start_response.add_header(key,val)
    con.close()
    return [content]
    

def start():
    evwsgi.start("0.0.0.0", "8080")
    evwsgi.set_base_module(fapws.basestr)
    evwsgi.wsgi_cb(("",generic))
    evwsgi.set_debug(0)    
    print("libev ABI version:%i.%i" % evwsgi.libev_version())
    evwsgi.run()


if __name__=="__main__":
    start()

