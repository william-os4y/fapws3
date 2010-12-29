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
import datetime
from Cookie import SimpleCookie, CookieError
try:
    import cStringIO as StringIO
except ImportError:
    import StringIO
import sys
import string
import traceback
import time

import config
import httplib


def get_status(code):
    return "%s %s" % (code, httplib.responses[code])


class Environ(dict):
    def __init__(self, *arg, **kw):
        self['wsgi.version'] = (1, 0)
        self['wsgi.errors'] = StringIO.StringIO()
        self['wsgi.input'] = StringIO.StringIO()
        self['wsgi.multithread'] = False
        self['wsgi.multiprocess'] = True
        self['wsgi.run_once'] = False
        self['fapws.params'] = {}
    #here after some entry point before the Environ update

    def update_headers(self, data):
        dict.update(self, data)

    def update_uri(self, data):
        dict.update(self, data)

    def update_from_request(self, data):
        dict.update(self, data)


class Start_response:
    def __init__(self):
        self.status_code = "200"
        self.status_reasons = "OK"
        self.response_headers = {}
        self.exc_info = None
        self.cookies = None
        # NEW -- sent records whether or not the headers have been send to the
        # client
        self.sent = False

    def __call__(self, status, response_headers, exc_info=None):
        self.status_code, self.status_reasons = status.split(" ", 1)
        self.status_code = str(self.status_code)
        for key, val in response_headers:
            #if type(key)!=type(""):
            key = str(key)
            #if type(val)!=type(""):
            val = str(val)
            self.response_headers[key] = val
        self.exc_info = exc_info  # TODO: to implement

    def add_header(self, key, val):
        key = str(key)
        val = str(val)
        self.response_headers[key] = val

    def set_cookie(self, key, value='', max_age=None, expires=None, path='/', domain=None, secure=None):
        if not self.cookies:
            self.cookies = SimpleCookie()
        self.cookies[key] = value
        if max_age:
            self.cookies[key]['max-age'] = max_age
        if expires:
            if isinstance(expires, str):
                self.cookies[key]['expires'] = expires
            elif isinstance(expires, datetime.datetime):
                expires = evwsgi.rfc1123_date(time.mktime(expires.timetuple()))
            else:
                raise CookieError('expires must be a datetime object or a string')
            self.cookies[key]['expires'] = expires
        if path:
            self.cookies[key]['path'] = path
        if domain:
            self.cookies[key]['domain'] = domain
        if secure:
            self.cookies[key]['secure'] = secure

    def delete_cookie(self, key):
        if self.cookies:
            self.cookies[key] = ''
        self.cookies[key]['max-age'] = "0"

    def __str__(self):
        res = "HTTP/1.0 %s %s\r\n" % (self.status_code, self.status_reasons)
        for key, val in self.response_headers.items():
            res += '%s: %s\r\n' % (key, val)
        if self.cookies:
            res += str(self.cookies) + "\r\n"
        res += "\r\n"
        return res


def redirectStdErr():
    """
    This methods allow use to redirect messages sent to stderr into a string
    Mandatory methods of the sys.stderr object are:
        write: to insert data
        getvalue; to retreive all data
    """
    sys.stderr = StringIO.StringIO()

supported_HTTP_command = ["GET", "POST", "HEAD", "OPTIONS"]


def split_len(seq, length):
    return [seq[i:i + length] for i in range(0, len(seq), length)]


def parse_cookies(environ):
    #transform the cookie environment into a SimpleCokkie object
    line = environ.get('HTTP_COOKIE', None)
    if line:
        cook = SimpleCookie()
        cook.load(line)
        return cook
    else:
        return None
