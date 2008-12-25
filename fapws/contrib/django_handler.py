from django.core.handlers import wsgi 
import django

djhand=wsgi.WSGIHandler()
def handler(environ, start_response):
    res=djhand(environ, start_response)
    if django.VERSION[0]==0:
        for key,val in res.headers.items():
            start_response.response_headers[key]=val
    else:
        for key,val in res._headers.values():
            start_response.response_headers[key]=val
    start_response.cookies=res.cookies
    return res.content
