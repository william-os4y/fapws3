
import time
import os.path
import sys

class Trace:
    def __init__(self):
        self.pp=4
    def __call__(self, f):
        def func(environ, start_response):
            res=f(environ, start_response)
            if environ['REQUEST_METHOD']==b"TRACE":
                res=[]
                for elem in environ.keys():
                    res.append("%s: %s\r\n" % (elem, str(environ[elem])))
            return res

        return func
    
