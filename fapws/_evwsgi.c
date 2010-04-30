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

#include <ev.h>

#include <Python.h>

#define BACKLOG 1024     // how many pending connections queue will hold
#define MAX_BUFF 32768  //read buffer size. bigger faster, but memory foot print bigger
#define MAX_RETRY 9   //number of connection retry
#define VERSION "0.5"

/*
Structure we use for each client's connection. 
*/
struct client {
        int fd;
        ev_io ev_write;
        ev_io ev_read;
        char *remote_addr;
        int remote_port;
        char *input_header;
        char *input_body;
        size_t input_pos;
        int retry;
        char *uri;
        char *cmd;
        char *protocol;
        char *http_major_minor;
        char *uri_path;   //correspond to the registered uri_header 
        PyObject *wsgi_cb;
        int response_iter_sent; //-2: nothing sent, -1: header sent, 0-9999: iter sent
        char *response_header;
	int response_header_length;
        PyObject *response_content;
        PyObject *response_content_obj;
        FILE *response_fp; // file of the sent file
};


/*
Somme  global variables
*/
char *server_name="127.0.0.1";
char *server_port="8000";
int sockfd;  // main sock_fd
int debug=0; //1 full debug detail: 0 nodebug

PyObject *py_base_module;  //to store the fapws.base python module
PyObject *py_config_module; //to store the fapws.config module
PyObject *py_registered_uri; //list containing the uri registered and their associated wsgi callback.
PyObject *py_generic_cb=NULL; 



/*
Just to assure the connection will be nonblocking
*/
int
setnonblock(int fd)
{
    int flags;

    flags = fcntl(fd, F_GETFL);
    if (flags < 0)
            return flags;
    flags |= O_NONBLOCK;
    if (fcntl(fd, F_SETFL, flags) < 0) 
            return -1;

    return 0;
}

/*
We just free all the required variables and then close the connection to the client 
*/
void close_connection(struct client *cli)
{
    if (debug)
        printf("host=%s,port=%i close_connection:cli:%p, input_header:%p***\n",cli->remote_addr, cli->remote_port, cli, cli->input_header);
    free(cli->input_header);
    free(cli->cmd);
    free(cli->uri);
    free(cli->protocol);
    free(cli->uri_path);
    //free(cli->response_header);
    Py_XDECREF(cli->response_content);
    if (cli->response_content_obj!=NULL)
    {
        Py_DECREF(cli->response_content_obj);
    }
    if (cli->response_fp){
        //free(cli->response_fp);
    }
    close(cli->fd);
    free(cli);
}

/*
This procedure remove the character c from source s and put the result in destination d
*/
void stripChar(char *s, char *d, char c) {
    while (*s) { 
        if (*s != c) { *d++ = *s; }
        s++;  
    }
    *d = '\0';
}

/*
HTML decoder procedure we can use for uri or post parameters. It return a char which must be free'd in the caller
*/
char *
decode_uri(const char *uri)
{
    char c, *ret;
    int i, j;
    
    ret = malloc(strlen(uri) + 1);
    for (i = j = 0; uri[i] != '\0'; i++) {
        c = uri[i];
        if (c == '+') {
            c = ' ';
        } else if (c == '%' && isxdigit((unsigned char)uri[i+1]) &&
            isxdigit((unsigned char)uri[i+2])) {
            char tmp[] = { uri[i+1], uri[i+2], '\0' };
            c = (char)strtol(tmp, NULL, 16);
            i += 2;
        }
        ret[j++] = c;
    }
    ret[j] = '\0';
    
    return (ret);
}

/*
This procdure analyse uri and return a Python dictionary with every parameters as keys and their associated values into a list. 
*/
PyObject *
parse_query(char * uri)
{
    PyObject *pydict=PyDict_New();
    char *line;
    char *p;
    if ((line = strdup(uri)) == NULL) {
        printf("failed to strdup\n");
        return NULL;
    }
    p=line;
    
    while (p != NULL && *p != '\0') {
        char  *value, *key;
        PyObject *pyelem;
        PyObject *pydummy;
        value = strsep(&p, "&");
        key = strsep(&value, "=");
        if (value==NULL) {
            value="";
        }
        value=decode_uri(value); // must be free'd
        key=decode_uri(key);     // must be free'd
        if ((pyelem=PyDict_GetItemString(pydict, key))==NULL) {
            pyelem=PyList_New(0);
        } else {
            Py_INCREF(pyelem); // because of GetItem 
        }
        pydummy=PyString_FromString(value);
        free(value);
        PyList_Append(pyelem, pydummy);
        Py_DECREF(pydummy);
        PyDict_SetItemString(pydict, key, pyelem);
        free(key);
        Py_DECREF(pyelem); 
    }
    free(line);
    return pydict;
}

/*
this procefure remove spaces and tabs who could lead or end a string
*/
char * remove_leading_and_trailing_spaces(char* s)
{ 
    int start=0;
    int end=(int)strlen(s);
  
    //remove trailing blanks
    while(end>0 && (s[end-1]==' ' || s[end-1]=='\t'))
    {
        end--;
    }
    s[end]='\0';
    //remove leading blanks
    while(start<end && (*s==' ' || *s=='\t'))
    {
        s++;
        start++;
    }
    return s;
}


