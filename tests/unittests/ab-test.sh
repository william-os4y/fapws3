#!/bin/sh

wait_sockets () {
echo " ############## sleeping ..."
sleep 60  #This could be adapted
echo "Open sockets: `netstat -a  | wc -l`"
echo "################"
}
#
#This bench is based on the famous HelloWorld provide by the unittests/server.py
#
nice -20 ab -n10000 -c1 http://127.0.0.1:8080/hello 
wait_sockets
nice -20 ab -n10000 -c2 http://127.0.0.1:8080/hello 
wait_sockets
nice -20 ab -n10000 -c5 http://127.0.0.1:8080/hello
wait_sockets
nice -20 ab -n10000 -c10 http://127.0.0.1:8080/hello
wait_sockets
nice -20 ab -n10000 -c50 http://127.0.0.1:8080/hello
wait_sockets
nice -20 ab -n10000 -c100 http://127.0.0.1:8080/hello

