# -*- coding: utf-8 -*-

import sys
if sys.version_info[0] == 2:
    print("This script is not compatible with Python2.x!!!! Please use the specific one: test27.py")
    sys.exit()

import http.client as http_client
import urllib.parse as urllib_parse

import os.path

import os

import _raw_send

if len(sys.argv)>1 and sys.argv[1]=="socket":
  import socket
  socket_server = True
else:
  socket_server = False

successes=0
failures=0


def test(search, test, data):
    global successes, failures
    if not test:
        print("TEST PROBLEM")
        failures+=1
    elif search not in data:
        print("""RESPONSE PROBLEM, we don't find "%s" """ % search)
        print(data)
        failures+=1
    else:
        print("SUCCESS")
        successes+=1

class UHTTPConnection(http_client.HTTPConnection):
    """Subclass of Python library HTTPConnection that
       uses a unix-domain socket.
       borrowed from http://7bits.nl/blog/2007/08/15/http-on-unix-sockets-with-python
    """
 
    def __init__(self, path):
        http_client.HTTPConnection.__init__(self, 'localhost')
        self.path = path
 
    def connect(self):
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.connect(self.path)
        self.sock = sock

if socket_server:
    con = UHTTPConnection("\0/org/fapws3/server")
else:
    con = http_client.HTTPConnection("127.0.0.1:8080")
    