/*
This procedure transform the header to something required by wsgi.
*/
void transform_header_key_to_wsgi_key(char *src, char *dest) {
    *dest++='H';
    *dest++='T';
    *dest++='T';
    *dest++='P';
    *dest++='_';
    while (*src) { 
        if (*src != '-') { *dest++ = toupper(*src); }
        else { *dest++ ='_'; }
        src++;  
    }
    *dest = '\0';
}

/*
The procedure call the Environ method called "method" and give pydict has parameter
*/
void 
update_environ(PyObject *pyenviron, PyObject *pydict, char *method)
{
    PyObject *pyupdate=PyObject_GetAttrString(pyenviron, method);
    PyObject_CallFunction(pyupdate, "(O)", pydict);
    Py_DECREF(pyupdate);
}

/*
This method transform the received html header to a wsgi dictionary.
*/
static PyObject *
header_to_dict(struct client *cli)
{
    char *http_version, *protocol, *uri, *cmd, *head, *value;
    char *buff1, *buff2;
    PyObject *pydict = PyDict_New();
    PyObject *pyval;
    //we first analyse the first line of the header
    //printf("header_to_dict:port:%i, len=%i,%s**\n", cli->remote_port, (int)strlen(cli->input_header), cli->input_header);
    buff1 = (char *)calloc(strlen(cli->input_header)+1, sizeof(char));
    assert(buff1!=NULL);
    head = (char *)calloc(strlen(cli->input_header)+1, sizeof(char));
    assert(head!=NULL);
    stripChar(cli->input_header, buff1, '\r'); //every lines ends with \r\n. For simplicity we just remove \r 
    http_version=strsep(&buff1, "\n");
    if (!http_version)
         return Py_None;
    cmd=strsep(&http_version," ");
     if (!cmd)
         return Py_None;
     cli->cmd=(char *)calloc(strlen(cmd)+1, sizeof(char));
     assert(cli->cmd);
     strcpy(cli->cmd, cmd);   // will be cleaned with cli
     pyval = Py_BuildValue("s", cmd );
     PyDict_SetItemString(pydict, "REQUEST_METHOD", pyval);
     Py_DECREF(pyval);
    uri=strsep(&http_version," ");
     if (!uri)
         return Py_None;
     cli->uri=(char *)calloc(strlen(uri)+1, sizeof(char));
     assert(cli->uri);
     strcpy(cli->uri, uri);   // will be cleaned with cli
     pyval = Py_BuildValue("s", uri );
     PyDict_SetItemString(pydict, "fapws.uri", pyval);
     Py_DECREF(pyval);
    pyval = Py_BuildValue("s", http_version ); // stays HTTP/1.1
     PyDict_SetItemString(pydict, "HTTP_PROTOCOL", pyval);
     Py_DECREF(pyval);
    protocol=strsep(&http_version, "/");
     if (!protocol)
         return Py_None;
    cli->protocol=(char *)calloc(strlen(protocol)+1, sizeof(char));
     assert(cli->protocol);
     strcpy(cli->protocol, protocol);   // will be cleaned with cli
    pyval = Py_BuildValue("s", http_version );
     PyDict_SetItemString(pydict, "fapws.major_minor", pyval); // can be 0.9, 1.0 or 1.1
     Py_DECREF(pyval);
        

    pyval = Py_BuildValue("s", server_name );
    PyDict_SetItemString(pydict, "SERVER_NAME", pyval);
    Py_DECREF(pyval);
    pyval = Py_BuildValue("s", server_port );
    PyDict_SetItemString(pydict, "SERVER_PORT", pyval);
    Py_DECREF(pyval);
    //then we analyze all the other lines up to the body (not included) of the header 
    while (*buff1!='\n')
    {
        value=strsep(&buff1, "\n");
	if (!buff1)  //we have not found any \n
              break;
        buff2=strsep(&value, ":"); // the first ":" delimit the header and the value
        if (!value)  //we don't have found the ":"
            continue;
        if (strlen(buff2)>0)
        { 
            buff2=remove_leading_and_trailing_spaces(buff2);
            transform_header_key_to_wsgi_key(buff2, head);
            value=remove_leading_and_trailing_spaces(value);
            pyval = Py_BuildValue("s", value );
            PyDict_SetItemString(pydict, head, pyval);
            Py_DECREF(pyval);
        }
    }
    free(head);  
    //free(buff1); // TODO ?? to verify !! why not free it ??
    free(cmd); 
    return pydict;
}

/*
This procedure loops around the pre-defined registered uri to find if the requested uri match. 
Return 0 is no matches
Return 1 if a match has been found
This procedure update cli->uri_path in case of match. 
*/
static int 
handle_uri(struct client *cli)
{
    int i,res;
    PyObject *py_item, *py_uri, *wsgi_cb;
    char *uri;

    for (i=0;i<PyList_Size(py_registered_uri);i++)
    {
        py_item=PyList_GetItem(py_registered_uri, i);
        py_uri =PyTuple_GetItem(py_item,0);
        wsgi_cb = PyTuple_GetItem(py_item,1);
        Py_INCREF(wsgi_cb); //because of GetItem RTFM
        uri=PyString_AsString(py_uri);
        res=strncmp(uri, cli->uri, strlen(uri));
        if (res==0)
        {
            cli->uri_path=(char *)calloc(strlen(uri)+1, sizeof(char));
            strcpy(cli->uri_path, uri);   // will be cleaned with cli
            cli->wsgi_cb=wsgi_cb;
            return 1;
        }
    }
    return 0;
}

