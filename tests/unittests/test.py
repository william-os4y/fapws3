# -*- coding: utf-8 -*-
import http.client
import urllib.request, urllib.parse, urllib.error
import os.path

try:
    import pycurl
except: 
    pycurl = False
    print("PyCurl is not present, some tests cannot be executed !!!!")

import os

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


con = http.client.HTTPConnection("127.0.0.1:8080")

if 1:
  print("=== Normal get ===")
  con.request("GET", "/env/param?key=val")
  response=con.getresponse()
  content=response.read()
  test(b"SCRIPT_NAME:/env",response.status==200,content) 
  test(b"PATH_INFO:/param",response.status==200,content)
  test(b"REQUEST_METHOD:GET",response.status==200,content) 
  test(b"SERVER_PROTOCOL:HTTP/1.1",response.status==200,content) 
  test(b"wsgi.url_scheme:HTTP",response.status==200,content) 
  test(b"QUERY_STRING:key=val",response.status==200,content) 
  test(b"fapws.params:{'key': ['val']}",response.status==200,content) 

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
  test(b"azerty", header=="gzip", "azerty")

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
  params = urllib.parse.urlencode({'var1': 'value1', 'var2': 'value2'})
  con.request("POST", "/testpost")
  response=con.getresponse()
  content=response.read()
  test(b"Length Required", response.status==411, content)

  print("=== Post with length ===")
  params = urllib.parse.urlencode({'var1': 'value1', 'var2': 'value2'})
  headers = {"Content-type": "application/x-www-form-urlencoded", 
            "Accept": "text/plain"}
  print("TTEST:",params, headers)
  con.request("POST", "/testpost", params, headers) #in this case httplib send automatically the content-length header
  response=con.getresponse()
  content=response.read()
  test(b"OK. params are:{'var1': ['value1'], 'var2': ['value2']}", response.status==200, content)

  if pycurl:
    print("=== Post with multipart ===")
    pf = [('field1', 'this is a test using httppost & stuff'),
        ('field2', (pycurl.FORM_FILE, 'short.txt'))
     ]

    response=""
    def echo(data):
      global response
      response+=data
    
    fpath='/tmp/short.txt'
    if os.path.isfile(fpath):
      os.remove(fpath) #we remove the data stored by the MultipartFormData

    c = pycurl.Curl()
    c.setopt(c.URL, 'http://127.0.0.1:8080/testpost')
    c.setopt(c.WRITEFUNCTION, echo)
    c.setopt(c.HTTPPOST, pf)
    c.perform()
    c.close()
    test("OK. params are:{'field2': ['/tmp/short.txt', {'Content-Type': 'text/plain', 'size': 14L}], 'field1': ['this is a test using httppost & stuff']}", 1==1, response)

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
  test("HTTP_BADKEY:: Value", response.status==200 , content)

  print("=== Bad header: key with CR  ===")
  headers={'Bad\nkey': "Value"}
  con.request("GET", "/env", "", headers)
  response=con.getresponse()
  content=response.read()
  test("KEY:Value", response.status==200 , content)

  print("=== Bad header: value with CR  ===")
  headers={'Badkey': "Val\nue"}
  con.request("GET", "/env", "", headers)
  response=con.getresponse()
  content=response.read()
  test("HTTP_BADKEY:Val", response.status==200 , content)

  print("=== Bad header: value with CRLF  ===")
  headers={'Badkey': "Val\r\nue"}
  con.request("GET", "/env", "", headers)
  response=con.getresponse()
  content=response.read()
  test("HTTP_BADKEY:Val", response.status==200 , content)

  print("=== Bad command  ===")
  con.request("GIT", "/env")
  response=con.getresponse()
  content=response.read()
  test("Not Implemented", response.status==501 , content)

  print("=== Bad first line  ===")
  con.request("GET", "/env\r\n")
  response=con.getresponse()
  content=response.read()
  test("SCRIPT_NAME:/env", response.status==200 , content)

  print("=== Bad script  ===")
  con.request("GET", "/badscript")
  response=con.getresponse()
  content=response.read()
  test("Traceback", response.status==500 , content)

  print("=== Bad command ===")
  con.request("!çàù","")
  response=con.getresponse()
  content=response.read()
  test("Not Implemented", response.status==501 , content)
  


print("==================")
print("TOTAL successes:", successes)
print("TOTAL failures:", failures)
print() 
print() 


