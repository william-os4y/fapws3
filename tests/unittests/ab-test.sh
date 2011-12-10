#!/bin/sh


wait_sockets () {
echo " ############## waiting ..."
os=`netstat -a | wc -l `
while [ $os -gt $MAX_os ] 
do
   os=`netstat -a | wc -l `
   echo "Open sockets: $os is not lower than $MAX_os"
   sleep 5 
done
echo "################"
}
#We just provide some info about the system
echo "################"
echo "System: `uname -a`"
echo "################"


#
#This bench is based on the famous HelloWorld provide by the unittests/server.py
#
MAX_os=$(expr `netstat -a | wc -l` + 100)
nice -20 ab -n10000 -c1 http://127.0.0.1:8080/hello 
wait_sockets

MAX_os=$(expr `netstat -a | wc -l` + 100)
nice -20 ab -n10000 -c2 http://127.0.0.1:8080/hello 
wait_sockets

MAX_os=$(expr `netstat -a | wc -l` + 100)
nice -20 ab -n10000 -c5 http://127.0.0.1:8080/hello
wait_sockets

MAX_os=$(expr `netstat -a | wc -l` + 100)
nice -20 ab -n10000 -c10 http://127.0.0.1:8080/hello
wait_sockets

MAX_os=$(expr `netstat -a | wc -l` + 100)
nice -20 ab -n10000 -c50 http://127.0.0.1:8080/hello
wait_sockets

nice -20 ab -n10000 -c100 http://127.0.0.1:8080/hello

