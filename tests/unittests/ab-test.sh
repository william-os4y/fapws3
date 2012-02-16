#!/bin/sh

if [ "$1" ]; then
    SERVERPID=$1
fi


wait_sockets () {
    echo " ############## waiting ..."
    os=`netstat -a | wc -l `
    while [ $os -gt $MAX_os ] 
    do
       echo "Open sockets: $os is not lower than $MAX_os"
       sleep 5 
       os=`netstat -a | wc -l `
    done
    echo "Open sockets: $os is now lower than $MAX_os"
}

system_info () {
    #We just provide some info about the system
    echo "################"
    echo "System: `uname -a`"
    echo "Python: `python -c "import sys;print(sys.version)"` "
    echo "Fawps3: `python -c "import fapws;print(fapws.version)"` "
}

display_memory () {
    if [ "$SERVERPID" ]; then
        echo "################"
        ps u $SERVERPID
    fi
}

bench () {
    #
    #This bench is based on the famous HelloWorld provide by the unittests/server.py
    #
    page=$1
    display_memory
    echo "################"
    MAX_os=$(expr `netstat -a | wc -l` + 100)
    nice -20 ab -n10000 -c1 http://127.0.0.1:8080/$page 
    display_memory
    wait_sockets
    echo "================" 
    
    MAX_os=$(expr `netstat -a | wc -l` + 100)
    nice -20 ab -n10000 -c2 http://127.0.0.1:8080/$page 
    display_memory
    wait_sockets
    echo "================" 
    
    MAX_os=$(expr `netstat -a | wc -l` + 100)
    nice -20 ab -n10000 -c5 http://127.0.0.1:8080/$page
    display_memory
    wait_sockets
    echo "================" 
    
    MAX_os=$(expr `netstat -a | wc -l` + 100)
    nice -20 ab -n10000 -c10 http://127.0.0.1:8080/$page
    display_memory
    wait_sockets
    echo "================" 
    
    MAX_os=$(expr `netstat -a | wc -l` + 100)
    nice -20 ab -n10000 -c50 http://127.0.0.1:8080/$page
    display_memory
    wait_sockets
    echo "================" 
    
    nice -20 ab -n10000 -c100 http://127.0.0.1:8080/$page
    display_memory
    echo "================" 

}

system_info
bench hello
bench iterhello
bench tuplehello
bench helloclass
bench short
bench longzipped
bench staticform
bench badscript
bench notavalidpage
bench returnnone
bench returnnull
bench returniternull

