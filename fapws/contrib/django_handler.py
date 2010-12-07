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
from django.core.handlers import wsgi
import django


djhand = wsgi.WSGIHandler()


def handler(environ, start_response):
    res = djhand(environ, start_response)
    if django.VERSION[0] == 0:
        for key, val in res.headers.items():
            start_response.response_headers[key] = val
    else:
        for key, val in res._headers.values():
            start_response.response_headers[key] = val
    start_response.cookies = res.cookies
    return res.content