/*
This procedure generate some wsgi required parameters. Return a Python dictionary
*/
static PyObject *
py_build_method_variables( struct client *cli)
{
    PyObject* pydict = PyDict_New();
    char *rst_uri, *decoded_uri;
    int len=0;
    PyObject *pydummy=NULL;

    pydummy=PyString_FromString(server_name);
    PyDict_SetItemString(pydict, "SERVER_NAME", pydummy);
    Py_DECREF(pydummy);
    pydummy=PyString_FromString(server_port);
    PyDict_SetItemString(pydict, "SERVER_PORT", pydummy);
    Py_DECREF(pydummy);
    pydummy=PyString_FromString(cli->uri);
    PyDict_SetItemString(pydict, "fapws.uri", pydummy);
    Py_DECREF(pydummy);
   
    // Clean up the uri 
    len=strlen(cli->uri)-strlen(cli->uri_path)+1;
    rst_uri = (char *)calloc(len, sizeof(char));
    strncpy(rst_uri, cli->uri + strlen(cli->uri_path), len);
    pydummy=PyString_FromString(cli->uri_path);
    PyDict_SetItemString(pydict, "SCRIPT_NAME", pydummy);
    Py_DECREF(pydummy);
    
    if (strchr(rst_uri, '?') == NULL) {
        decoded_uri=decode_uri(rst_uri);
        pydummy=PyString_FromString(decoded_uri);
        free(decoded_uri);
        PyDict_SetItemString(pydict, "PATH_INFO", pydummy);
        Py_DECREF(pydummy);
        pydummy=PyString_FromString("");
        PyDict_SetItemString(pydict, "QUERY_STRING", pydummy);    
        Py_DECREF(pydummy);
    }
    else {
        char  *path_info, *query_string;
        query_string=strdup(rst_uri);
        path_info=strsep(&query_string,"?");
        decoded_uri=decode_uri(path_info);
        pydummy=PyString_FromString(decoded_uri);
        free(decoded_uri);
        PyDict_SetItemString(pydict, "PATH_INFO", pydummy);
        Py_DECREF(pydummy);
        pydummy=PyString_FromString(query_string);        
        PyDict_SetItemString(pydict,"QUERY_STRING",pydummy);
        Py_DECREF(pydummy);
        pydummy=parse_query(query_string);
        PyDict_SetItemString(pydict,"fapws.params",pydummy);
        Py_DECREF(pydummy);
        free(path_info);
    }
    free(rst_uri);
    return pydict;
}

/*
This procedure extract some info from the request
*/
PyObject *
py_get_request_info(struct client *cli)
{
    PyObject* pydict = PyDict_New();
    PyObject *pydummy=NULL;
    
    pydummy=PyString_FromString(cli->remote_addr);
    PyDict_SetItemString(pydict, "fapws.remote_addr", pydummy);
    PyDict_SetItemString(pydict, "REMOTE_ADDR", pydummy);
    Py_DECREF(pydummy);
    pydummy=Py_BuildValue("H", cli->remote_port);
    PyDict_SetItemString(pydict, "fapws.remote_port", pydummy);
    Py_DECREF(pydummy);
    pydummy=PyString_FromString(cli->protocol);
    PyDict_SetItemString(pydict, "fapws.protocol", pydummy);
    Py_DECREF(pydummy);
    return pydict;
}


/*
In case of POST, we must populate some additional wsgi parameters.
*/
static int  
manage_header_body(struct client *cli, PyObject *pyenviron)
{
    PyObject *pydummy; 

    pydummy=PyDict_GetItemString(pyenviron,"HTTP_CONTENT_LENGTH");
    if (pydummy==NULL) {
        //a POST without content-length is not a valid 
        if (debug) {
            printf("We cannot manage a POST without Content-Length\n");
            printf("Associated header:\n%s\n",cli->input_header);
        }
        return -411;
    }
    char *content_length_str = PyString_AsString(pydummy);
    int content_length = atoi(content_length_str);
    pydummy = PyInt_FromString(content_length_str, NULL, 10);
    PyDict_SetItemString(pyenviron, "CONTENT_LENGTH", pydummy); 
    Py_DECREF(pydummy);

    PyObject *pystringio=PyDict_GetItemString(pyenviron, "wsgi.input");
    Py_INCREF(pystringio);
    PyObject *pystringio_write=PyObject_GetAttrString(pystringio, "write");
    Py_DECREF(pystringio);
    pydummy = PyBuffer_FromMemory(cli->input_body, content_length);
    PyObject_CallFunction(pystringio_write, "(O)", pydummy);
    Py_DECREF(pydummy);
    Py_DECREF(pystringio_write);
    PyObject *pystringio_seek=PyObject_GetAttrString(pystringio, "seek");
    pydummy=PyInt_FromString("0", NULL, 10);
    PyObject_CallFunction(pystringio_seek, "(O)", pydummy);
    Py_DECREF(pydummy);
    Py_DECREF(pystringio_seek);

    //fapws.params cannot be done in case of multipart
    pydummy=PyDict_GetItemString(pyenviron,"HTTP_CONTENT_TYPE");
    if (pydummy!=NULL)
    {
        PyDict_SetItemString(pyenviron,"CONTENT_TYPE", pydummy);
    } else {
        PyDict_SetItemString(pyenviron,"CONTENT_TYPE", Py_None);
    }
    //no incref because value not needed
    if (pydummy!=NULL)
    {
        char *ct=PyString_AsString(pydummy);
        if (strncasecmp(ct, "multipart", 9)!=0) 
        {
            pydummy=parse_query(cli->input_body);
            PyDict_SetItemString(pyenviron,"fapws.params",pydummy);
            Py_DECREF(pydummy);
        }
    }
    return 0;
}

