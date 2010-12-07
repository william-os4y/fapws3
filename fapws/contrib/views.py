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


class Staticfile:
    """ Generic class that you can use to dispatch static files
    You must use it like this:
      static=Staticfile("/rootpath/")
      evhttp.http_cb("/static/",static)
    NOTE: you must be consistent between /rootpath/ and /static/ concerning the ending "/"
    """
    def __init__(self, rootpath="", maxage=None):
        self.rootpath = rootpath
        self.maxage = maxage

    def __call__(self, environ, start_response):
        fpath = self.rootpath + environ['PATH_INFO']
        try:
            f = open(fpath, "rb")
        except:
            print "ERROR in Staticfile: file %s not existing" % (fpath)
            start_response('404 File not found', [])
            return []
        fmtime = os.path.getmtime(fpath)
        if environ.get('HTTP_IF_NONE_MATCH', 'NONE') != str(fmtime):
            headers = []
            if self.maxage:
                headers.append(('Cache-control', 'max-age=%s' % int(self.maxage + time.time())))
            #print "NEW", environ['fapws.uri']
            ftype = mimetypes.guess_type(fpath)[0]
            headers.append(('Content-Type', ftype))
            headers.append(('ETag', fmtime))
            headers.append(('Content-Length', os.path.getsize(fpath)))
            start_response('200 OK', headers)
            return f
        else:
            #print "SAME", environ['fapws.uri']
            start_response('304 Not Modified', [])
            return []
