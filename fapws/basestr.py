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

class Environ(dict):
    def __init__(self, *arg, **kw):
        self['wsgi.version'] = (1, 0)
        self['wsgi.errors'] = BytesIO()
        self['wsgi.input'] = BytesIO()
        self['wsgi.multithread'] = False
        self['wsgi.multiprocess'] = True
        self['wsgi.run_once'] = False
        self['fapws.params'] = {}
    #here after some entry point before the Environ update
       
    def _bytes2str(self,data): 
        new_data = {}
        for key,val in data.items():
            if type(val) == bytes:
                new_val = val.decode('utf8')
            else:
                new_val = val
            new_data[key] = new_val
        return new_data

    def update_headers(self, data):
        new_data = self._bytes2str(data)
        dict.update(self, new_data)

    def update_uri(self, data):
        new_data = self._bytes2str(data)
        dict.update(self, new_data)

    def update_from_request(self, data):
        new_data = self._bytes2str(data)
        dict.update(self, new_data)