/*
This is the main python handler that will transform and treat the client html request. 
return 1 if we have found a python object to treat the requested uri
return 0 if not (page not found)
return -1 in case of problem
return -2 in case the request command is not implemented
*/
static int 
python_handler(struct client *cli)
{
    PyObject *pydict, *pydummy;
    int ret;

    if (debug)
         printf("host=%s,port=%i:python_handler:HEADER:\n%s**\n", cli->remote_addr, cli->remote_port, cli->input_header);
    //  1)initialise environ
    PyObject *pyenviron_class=PyObject_GetAttrString(py_base_module, "Environ");
    if (!pyenviron_class)
    {
         printf("load Environ failed from base module");
         exit(1);
    }
    PyObject *pyenviron=PyObject_CallObject(pyenviron_class, NULL);
    if (!pyenviron)
    {
         printf("Failed to create an instance of Environ");
         exit(1);
    }
    Py_DECREF(pyenviron_class);
    //  2)transform headers into a dictionary and send it to environ.update_headers
    pydict=header_to_dict(cli);
    if (pydict==Py_None)
    {
        Py_DECREF(pyenviron);
        return -500;
    }
    update_environ(pyenviron, pydict, "update_headers");
    Py_DECREF(pydict);   
    //  2bis) we check if the request method is supported
    PyObject *pysupportedhttpcmd = PyObject_GetAttrString(py_base_module, "supported_HTTP_command");
    pydummy = PyString_FromString(cli->cmd);
    if (PySequence_Contains(pysupportedhttpcmd,pydummy)!=1)
    {
        //return not implemented 
        Py_DECREF(pysupportedhttpcmd);
        Py_DECREF(pydummy);
        Py_DECREF(pyenviron);
        return -501;
    }
    Py_DECREF(pydummy);
    //  2ter) we treat directly the OPTIONS command
    if (strcmp(cli->cmd,"OPTIONS")==0)
    {
        pydummy=PyString_FromString("HTTP/1.1 200 OK\r\nServer: fapws3/" VERSION "\r\nAllow: ");
        PyObject *pyitem; 
        int index, max;
        max = PyList_Size(pysupportedhttpcmd);
        for (index=0; index<max; index++)
        {
            pyitem=PyList_GetItem(pysupportedhttpcmd, index);  // no need to decref pyitem
            PyString_Concat(&pydummy, PyObject_Str(pyitem));
            if (index<max-1)
               PyString_Concat(&pydummy, PyString_FromString(", "));
        }
        PyString_Concat(&pydummy, PyString_FromString("\r\nContent-Length: 0\r\n\r\n"));
        cli->response_header=PyString_AsString(pydummy);
	cli->response_header_length=strlen(cli->response_header);
        cli->response_content=PyList_New(0);
        Py_DECREF(pyenviron);
        return 1;
    }
    Py_DECREF(pysupportedhttpcmd);
    //  3)find if the uri is registered
    if (handle_uri(cli)!=1)
    {
         if (py_generic_cb==NULL)
         {
            //printf("uri not found\n");
            Py_DECREF(pyenviron);
            return 0;
         }
         else
         {
             cli->wsgi_cb=py_generic_cb;
             Py_INCREF(cli->wsgi_cb);
         }
     }
     else
     {
        // 4) build path_info, ...
        pydict=py_build_method_variables(cli);
        update_environ(pyenviron, pydict, "update_uri");
        Py_DECREF(pydict);   
        // 5) in case of POST, put it into the wsgi.input
        if (strcmp(cli->cmd,"POST")==0)
        {
            //printf("manage the post\n");
            ret=manage_header_body(cli, pyenviron);
            //printf("manage header return:%i\n",ret);
            if (ret < 0) {
                return ret;
            }
        }
    }
    //  6) add some request info
    pydict=py_get_request_info(cli);
    update_environ(pyenviron, pydict, "update_from_request");
    Py_DECREF(pydict);
    // 7) build response object
    PyObject *pystart_response_class=PyObject_GetAttrString(py_base_module, "Start_response");
    PyObject *pystart_response=PyInstance_New(pystart_response_class, NULL, NULL);
    Py_DECREF(pystart_response_class);
    // 8) execute python callbacks with his parameters
    PyObject *pyarglist = Py_BuildValue("(OO)", pyenviron, pystart_response );
    cli->response_content = PyEval_CallObject(cli->wsgi_cb,pyarglist);
    if (cli->response_content!=NULL) 
    {
        if ((PyFile_Check(cli->response_content)==0) && (PyIter_Check(cli->response_content)==1)) {
            //This is an Iterator object. We have to execute it first
            cli->response_content_obj = cli->response_content;
            cli->response_content = PyIter_Next(cli->response_content_obj);
        }
    }
    Py_DECREF(pyarglist);
    Py_XDECREF(cli->wsgi_cb);
    if (cli->response_content!=NULL) 
    {
        PyObject *pydummy = PyObject_Str(pystart_response);
        /*char *temp=NULL;
	temp=PyString_AsString(pydummy);
        Py_DECREF(pydummy);
        cli->response_header=(char *)calloc(strlen(temp)+1, sizeof(char));
        strcpy(cli->response_header, temp);*/
        cli->response_header=PyString_AsString(pydummy);
	cli->response_header_length=strlen(cli->response_header);
        Py_DECREF(pydummy);
    }
    else 
    //python call return is NULL
    {
        printf("Python error\n");
        cli->response_header="HTTP/1.1 500 Not found\r\nContent-Type: text/html\r\nServer: fapws3/" VERSION "\r\n\r\n";
	cli->response_header_length=strlen(cli->response_header);
        if (PyErr_Occurred()) 
        { 
             //get_traceback();py_b
             PyObject *pyerrormsg_method=PyObject_GetAttrString(py_base_module,"redirectStdErr");
             PyObject *pyerrormsg=PyObject_CallFunction(pyerrormsg_method, NULL);
             Py_DECREF(pyerrormsg_method);
             Py_DECREF(pyerrormsg);
             PyErr_Print();
             PyObject *pysys=PyObject_GetAttrString(py_base_module,"sys");
             PyObject *pystderr=PyObject_GetAttrString(pysys,"stderr");
             Py_DECREF(pysys);
/*             PyObject *pyclose_method=PyObject_GetAttrString(pystderr, "close");
             PyObject *pyclose=PyObject_CallFunction(pyclose_method, NULL);
             Py_DECREF(pyclose_method);
             Py_DECREF(pyclose);*/
             PyObject *pygetvalue=PyObject_GetAttrString(pystderr, "getvalue");
             Py_DECREF(pystderr);
             PyObject *pyres=PyObject_CallFunction(pygetvalue, NULL);
             Py_DECREF(pygetvalue);
             printf("%s\n", PyString_AsString(pyres));
             //test if we must send it to the page
             PyObject *pysendtraceback = PyObject_GetAttrString(py_config_module,"send_traceback_to_browser");
             cli->response_content=PyList_New(0);
             if (pysendtraceback==Py_True) {
                PyList_Append(cli->response_content, PyString_FromString("<h1>Error</h1><pre>"));
                PyList_Append(cli->response_content, pyres);
                PyList_Append(cli->response_content, PyString_FromString("</pre>"));
             } else {
                PyObject *pyshortmsg = PyObject_GetAttrString(py_config_module,"send_traceback_short");
                PyList_Append(cli->response_content, pyshortmsg);
                Py_DECREF(pyshortmsg);
             }
             Py_DECREF(pyres);
             Py_DECREF(pysendtraceback);
         }
         else 
         {
             cli->response_content=PyList_New(0);
             PyList_Append(cli->response_content, PyString_FromString("Page not found."));
         }
    }
    Py_XDECREF(pystart_response);
    Py_XDECREF(pyenviron);
    return 1;
}

