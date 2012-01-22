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
from fapws.base import *
from fapws.contrib import multipart

class Environ(dict):
    def __init__(self, *arg, **kw):
        self[b'wsgi.version'] = (1, 0)
        self[b'wsgi.errors'] = BytesIO()
        self[b'wsgi.input'] = multipart.MultipartFormData("/tmp/")
        self[b'wsgi.multithread'] = False
        self[b'wsgi.multiprocess'] = True
        self[b'wsgi.run_once'] = False
        self[b'fapws.params'] = {}
    #here after some entry point before the Environ update

    def update_headers(self, data):
        dict.update(self, data)

    def update_uri(self, data):
        dict.update(self, data)

    def update_from_request(self, data):
        dict.update(self, data)