if 1:
  print("=== Normal get ===")
  con.request("GET", "/env/param?key=val")
  response=con.getresponse()
  content=response.read()
  test(b"SCRIPT_NAME:b'/env'",response.status==200,content) 
  test(b"PATH_INFO:b'/param'",response.status==200,content)
  test(b"REQUEST_METHOD:b'GET'",response.status==200,content)  
  test(b"SERVER_PROTOCOL:b'HTTP/1.1'",response.status==200,content) 
  test(b"wsgi.url_scheme:b'HTTP'",response.status==200,content) 
  test(b"QUERY_STRING:b'key=val'",response.status==200,content) 
  test(b"fapws.params:{b'key': [b'val']}",response.status==200,content) 

  print("=== URL not found ===")
  con.request("GET", "/wrongpage")
  response=con.getresponse()
  content=response.read()
  test(b"Page not found", response.status==500, content)

  print("=== Get Hello world ===")
  con.request("GET", "/hello")
  response=con.getresponse()
  content=response.read()
  test(b"Hello world!!", response.status==200, content)

  print("=== Get Iter Hello world ===")
  con.request("GET", "/iterhello")
  response=con.getresponse()
  content=response.read()
  test(b"Hello world!!", response.status==200, content)

  print("=== Get tuple Hello world ===")
  con.request("GET", "/tuplehello")
  response=con.getresponse()
  content=response.read()
  test(b"Hello world!!", response.status==200, content)

  print("=== Get Class Hello world ===")
  con.request("GET", "/helloclass")
  response=con.getresponse()
  content=response.read()
  test(b"Hello from class !!!", response.status==200, content)

  print("=== Get long file ===")
  con.request("GET", "/long")
  response=con.getresponse()
  content=response.read()
  test(b"azerty", len(content)==os.path.getsize("long.txt"), content)

  print("=== Get long file zipped ===")
  headers={"Accept-Encoding":"gzip"}
  con.request("GET", "/longzipped", "", headers)
  response=con.getresponse()
  content=response.read()
  header=response.getheader('content-encoding')
  header_length=response.getheader('content-length')
  test(b"azerty", str(len(content))==header_length, b"azerty")

  print("=== Get split long file ===")
  con.request("GET", "/elong")
  response=con.getresponse()
  content=response.read()
  test(b"azerty", len(content)==os.path.getsize("long.txt"), content)

  print("=== Get cached file ===")
  headers={"if-None-Match":str(os.path.getmtime('test.html'))}
  con.request("GET", "/staticform", "", headers)
  response=con.getresponse()
  test("304", response.status==304, "304")

  print("=== Post without length ===")
  params = urllib_parse.urlencode({'var1': 'value1', 'var2': 'value2'})
  con.request("POST", "/testpost")
  response=con.getresponse()
  content=response.read()
  test(b"Length Required", response.status==411, content)

  print("=== Post with length ===")
  params = urllib_parse.urlencode({'var1': 'value1', 'var2': 'value2'})
  headers = {"Content-type": "application/x-www-form-urlencoded", 
            "Accept": "text/plain"}
  con.request("POST", "/testpost", params, headers) #in this case http.client send automatically the content-length header
  response=con.getresponse()
  content=response.read()
  test(b"OK. params are:{b'var1': [b'value1'], b'var2': [b'value2']}", response.status==200, content)

  if socket_server == True:
    print("=== Post multipart is skipped on Socket server ===")
  else:
    print("=== Post with multipart ===")
    try:
      os.remove('/tmp/short.txt')
    except:
      pass
    data = b"""POST /testpost HTTP/1.1\r
Host: 127.0.0.1:8080\r
Accept: */*\r
Content-Length: 333\r
Content-Type: multipart/form-data; boundary=----------------------------6b72468f07eb\r
\r
------------------------------6b72468f07eb\r
Content-Disposition: form-data; name="field1"\r
\r
this is a test using httppost & stuff\r
------------------------------6b72468f07eb\r
Content-Disposition: form-data; name="field2"; filename="short.txt"\r
Content-Type: text/plain\r
\r
Hello world
\r
------------------------------6b72468f07eb--\r\n"""  
    response = _raw_send.send(data)
    test(b"OK. params are:{b'field2': ['/tmp/short.txt', {b'Content-Type': b'text/plain', b'size': 14}], b'field1': [b'this is a test using httppost & stuff']}", 1==1, response)

  print("=== Options ===")
  con.request("OPTIONS", "/")
  response=con.getresponse()
  content=response.read()
  resp_allow=response.getheader('allow', None)
  test("Options", response.status==200 and resp_allow[:3]=='GET', "Options")

  print("=== Bad header: 2 semi-column ===")
  headers={'Badkey:': "Value"}
  con.request("GET", "/env", "", headers)
  response=con.getresponse()
  content=response.read()
  test(b"HTTP_BADKEY:b': Value'", response.status==200 , content)

  print("=== Bad header: key with CR  ===")
  headers={'Bad\nkey': "Value"}
  con.request("GET", "/env", "", headers)
  response=con.getresponse()
  content=response.read()
  test(b"KEY:b'Value'", response.status==200 , content)

  print("=== Bad header: value with CR  ===")
  headers={'Badkey': "Val\nue"}
  con.request("GET", "/env", "", headers)
  response=con.getresponse()
  content=response.read()
  test(b"HTTP_BADKEY:b'Val", response.status==200 , content)

  print("=== Bad header: value with CRLF  ===")
  headers={'Badkey': "Val\r\nue"}
  con.request("GET", "/env", "", headers)
  response=con.getresponse()
  content=response.read()
  test(b"HTTP_BADKEY:b'Val", response.status==200 , content)

  print("=== Bad command  ===")
  con.request("GIT", "/env")
  response=con.getresponse()
  content=response.read()
  test(b"Not Implemented", response.status==501 , content)

  print("=== Bad first line  ===")
  con.request("GET", "/env\r\n")
  response=con.getresponse()
  content=response.read()
  test(b"SCRIPT_NAME:b'/env'", response.status==200 , content)

  print("=== Bad script  ===")
  con.request("GET", "/badscript")
  response=con.getresponse()
  content=response.read()
  test(b"Traceback", response.status==500 , content)

  print("=== Bad command ===")
  con.request("TOTO","")
  response=con.getresponse()
  content=response.read()
  test(b"Not Implemented", response.status==501 , content)
  
  print("=== Very long GET ===")
  url = "/env?var=" + "to"*2056
  con.request("GET", url)
  response=con.getresponse()
  content=response.read()
  test(b"tototototo", response.status==200 , content)

  print("=== Return Null ===")
  con.request("GET", "/returnnull")
  response=con.getresponse()
  content=response.read()
  print response.status
  test(b"", response.status==200 , content)

  print("=== Return None ===")
  con.request("GET", "/returnnone")
  response=con.getresponse()
  content=response.read()
  test(b"", response.status==200 , content)

  print("=== Return Iter None ===")
  con.request("GET", "/returniternull")
  response=con.getresponse()
  content=response.read()
  test(b"start", response.status==200 , content)

print("==================")
print("TOTAL successes:", successes)
print("TOTAL failures:", failures)
print() 
print() 


