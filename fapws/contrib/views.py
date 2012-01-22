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
import mimetypes
import os
import time
from fapws.compat import convert_to_bytes

class Staticfile:
    """ Generic class that you can use to dispatch static files
    You must use it like this:
      static=Staticfile("/rootpath/")
      evhttp.http_cb("/static/",static)
    NOTE: you must be consistent between /rootpath/ and /static/ concerning the ending "/"
    """
    def __init__(self, rootpath=b"", maxage=None):
        self.rootpath = rootpath
        self.maxage = maxage

    def __call__(self, environ, start_response):
        fpath = self.rootpath + environ['PATH_INFO']
        try:
            f = open(fpath, "rb")
        except:
            print("ERROR in Staticfile: file %s not existing" % (fpath))
            start_response('404 File not found', [])
            return []
        fmtime = os.path.getmtime(fpath)
        if environ.get('HTTP_IF_NONE_MATCH', b'NONE') != convert_to_bytes(fmtime):
            headers = []
            if self.maxage:
                headers.append((b'Cache-control', b'max-age=' + convert_to_bytes(int(self.maxage + time.time()))))
            #print "NEW", environ['fapws.uri']
            print("FPATH", fpath)
            ftype = mimetypes.guess_type(fpath.decode('utf8'))[0]
            headers.append((b'Content-Type', convert_to_bytes(ftype)))
            headers.append((b'ETag', convert_to_bytes(fmtime)))
            headers.append((b'Content-Length', convert_to_bytes(os.path.getsize(fpath))))
            start_response(b'200 OK', headers)
            return f
        else:
            #print "SAME", environ['fapws.uri']
            start_response(b'304 Not Modified', [])
            return []
