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
import os
import subprocess
from fapws.compat import convert_to_bytes

class CGIApplication:
    def __init__(self, script):
        self.script = script
        self.dirname = os.path.dirname(script)
        self.cgi_environ = {}

    def _setup_cgi_environ(self, environ):
        for key, val in list(environ.items()):
            if type(val) in (str,bytes):
                key = convert_to_bytes(key)
                self.cgi_environ[key] = convert_to_bytes(val)
        self.cgi_environ[b'REQUEST_URI'] = convert_to_bytes(environ['fapws.uri'])

    def _split_return(self, data):
        data = convert_to_bytes(data)
        if b'\n\n' in data:
            header, content = data.split(b'\n\n', 1)
        else:
            header = b""
            content = data
        return header, content

    def _split_header(self, header):
        i = 0
        headers = []
        firstline = b"HTTP/1.1 200 OK"
        for line in header.split(b'\n'):
            if i == 0 and b':' not in line:
                firstline = line
            if b':' in line:
                name, value = line.split(b':', 1)
                headers.append((convert_to_bytes(name), convert_to_bytes(value)))
            i += 1
        status = " ".join(firstline.split()[1:])
        return status, headers

    def __call__(self, environ, start_response):
        self._setup_cgi_environ(environ)
        proc = subprocess.Popen(
                    [self.script],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    env=self.cgi_environ,
                    cwd=self.dirname,
                    )
        input_len = int(environ.get(b'CONTENT_LENGTH', b'0'))
        if input_len:
            cgi_input = environ[b'wsgi.input'].read(input_len)
        else:
            cgi_input = ""
        #print "cgi input", cgi_input
        stdout, stderr = proc.communicate(cgi_input)
        if stderr:
            return [stderr]
        header, content = self._split_return(stdout)
        status, headers = self._split_header(header)
        start_response(status, headers)
        return [content]
