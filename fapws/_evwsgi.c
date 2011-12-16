/*
    Copyright (C) 2009 William.os4y@gmail.com

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, version 2 of the License.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.


*/

#include <fcntl.h>   //for setnonblocking 
#include <stddef.h>  //for the offset command

#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <errno.h>
#include <string.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <netdb.h>
#include <arpa/inet.h>
#include <sys/wait.h>
#include <signal.h>
#include <assert.h>
#include <sys/un.h>

#include <ev.h>

#include <Python.h>
#include "common.h"
#include "mainloop.h"
#include "wsgi.h"
#include "extra.h"


/*
Somme  global variables
*/
char *server_name="127.0.0.1";
int server_name_length;
char *server_port="8000";
int sockfd;  // main sock_fd
int debug=0; //1 full debug detail: 0 nodebug
char *VERSION;
#define BACKLOG 1024     // how many pending connections queue will hold
char *date_format;


PyObject *py_base_module;  //to store the fapws.base python module
PyObject *py_config_module; //to store the fapws.config module
PyObject *py_registered_uri; //list containing the uri registered and their associated wsgi callback.
PyObject *py_generic_cb=NULL; 
#define MAX_TIMERS 10 //maximum number of running timers
struct TimerObj *list_timers[MAX_TIMERS];
int list_timers_i=0; //number of values entered in the array list_timers
struct ev_loop *loop; // we define a global loop
PyObject *pydeferqueue;  //initialisation of defer
ev_idle *idle_watcher;
static PyObject *ServerError;




/*
Procedure exposed in Python will establish the socket and the connection.
*/
static PyObject *py_ev_start(PyObject *self, PyObject *args)
{
/*
code copied from the nice book written by Bee:
http://beej.us/guide/bgnet/output/html/singlepage/bgnet.html
*/
    struct addrinfo hints, *servinfo, *p;
//    struct sockaddr_storage their_addr; // connector's address information
    int yes=1;
    int rv;

    if (!PyArg_ParseTuple(args, "s#s", &server_name, &server_name_length, &server_port))
    {
        PyErr_SetString(ServerError, "Failed to parse the start parameters. Must be 2 strings.");
        return NULL;
    }
    if (strncmp(server_port, "unix", 4) != 0) {
        memset(&hints, 0, sizeof hints);
        hints.ai_family = AF_UNSPEC;
        hints.ai_socktype = SOCK_STREAM;
        hints.ai_flags = AI_PASSIVE; // use my IP
        if ((rv = getaddrinfo(server_name, server_port, &hints, &servinfo)) == -1) {
            PyErr_Format(ServerError, "getaddrinfo: %s", gai_strerror(rv));
            return NULL;
        }

        // loop through all the results and bind to the first we can
        for(p = servinfo; p != NULL; p = p->ai_next) {
            sockfd = socket(p->ai_family, p->ai_socktype, p->ai_protocol);
            if (sockfd == -1) {
                perror("server: socket");
                continue;
            }

            if (setsockopt(sockfd, SOL_SOCKET, SO_REUSEADDR, &yes,
                    sizeof(int)) == -1) {
                perror("setsockopt");
            }

            if (bind(sockfd, p->ai_addr, p->ai_addrlen) == -1) {
                close(sockfd);
                perror("server: bind");
                continue;
            }

            break;
        }
        
        freeaddrinfo(servinfo); // all done with this structure

        if (p == NULL)  {
            PyErr_SetString(ServerError, "server: failed to bind");
            return NULL;
        }
        
    } else {
        sockfd = socket(AF_UNIX, SOCK_STREAM, 0);
        if (sockfd == -1) {
            perror("server: socket");
            PyErr_SetString(ServerError, "server: failed to create socket");
            return NULL;
        }
        
        struct sockaddr_un sockun;
        sockun.sun_family = AF_UNIX;
        memcpy(sockun.sun_path, server_name, server_name_length);
        /*if (sockun.sun_path[0] == '@')
            sockun.sun_path[0] = '\0';*/
        if (bind(sockfd, (struct sockaddr *) &sockun, server_name_length+2) == -1) {
            close(sockfd);
            perror("server: bind");
            PyErr_SetString(ServerError, "server: failed to bind");
            return NULL;
        }
    }

    if (listen(sockfd, BACKLOG) == -1) {
        PyErr_SetString(ServerError, "listen");
        return NULL;
    }
    if (server_name[0] == 0)
        printf("listen on @%s:unix\n", server_name+1);
    else
        printf("listen on %s:%s\n", server_name, server_port);
    return Py_None;
}

