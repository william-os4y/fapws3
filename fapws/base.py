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
from http.cookies import SimpleCookie, CookieError
from io import StringIO
import sys
import string
import traceback
import time

from fapws import config
import http


def get_status(code):
    return "%s %s" % (code, http.client.responses[code])


class Environ(dict):
    def __init__(self, *arg, **kw):
        self['wsgi.version'] = (1, 0)
        self['wsgi.errors'] = StringIO()
        self['wsgi.input'] = StringIO()
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
        self.status_code = b"200"
        self.status_reasons = b"OK"
        self.response_headers = {}
        self.exc_info = None
        self.cookies = None
        # NEW -- sent records whether or not the headers have been send to the
        # client
        self.sent = False

    def __call__(self, status, response_headers, exc_info=None):
        self.status_code, self.status_reasons = status.split(b" ", 1)
        self.status_code = str(self.status_code)
        for key, val in response_headers:
            #if type(key)!=type(""):
            key = bytes(key)
            #if type(val)!=type(""):
            val = bytes(val)
            self.response_headers[key] = val
        self.exc_info = exc_info  # TODO: to implement

    def add_header(self, key, val):
        key = bytes(key)
        val = bytes(val)
        self.response_headers[key] = val

    def set_cookie(self, key, value='', max_age=None, expires=None, path='/', domain=None, secure=None):
        if not self.cookies:
            self.cookies = SimpleCookie()
        self.cookies[key] = value
        if max_age:
            self.cookies[key][b'max-age'] = max_age
        if expires:
            if isinstance(expires, str):
                self.cookies[key][b'expires'] = expires
            elif isinstance(expires, datetime.datetime):
                expires = evwsgi.rfc1123_date(time.mktime(expires.timetuple()))
            else:
                raise CookieError(b'expires must be a datetime object or a string')
            self.cookies[key][b'expires'] = expires
        if path:
            self.cookies[key][b'path'] = path
        if domain:
            self.cookies[key][b'domain'] = domain
        if secure:
            self.cookies[key][b'secure'] = secure

    def delete_cookie(self, key):
        if self.cookies:
            self.cookies[key] = b''
        self.cookies[key][b'max-age'] = b"0"

    def __str__(self):
        res = b"HTTP/1.0 %s %s\r\n" % (self.status_code, self.status_reasons)
        for key, val in list(self.response_headers.items()):
            res += b'%s: %s\r\n' % (key, val)
        if self.cookies:
            res += str(self.cookies) + b"\r\n"
        res += b"\r\n"
        return res


def redirectStdErr():
    """
    This methods allow use to redirect messages sent to stderr into a string
    Mandatory methods of the sys.stderr object are:
        write: to insert data
        getvalue; to retreive all data
    """
    sys.stderr = StringIO()
    return "toto"

supported_HTTP_command = [b"GET", b"POST", b"HEAD", b"OPTIONS"]


def split_len(seq, length):
    return [seq[i:i + length] for i in range(0, len(seq), length)]

def parse_cookies(environ):
    #transform the cookie environment into a SimpleCokkie object
    line = environ.get(b'HTTP_COOKIE', None)
    if line:
        cook = SimpleCookie()
        cook.load(line)
        return cook
    else:
        return None