/*
Procedure that will write "len" bytes of "response" to the client.
*/
static int write_cli(struct client *cli, char *response, size_t len,  int revents)
{
    size_t r=0, sent_len=MAX_BUFF;
    int c=0;
    if (revents & EV_WRITE){
        //printf("write_cli:uri=%s**\n", cli->uri);
        //printf("respnse:%i*****\n", (int)strlen(response));
        while ((int)len > 0)
        {
            if (len<sent_len)
            {
                 sent_len=len;
            }
            r=write(cli->fd,response ,sent_len);
            c++;
            if (debug)
                printf("host=%s,port=%i write_cli:uri=%s,r=%i,len=%i,c=%i\n", cli->remote_addr, cli->remote_port, cli->uri, (int)r, (int)len,c);
            if (((int)r<0) & (errno != EAGAIN))
            {
                cli->retry++;
                fprintf(stderr,"Failed to write to the client:%s:%i, #:%i.\n", cli->remote_addr, cli->remote_port, cli->retry);
                if (cli->retry>MAX_RETRY) 
                {
                    fprintf(stderr, "Connection closed after %i retries\n", cli->retry);
                    return 0; //stop the watcher and close the connection
                    }
                usleep(100000);  //failed but we don't want to close the watcher
            }
            if ((int)r==0)
            {
                return 1;
            }
            if ((int)r>0)
            {
                response+=(int)r;
                len -=r ;
            }
         }
         //p==len
         return 1;
    }
    else {
        printf("write callback not ended correctly\n");
        return 0; //stop the watcher and close the connection
    }

}