/*
Procedure exposed in Python will generate and start the event loop
*/
static PyObject *py_run_loop(PyObject *self, PyObject *args)
{
    char *backend="";
    int i;
    ev_io accept_watcher;
    ev_signal signal_watcher, signal_watcher2, signal_watcher3;
    struct TimerObj *timer;
    loop = ev_default_loop (0);
    switch (ev_backend(loop))
    {
        case 1:
            backend="select";
            break;
        case 2:
            backend="poll";
            break;
        case 4:
            backend="epoll";
            break;
        case 8:
            backend="kqueue";
            break;
    }
    printf("Using %s as event backend\n", backend);
    ev_io_init(&accept_watcher,accept_cb,sockfd,EV_READ);
    ev_io_start(loop,&accept_watcher);
    ev_signal_init(&signal_watcher, sigint_cb, SIGINT);
    ev_signal_start(loop, &signal_watcher);
    ev_signal_init(&signal_watcher2, sigpipe_cb, SIGPIPE);
    ev_signal_start(loop, &signal_watcher2);
    ev_signal_init(&signal_watcher3, sigterm_cb, SIGTERM);
    ev_signal_start(loop, &signal_watcher3);
    idle_watcher = malloc(sizeof(ev_idle));
    ev_idle_init(idle_watcher, idle_cb);
    if (list_timers_i>=0)
    {
        for (i=0; i<list_timers_i; i++)
        {
            timer=list_timers[i];
            ev_timer_init(&timer->timerwatcher, timer_cb, timer->delay, timer->delay);
            ev_timer_start(loop, &timer->timerwatcher);
        }
    }
    ev_loop (loop, 0);
    return Py_None;
}

/*
Procedure exposed in Python to provide the sockfd
*/
static PyObject *py_socket_fd(PyObject *self, PyObject *args)
{
    PyObject *pyres = PyLong_FromLong(sockfd);
    return pyres;
}

/*
Procedure exposed in Python to provide libev's ABI version
*/
static PyObject *py_libev_version(PyObject *self, PyObject *args)
{
    PyObject *pyres=Py_BuildValue("ii", ev_version_major(), ev_version_minor());
    return pyres;
}



/*
Procedure exposed in Python to register the "base" module
*/
static PyObject *py_set_base_module(PyObject *self, PyObject *args)
{
    if (!PyArg_ParseTuple(args, "O", &py_base_module)) 
        return NULL;
    py_config_module=PyObject_GetAttrString(py_base_module, "config");
    py_registered_uri = PyList_New(0);

    //Get the version from the config.py file
    PyObject *pyver=PyObject_GetAttrString(py_config_module,"SERVER_IDENT");
    VERSION=PyString_AsString(pyver);
    
    //get the date format
    PyObject *pydateformat=PyObject_GetAttrString(py_config_module,"date_format");
    date_format=PyString_AsString(pydateformat);
    
    
    
    return Py_None;    
}

/*
Procedure exposed in Python to add the tuple: uri, wsgi call back
*/
static PyObject *py_add_wsgi_cb(PyObject *self, PyObject *args)
{
    PyObject *py_tuple;
    if (!PyArg_ParseTuple(args, "O", &py_tuple)) 
        return NULL;
    if (py_registered_uri == NULL) {
        PyErr_SetString(ServerError, "Base module not set");
        return NULL;
    }
    PyList_Append(py_registered_uri, py_tuple);
    return Py_None;    
}
    
/*
Procedure exposed in Python to expose "parse_query"
*/
PyObject *py_parse_query(PyObject *self, PyObject *args)
{
    char *uri;

    if (!PyArg_ParseTuple(args, "s", &uri))
        return NULL;
    return parse_query(uri);
}

/*
Procedure exposed in Python to register the generic python callback
*/
PyObject *py_set_gen_wsgi_cb(PyObject *self, PyObject *args)
{
    if (!PyArg_ParseTuple(args, "O", &py_generic_cb))
        return NULL;
    return Py_None;
}

/*
*/
PyObject *py_set_debug(PyObject *self, PyObject *args)
{
    if (!PyArg_ParseTuple(args, "i", &debug))
        return NULL;
    return Py_None;
}

/*
*/
PyObject *py_get_debug(PyObject *self, PyObject *args)
{
    return Py_BuildValue("i", debug);
}

/*
Procedure exposed in Python to add a timer: delay, python callback method
*/
static PyObject *py_add_timer_cb(PyObject *self, PyObject *args)
{
    struct TimerObj *timer;
    if (list_timers_i<MAX_TIMERS)
    {
        timer = calloc(1,sizeof(struct TimerObj));
        if (!PyArg_ParseTuple(args, "fO", &timer->delay, &timer->py_cb)) 
            return NULL;
        list_timers[list_timers_i]=timer;
        list_timers_i++;
    } 
    else
    {
        printf("Limit of maximum %i timers has been reached\n", list_timers_i);
    }
    
    return PyInt_FromLong(list_timers_i);    
}

/*
Procedure exposed in Python to stop a running timer: i
*/
static PyObject *py_stop_timer(PyObject *self, PyObject *args)
{
    int i;
    struct TimerObj *timer;
    struct ev_loop *loop = ev_default_loop(0);
    if (!PyArg_ParseTuple(args, "i", &i)) 
        return NULL;
    timer=list_timers[i];
    ev_timer_stop(loop, &timer->timerwatcher);
    
    return Py_None;    
}

