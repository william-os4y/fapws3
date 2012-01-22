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



#import cStrinIO

from io import BytesIO
import gzip
from fapws.compat import convert_to_bytes


class Gzip:
    #wsgi gzip middelware
    def __call__(self, f):
        def func(environ, start_response):
            content = f(environ, start_response)
            if b'gzip' in environ.get(b'HTTP_ACCEPT_ENCODING', b''):
                if type(content) is list:
                    content = "".join(content)
                else:
                    #this is a stream
                    content = content.read()
                sio = BytesIO()
                comp_file = gzip.GzipFile(mode='wb', compresslevel=6, fileobj=sio)
                comp_file.write(content)
                comp_file.close()
                start_response.add_header(b'Content-Encoding', b'gzip')
                res = sio.getvalue()
                start_response.add_header(b'Content-Length', convert_to_bytes(len(res)))
                return [res]
            else:
                return content
        return func