/*
This is the write call back registered within the event loop
*/
static void write_cb(struct ev_loop *loop, struct ev_io *w, int revents)
{ 
    char *response;
    int stop=0; //0: not stop, 1: stop, 2: stop and call tp close
    int ret; //python_handler return
    struct client *cli= ((struct client*) (((char*)w) - offsetof(struct client,ev_write)));
    if (cli->response_iter_sent==-2)
    { 
        //we must send an header or an error
        ret=python_handler(cli); //look for python callback and execute it
        if (ret==0) //look for python callback and execute it
        {
            //uri not found
            response="HTTP/1.1 500 Not found\r\nContent-Type: text/html\r\nServer: fapws3/" VERSION "\r\n\r\n<html><head><title>Page not found</head><body><p>Page not found!!!</p></body></html>";
            write_cli(cli,response, strlen(response), revents);
            stop=1;
        } 
        else if (ret==-411)
        {
            response="HTTP/1.1 411 Length Required\r\nContent-Type: text/html\r\nServer: fapws3/" VERSION "\r\n\r\n<html><head><title>Length Required</head><body><p>Length Required!!!</p></body></html>";
            write_cli(cli,response, strlen(response), revents);
            stop=1;
        }
        else if (ret==-500)
        {
            response="HTTP/1.1 500 Internal Server Error\r\nContent-Type: text/html\r\nServer: fapws3/" VERSION "\r\n\r\n<html><head><title>Internal Server Error</head><body><p>Internal Server Error!!!</p></body></html>";
            write_cli(cli,response, strlen(response), revents);
            stop=1;
        }
        else if (ret==-501)
        {
            //problem to parse the request
            response="HTTP/1.1 501 Not Implemented\r\nContent-Type: text/html\r\nServer: fapws3/" VERSION "\r\n\r\n<html><head><title>Not Implemented</head><body><p>Not Implemented!!!</p></body></html>";
            write_cli(cli,response, strlen(response), revents);
            stop=1;
        }
        else
        {
            //uri found, we thus send the html header 
            write_cli(cli, cli->response_header, cli->response_header_length, revents);
            cli->response_iter_sent++; //-1: header sent
        }
    } 
    else if (strcmp(cli->cmd,"HEAD")==0)
    {
        //we don't send additonal data for a HEAD command
        stop=2;
    }
    else 
    {
        //we let the python developer to manage other HTTP command
        if ((PyList_Check(cli->response_content))  && (cli->response_content_obj==NULL)) //we treat list object
        {
            cli->response_iter_sent++;
            if (cli->response_iter_sent<PyList_Size(cli->response_content)) 
            {
                PyObject *pydummy = PyList_GetItem(cli->response_content, cli->response_iter_sent);
                char *buff;
#if (PY_VERSION_HEX < 0x02050000)
                int buflen;
                if (PyObject_AsReadBuffer(pydummy, (const void **) &buff, &buflen)==0)
#else
                Py_ssize_t buflen;
                if (PyObject_AsReadBuffer(pydummy, (const void **) &buff, &buflen)==0)
#endif
                {
                    // if this is a readable buffer, we send it. Other else, we ignore it.
                    if (write_cli(cli, buff, buflen, revents)==0)
                    {
                        cli->response_iter_sent=PyList_Size(cli->response_content);  //break the for loop
                    }
                }
                else
                {
                    printf("The item %i of your list is not a string!!!!  It will be skipped\n",cli->response_iter_sent);
                }            }
            else // all iterations has been sent
            {
                stop=2;
            }    
        } 
        else if (PyFile_Check(cli->response_content) && (cli->response_content_obj==NULL)) // we treat file object
        {
            if (cli->response_iter_sent==-1) // we need to initialise the file descriptor
            {
                cli->response_fp=PyFile_AsFile(cli->response_content);
            }
            cli->response_iter_sent++;
            char buff[MAX_BUFF]="";  
            size_t len=fread(buff, sizeof(char), MAX_BUFF, cli->response_fp);
            if ((int)len==0)
            {
                stop=2;
            }
            else
            {
                if (write_cli(cli,buff, len, revents)==0)
                {
                    stop=2;
                }
                if ((int)len<MAX_BUFF)
                {
                    //we have send the whole file
                    stop=2;
                }
            }
            //free(buff);
        } 
        else if (PyIter_Check(cli->response_content_obj)) //we treat Iterator object
        {
            cli->response_iter_sent++;
            PyObject *pyelem = cli->response_content;
            if (pyelem == NULL) 
            {
                stop = 2;
            }
            else 
            {
                char *buff;
#if (PY_VERSION_HEX < 0x02050000)
                int buflen;
                if (PyObject_AsReadBuffer(pyelem, (const void **) &buff, &buflen)==0)
#else
                Py_ssize_t buflen;
                if (PyObject_AsReadBuffer(pyelem, (const void **) &buff, &buflen)==0)
#endif
                {
                    // if this is a readable buffer, we send it. Other else, we ignore it.
                    if (write_cli(cli, buff, buflen, revents)==0)
                    {
                        stop=2;  //break the iterator loop
                    }
                }
                else
                {
                    printf("The item %i of your iterator is not a string!!!!  It will be skipped\n",cli->response_iter_sent);
                }
                Py_DECREF(pyelem);
                cli->response_content = PyIter_Next(cli->response_content_obj);
                if (cli->response_content==NULL)
                {
                     if (debug)
                     {
                         printf("host=%s,port=%i iterator ended uri=%s\n", cli->remote_addr, cli->remote_port, cli->uri );
                     }
                     stop=2;
                }
            }    
        } 
        else 
        {
            printf("wsgi output of is neither a list neither a fileobject\n");
            //PyErr_SetString(PyExc_TypeError, "Result must be a list or a fileobject");
            stop=1;
        }
    }// end of GET OR POST request
    if (stop==2)
    {
      if (cli->response_content!=NULL) {
        if (PyObject_HasAttrString(cli->response_content, "close"))
        {
            PyObject *pydummy=PyObject_GetAttrString(cli->response_content, "close");
            PyObject_CallFunction(pydummy, NULL);
            Py_DECREF(pydummy);
        }
      }
      ev_io_stop(EV_A_ w);
      close_connection(cli);
    }
    if (stop==1)
    {
        ev_io_stop(EV_A_ w);
        close_connection(cli);
    }
}