/*
Procedure exposed in Python to restart a running timer: i
*/
static PyObject *py_restart_timer(PyObject *self, PyObject *args)
{
    int i;
    struct TimerObj *timer;
    struct ev_loop *loop = ev_default_loop(0);
    if (!PyArg_ParseTuple(args, "i", &i)) 
        return NULL;
    if (i<=list_timers_i)
    {
        timer=list_timers[i];
        ev_timer_again(loop, &timer->timerwatcher);
    }
    else
    {
        printf("index out of range\n");
    }
    return Py_None;    
}


/*
Register a python function to execute when idle
*/
PyObject *py_defer(PyObject *self, PyObject *args)
{
    PyObject *pyfct, *pycombined, *pyfctargs;
    int startidle=0;
    int toadd=1;
    int listsize=0;
    
    if (!PyArg_ParseTuple(args, "OOO", &pyfct, &pyfctargs, &pycombined))
        return NULL;
    //if queue is empty, trigger a start of idle
    
    if (!pydeferqueue) 
    {
        pydeferqueue=PyList_New(0);
    }
    listsize=PyList_Size(pydeferqueue);
    if (listsize==0)
    {
        //it has been stopped by the idle_cb
        startidle=1;    
    }
    //add fct cb into the defer queue
    PyObject *pyelem=PyList_New(0);
    PyList_Append(pyelem, pyfct);
    PyList_Append(pyelem, pyfctargs);   
    if (pycombined==Py_True)
    {
        //check if the fucntion is already in the queue
        if (PySequence_Contains(pydeferqueue, pyelem))
        {
            toadd=0;
        }
    }
    
    if (toadd==1)
    {
        PyList_Append(pydeferqueue, pyelem);
        //start the idle
        if (startidle==1)
        {
            //we create a new idle watcher and we start it
            if (debug) printf("trigger idle_start \n");
            ev_idle_start(loop, idle_watcher);
        }
    }
    Py_DECREF(pyelem);
    return Py_None;
}

/*
Return the defer queue size
*/
PyObject *py_defer_queue_size(PyObject *self, PyObject *args)
{
    int listsize;
    if (pydeferqueue)
    {
        listsize=PyList_Size(pydeferqueue);  
        return Py_BuildValue("i", listsize);
    } else
    {
        return Py_None;
    }
}

/*

*/
PyObject *py_rfc1123_date(PyObject *self, PyObject *args)
{
    time_t t;
    PyObject *result;
    char *rfc_string = NULL;
    if (!PyArg_ParseTuple(args, "L", &t))
        return NULL;
    rfc_string = time_rfc1123(t);
    result = PyString_FromString(rfc_string);
    free(rfc_string);
    return result;
}


static PyMethodDef EvhttpMethods[] = {
    {"start", py_ev_start, METH_VARARGS, "Define evhttp sockets"},
    {"set_base_module", py_set_base_module, METH_VARARGS, "set you base module"},
    {"run", py_run_loop, METH_VARARGS, "Run the main loop"},
    {"wsgi_cb", py_add_wsgi_cb, METH_VARARGS, "Add an uri and his wsgi callback in the list of uri to watch"},
    {"wsgi_gen_cb", py_set_gen_wsgi_cb, METH_VARARGS, "Set the generic wsgi callback"},
    {"parse_query", py_parse_query, METH_VARARGS, "parse query into dictionary"},
    {"set_debug", py_set_debug, METH_VARARGS, "Set the debug level"},
    {"get_debug", py_get_debug, METH_VARARGS, "Get the debug level"},
    {"libev_version", py_libev_version, METH_VARARGS, "Get the libev's ABI version you are using"},
    {"add_timer", py_add_timer_cb, METH_VARARGS, "Add a timer"},
    {"stop_timer", py_stop_timer, METH_VARARGS, "Stop a running timer"},
    {"restart_timer", py_restart_timer, METH_VARARGS, "Restart an existing timer"},
    {"defer", py_defer, METH_VARARGS, "defer the execution of a python function."},
    {"defer_queue_size", py_defer_queue_size, METH_VARARGS, "Get the size of the defer queue"},
    {"rfc1123_date", py_rfc1123_date, METH_VARARGS, "trasnform a time (in sec) into a string compatible with the rfc1123"},
    {"socket_fd", py_socket_fd, METH_VARARGS, "Return the server socket's file descriptor"},
    {NULL, NULL, 0, NULL}        /* Sentinel */
};

PyMODINIT_FUNC
init_evwsgi(void)
{
    PyObject *m;
    m = Py_InitModule("_evwsgi", EvhttpMethods);
    
    ServerError = PyErr_NewException("_evwsgi.error", NULL, NULL);
    Py_INCREF(ServerError);
    PyModule_AddObject(m, "error", ServerError);
}
