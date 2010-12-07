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
try:
    import cStringIO as StringIO
except:
    import StringIO
import gzip


class Gzip:
    #wsgi gzip middelware
    def __call__(self, f):
        def func(environ, start_response):
            content = f(environ, start_response)
            if 'gzip' in environ.get('HTTP_ACCEPT_ENCODING', ''):
                if type(content) is list:
                    content = "".join(content)
                else:
                    #this is a stream
                    content = content.read()
                sio = StringIO.StringIO()
                comp_file = gzip.GzipFile(mode='wb', compresslevel=6, fileobj=sio)
                comp_file.write(content)
                comp_file.close()
                start_response.add_header('Content-Encoding', 'gzip')
                res = sio.getvalue()
                start_response.add_header('Content-Length', len(res))
                return [res]
            else:
                return content
        return func
