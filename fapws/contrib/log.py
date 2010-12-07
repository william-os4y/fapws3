# -*- coding: utf-8 -*-
#    Copyright (C) 2009 William.os4y@gmail.com
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, version 2 of the License.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
import time
import os
import sys


class Log:
    def __init__(self, output=sys.stdout):
        self.output = output

    def __call__(self, f):
        def func(environ, start_response):
            res = f(environ, start_response)
            tts = time.strftime("%d/%b/%Y:%H:%M:%S", time.gmtime())
            if type(res) is list:
                content = "".join(res)
                size = len(content)
            elif hasattr(res, "name"):
                #this is a filetype object
                size = os.path.getsize(res.name)
            else:
                size = "-"
            #this is provided by a proxy or direct
            remote_host = environ.get('HTTP_X_FORWARDED_FOR', environ['fapws.remote_addr'])
            self.output.write("%s %s - [%s GMT] \"%s %s %s\" %s %s \"%s\" \"%s\"\n" % (remote_host, environ['HTTP_HOST'], tts, environ['REQUEST_METHOD'], environ['fapws.uri'], environ['wsgi.url_scheme'],  start_response.status_code, size, environ.get("HTTP_REFERER", "-"), environ.get('HTTP_USER_AGENT', "-")))
            self.output.flush()
            return res
        return func
