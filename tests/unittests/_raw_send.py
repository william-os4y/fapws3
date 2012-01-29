import socket
import time

def send(post_data, port=8080, host='127.0.0.1'):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((host, port))
    s.send(post_data)
    time.sleep(0.1) # we just let the sercer having time to build the answer
    res = s.recv(1024)
    s.close()
    return res


if __name__ ==  "__main__":
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
    res = send(data)
    print(res)