/*
The procedure is the connection callback registered in the event loop
*/
static void connection_cb(struct ev_loop *loop, struct ev_io *w, int revents)
{ 
    struct client *cli= ((struct client*) (((char*)w) - offsetof(struct client,ev_read)));
    size_t r=0;
    char rbuff[MAX_BUFF]="";
    int read_finished=0;
    char *err=NULL;
    if (revents & EV_READ){
        //printf("pass revents\n");
        r=read(cli->fd,rbuff,MAX_BUFF);
        //printf("read %i bytes\n", r);
        if ((int)r<0) {
            fprintf(stderr, "Failed to read the client data. %i tentative\n", cli->retry);
            cli->retry++;
            if (cli->retry>MAX_RETRY) 
            {
                fprintf(stderr, "Connection closed after %i retries\n", cli->retry);
                ev_io_stop(EV_A_ w);
                close_connection(cli);
                return ;
                }
            return;
        }
        if ((int)r==0) {
            read_finished=1;
        } 
        else
        {
            cli->input_header=realloc(cli->input_header, (cli->input_pos + r + 1)*sizeof(char));
            memcpy(cli->input_header + cli->input_pos, rbuff, r); 
            cli->input_pos += r; 
            cli->input_header[cli->input_pos]='\0';
            if (debug)
                printf("host=%s,port=%i connection_cb:cli:%p, input_header:%p, input_pos:%i, r:%i\n", cli->remote_addr, cli->remote_port, cli, cli->input_header, (int)cli->input_pos, (int)r);
            // if \r\n\r\n then end of header   
            cli->input_body=strstr(cli->input_header, "\r\n\r\n"); //use memmem ???
            int header_lentgh =cli->input_body-cli->input_header;
            if (cli->input_body!=NULL)
            {
                //if content-length
                char *contentlenght=strstr(cli->input_header, "Content-Length: ");
                if (contentlenght==NULL)
                {
                    read_finished=1;
                }
                else 
                {
                    int bodylength=strtol(contentlenght+16, &err, 10);
                      //assure we have all body data
                    if ((int)cli->input_pos==bodylength+4+header_lentgh)
                    {
                        read_finished=1;
                        cli->input_body+=4; // to skip the \r\n\r\n
                    }
                }
            }
         }
         if (read_finished)
         {
            ev_io_stop(EV_A_ w);
            if (strlen(cli->input_header)>0)
            {
                ev_io_init(&cli->ev_write,write_cb,cli->fd,EV_WRITE);
                ev_io_start(loop,&cli->ev_write);
            }
            else
            { 
                //this is not a normal request, we thus free the parameters created during the initialisation in accept_cb
                close(cli->fd);
                free(cli->input_header);
            }
         }
    }
    else {
        printf("read callback not ended correctly\n");
    }
}

/*
This is the accept call back registered in the event loop
*/
static void accept_cb(struct ev_loop *loop, struct ev_io *w, int revents)
{
    int client_fd;
    struct client *cli;
    struct sockaddr_in client_addr;
    socklen_t client_len = sizeof(client_addr);
    client_fd = accept(w->fd, (struct sockaddr *)&client_addr, &client_len);
        if (client_fd == -1) {
                return;
        }
    //intialisation of the client struct
    cli = calloc(1,sizeof(struct client));
    cli->fd=client_fd;
    cli->input_header=malloc(1*sizeof(char));  //will be free'd when we will close the connection
    cli->input_body=NULL;
    cli->uri=NULL;
    cli->cmd=NULL;
    cli->protocol=NULL;
    cli->uri_path=NULL;
    cli->wsgi_cb=NULL;
    cli->response_header=NULL;
    cli->response_content=NULL;
    cli->response_content_obj=NULL;
    if (debug)
        printf("host:%s,port:%i accept_cb: cli:%p, input_header:%p\n", inet_ntoa (client_addr.sin_addr),ntohs(client_addr.sin_port), cli, cli->input_header);
    cli->input_pos=0;
    cli->retry=0;
    cli->response_iter_sent=-2;
    cli->remote_addr=inet_ntoa (client_addr.sin_addr);
    cli->remote_port=ntohs(client_addr.sin_port);
    if (setnonblock(cli->fd) < 0)
                fprintf(stderr, "failed to set client socket to non-blocking");
    ev_io_init(&cli->ev_read,connection_cb,cli->fd,EV_READ);
    //printf("accept_cb done\n");
    ev_io_start(loop,&cli->ev_read);
}

/*
This is the sigint callback registered in the event loop
*/
static void sigint_cb(struct ev_loop *loop, ev_signal *w, int revents)
{
    printf("Bye.\n");
    ev_unloop(loop, EVUNLOOP_ALL);
}

/*
This is the sigpipe callback registered in the event loop
*/
static void sigpipe_cb(struct ev_loop *loop, ev_signal *w, int revents)
{
    printf("SIGPIPE encountered !!!! We ignore it.\n");
}



/*
Procedure exposed in Python will establish the socket and the connection.
*/
static PyObject *
py_ev_start(PyObject *self, PyObject *args)
{
/*
code copied from the nice book written by Bee:
http://beej.us/guide/bgnet/output/html/singlepage/bgnet.html
*/
    struct addrinfo hints, *servinfo, *p;
//    struct sockaddr_storage their_addr; // connector's address information
    int yes=1;
    int rv;

    PyArg_ParseTuple(args, "ss", &server_name, &server_port);
    memset(&hints, 0, sizeof hints);
    hints.ai_family = AF_UNSPEC;
    hints.ai_socktype = SOCK_STREAM;
    hints.ai_flags = AI_PASSIVE; // use my IP
    if ((rv = getaddrinfo(server_name, server_port, &hints, &servinfo)) == -1) {
        fprintf(stderr, "getaddrinfo: %s\n", gai_strerror(rv));
        exit(1);
    }

    // loop through all the results and bind to the first we can
    for(p = servinfo; p != NULL; p = p->ai_next) {
        if ((sockfd = socket(p->ai_family, p->ai_socktype,
                p->ai_protocol)) == -1) {
            perror("server: socket");
            continue;
        }

        if (setsockopt(sockfd, SOL_SOCKET, SO_REUSEADDR, &yes,
                sizeof(int)) == -1) {
            perror("setsockopt");
            exit(1);
        }

        if (bind(sockfd, p->ai_addr, p->ai_addrlen) == -1) {
            close(sockfd);
            perror("server: bind");
            continue;
        }

        break;
    }

    if (p == NULL)  {
        fprintf(stderr, "server: failed to bind\n");
        exit(1);
    }

    freeaddrinfo(servinfo); // all done with this structure

    if (listen(sockfd, BACKLOG) == -1) {
        perror("listen");
        exit(1);
    }
    printf("listen on %s:%s\n", server_name, server_port);
    return Py_None;
}

/*
Procedure exposed in Python will generate and start the event loop
*/
static PyObject *
py_run_loop(PyObject *self, PyObject *args)
{
    char *backend="";
    ev_io accept_watcher;
    ev_signal signal_watcher, signal_watcher2;
    struct ev_loop *loop = ev_default_loop (0);
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
    ev_loop (loop, 0);
    return Py_None;
}

/*
Procedure exposed in Python to provide extension's version
*/
static PyObject *
py_version(PyObject *self, PyObject *args)
{
    PyObject *pyres=Py_BuildValue("s", "3.b.0");
    return pyres;
}

/*
Procedure exposed in Python to provide libev's ABI version
*/
static PyObject *
py_libev_version(PyObject *self, PyObject *args)
{
    PyObject *pyres=Py_BuildValue("ii", ev_version_major(), ev_version_minor());
    return pyres;
}



/*
Procedure exposed in Python to register the "base" module
*/
static PyObject *
py_set_base_module(PyObject *self, PyObject *args)
{
    if (!PyArg_ParseTuple(args, "O", &py_base_module)) 
        return NULL;
    py_config_module=PyObject_GetAttrString(py_base_module, "config");
    py_registered_uri = PyList_New(0);
    return Py_None;    
}

/*
Procedure exposed in Python to add the tuple: uri, wsgi call back
*/
static PyObject *
py_add_wsgi_cb(PyObject *self, PyObject *args)
{
    PyObject *py_tuple;
    if (!PyArg_ParseTuple(args, "O", &py_tuple)) 
        return NULL;
    PyList_Append(py_registered_uri, py_tuple);
    return Py_None;    
}
    
/*
Procedure exposed in Python to expose "parse_query"
*/
PyObject *
py_parse_query(PyObject *self, PyObject *args)
{
    char *uri;

    if (!PyArg_ParseTuple(args, "s", &uri))
        return NULL;
    return parse_query(uri);
}

/*
Procedure exposed in Python to register the generic python callback
*/
PyObject *
py_set_gen_wsgi_cb(PyObject *self, PyObject *args)
{
    if (!PyArg_ParseTuple(args, "O", &py_generic_cb))
        return NULL;
    return Py_None;
}

/*
*/
PyObject *
py_set_debug(PyObject *self, PyObject *args)
{
    if (!PyArg_ParseTuple(args, "i", &debug))
        return NULL;
    return Py_None;
}

/*
*/
PyObject *
py_get_debug(PyObject *self, PyObject *args)
{
    return Py_BuildValue("i", debug);
}


static PyMethodDef EvhttpMethods[] = {
    {"start", py_ev_start, METH_VARARGS, "Define evhttp sockets"},
    {"version", py_version, METH_VARARGS, "return the version of the shared object"}, 
    {"set_base_module", py_set_base_module, METH_VARARGS, "set you base module"},
    {"run", py_run_loop, METH_VARARGS, "Run the main loop"},
    {"wsgi_cb", py_add_wsgi_cb, METH_VARARGS, "Add an uri and his wsgi callback in the list of uri to watch"},
    {"wsgi_gen_cb", py_set_gen_wsgi_cb, METH_VARARGS, "Set the generic wsgi callback"},
    {"parse_query", py_parse_query, METH_VARARGS, "parse query into dictionary"},
    {"set_debug", py_set_debug, METH_VARARGS, "Set the debug level"},
    {"get_debug", py_get_debug, METH_VARARGS, "Get the debug level"},
    {"libev_version", py_libev_version, METH_VARARGS, "Get the libev's ABI version you are using"},
    {NULL, NULL, 0, NULL}        /* Sentinel */
};

PyMODINIT_FUNC
init_evwsgi(void)
{
    (void) Py_InitModule("_evwsgi", EvhttpMethods);
}
