#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <errno.h>
#include <string.h>
#include <Python.h>

#include "extra.h"
#include "common.h"
#include "wsgi.h"
#include "compat.h"

extern char *server_name;
extern char *server_port;
extern int debug;

/*
This procdure analyse uri and return a Python dictionary with every parameters as keys and their associated values into a list. 
*/
PyObject *parse_query(char * uri)
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
        if ((pyelem=PyDict_GetItemChar(pydict, key))==NULL) {
            pyelem=PyList_New(0);
        } else {
            Py_INCREF(pyelem); // because of GetItem 
        }
        pydummy=PyBytes_FromChar(value);
        free(value);
        PyList_Append(pyelem, pydummy);
        Py_DECREF(pydummy);
        PyDict_SetItemChar(pydict, key, pyelem);
        free(key);
        Py_DECREF(pyelem); 
    }
    free(line);
    return pydict;
}


/*
GET /hello/toto?param=key HTTP/1.1\r\n
Host: 127.0.0.1:8080\r\n
User-Agent: Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.2.3) Gecko/20100423 Ubuntu/10.04 (lucid) Firefox/3.6.3\r\n
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*;q=0.8\r\n
Accept-Language: en-us,en;q=0.5\r\n
Accept-Encoding: gzip,deflate\r\n
Accept-Charset: ISO-8859-1,utf-8;q=0.7,*;q=0.7\r\n
Keep-Alive: 115\r\n
Connection: keep-alive\r\n
Cookie: __utma=96992031.1741467985.1258282980.1258282980.1258282980.1\r\n
Cache-Control: max-age=0\r\n
\r\n


Request becomes:
----------------
REQUEST_METHOD fapws.uri wsgi.url_scheme/fapws.major_minor\r\n
HTTP_<header>:<value>\r\n
\r\n
<wsgi.input>\r\n


fapws.uri becomes
-----------------
SCRIPT_NAME/PATH_INFO?QUERY_STRING

QUERY_STRING becomes
--------------------
a dictionary key and list of values


{
 'fapws.params': {b'param': [b'key']}, 
 'fapws.uri': b'/hello/toto?param=key', 
 'fapws.raw_header': b'...'
 'fapws.major_minor': b'1.1', 
 'fapws.remote_addr': b'127.0.0.1', 
 'fapws.remote_port': 60580, 
 'fapws.socket_fd': 4,
 'REQUEST_METHOD': b'GET', 
 'SCRIPT_NAME': b'/hello', 
 'QUERY_STRING': b'param=key', 
 'SERVER_NAME': b'0.0.0.0', 
 'SERVER_PORT': b'8080', 
 'PATH_INFO': b'/toto'
 'REMOTE_ADDR': b'127.0.0.1', 
 'HTTP_PROTOCOL': b'HTTP/1.1', 
 'wsgi.input': <_io.BytesIO object at 0xb75e7dc0>, 
 'wsgi.multithread': False, 
 'wsgi.version': (1, 0), 
 'wsgi.run_once': False, 
 'wsgi.errors': <_io.StringO object at 0xb75e7da0>, 
 'wsgi.multiprocess': True, 
 'wsgi.url_scheme': b'http', 
 'HTTP_COOKIE': b'__utma=96992031.1741467985.1258282980.1258282980.1258282980.1', 
 'HTTP_HOST': b'127.0.0.1:8080', 
 'HTTP_KEEP_ALIVE': b'115', 
 'HTTP_CONNECTION': b'keep-alive', 
 'HTTP_CACHE_CONTROL': b'max-age=0', 
 'HTTP_ACCEPT': b'text/html,application/xhtml+xml,application/xml;q=0.9,*;q=0.8', 
 'HTTP_ACCEPT_CHARSET': b'ISO-8859-1,utf-8;q=0.7,*;q=0.7', 
 'HTTP_USER_AGENT': b'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.2.3) Gecko/20100423 Ubuntu/10.04 (lucid) Firefox/3.6.3', 
 'HTTP_ACCEPT_LANGUAGE': b'en-us,en;q=0.5', 
 'HTTP_ACCEPT_ENCODING': b'gzip,deflate', 
}





*/



#define CR '\r'
#define LF '\n'
#define BLANK ' '
#define KEY_SEP ':'

enum state
  { s_stop = 1 ,
    s_firstline_start,
    s_firstline_w1,
    s_firstline_w2,
    s_header_key,
    s_header_val,
    s_body
  };
 
 

 void set_char(char *from, char *to, int i, int *j)
 {
    int t;
    t=*j;
     if (t==0 && (from[i]==CR || from[i]==LF || from[i]==BLANK))
     {
     //printf("Character to skip\n");
     } 
     else
    {
       to[t]=from[i];
       t++;
       *j=t;
    }

}



/*
This procedure transform the header to something required by wsgi.
*/
void transform_header_key_to_wsgi_key(char *src, char *dest)
{
    char *start;
    start = dest;
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
    dest = start;  //we reset the pointer to the begining of the string
}


/*
This method transform the received html header to a wsgi dictionary.
*/
PyObject * header_to_dict (struct client *cli)
{
   char ch, *buf;
   int len;
   enum state state;
   int i;
   int j=0;
   int sw_query_string=0;
   char *data;
   char *buf2;
   
   buf=cli->input_header;
   
   PyObject *pydict = PyDict_New();
   PyObject *pyval;
   PyObject *pyheader_key=NULL;

   pyval = PyBytes_FromChar(cli->input_header); 
   PyDict_SetItemString(pydict, "fapws.raw_header", pyval);
   Py_DECREF(pyval);

   len=strlen(buf);
   data=malloc(len);
   buf2=malloc(len);

   state=s_firstline_start;
   for (i=0;i<len;i++)
   {
     ch=buf[i];
     //printf("%i - %i\n",i, j);
     switch (state)
     {
       case s_firstline_start:
         set_char(buf, data, i, &j);
         if (ch==BLANK)
         { 
           state=s_firstline_w1;
           data[j-1]='\0';
           j=0;
           //printf("METHOD:%s***\n",data);
           cli->cmd=malloc(strlen(data)+1);
           assert(cli->cmd);
           strcpy(cli->cmd, data);   // will be cleaned with cli
           pyval = PyBytes_FromChar(data);
           PyDict_SetItemString(pydict, "REQUEST_METHOD", pyval);
           Py_DECREF(pyval);
         }
         break;
     case s_firstline_w1:
         set_char(buf, data, i, &j);
         if (ch=='?') sw_query_string=j+1;
         if (ch==BLANK)
         { 
           state=s_firstline_w2;
           data[j-1]='\0';
           //printf("PATH:%s***\n",data);
           pyval = PyBytes_FromChar(data);
           PyDict_SetItemString(pydict, "fapws.uri", pyval);
           Py_DECREF(pyval);
           cli->uri=malloc(strlen(data)+1);
           assert(cli->uri);
           strcpy(cli->uri, data);   // will be cleaned with cli
           char *query_string;
           query_string=data+sw_query_string-1;
           //printf("QUERY_STRING:%s***\n", query_string);
           pyval = PyBytes_FromChar(query_string);
           PyDict_SetItemString(pydict, "QUERY_STRING", pyval);
           Py_DECREF(pyval);
           j=0;
           
         }
         break;
     case s_firstline_w2:
         set_char(buf, data, i, &j);
         if (ch==CR)
         { 
           state=s_header_key;
           data[j-1]='\0';
           //printf("PROTOCOL FULL:%s***\n",data);
           char *major_minor;
           major_minor=data+j-1-3;
           //printf("MAJOR MINOR:%s***\n",major_minor); 
           pyval = PyBytes_FromChar(major_minor);
           PyDict_SetItemString(pydict, "fapws.major_minor", pyval);
           Py_DECREF(pyval);
           pyval = PyBytes_FromChar(data); 
           PyDict_SetItemString(pydict, "SERVER_PROTOCOL", pyval);
           PyDict_SetItemString(pydict, "REQUEST_PROTOCOL", pyval);
           Py_DECREF(pyval);
           data[j-1-4]='\0'; //remove "/1.1" for example
           //printf("SCHEME:%s***\n",data); 
           pyval = PyBytes_FromChar(data); 
           PyDict_SetItemString(pydict, "wsgi.url_scheme", pyval);
           Py_DECREF(pyval);
           j=0;
         }
         break;
     case s_header_key:
         if (buf[i]==CR) state=s_body;
         set_char(buf, data, i, &j);
         if (ch==KEY_SEP)
         { 
           state=s_header_val;
           data[j-1]='\0';
           j=0;
           //printf("KEY:%s***\n",data);
           transform_header_key_to_wsgi_key(data, buf2);
           pyheader_key=PyUnicode_FromString(buf2);
           
         }
         break;
     case s_header_val:
         set_char(buf, data, i, &j);
         if (ch==CR)
         { 
           state=s_header_key;
           data[j-1]='\0';
           j=0;
           //printf("VAL:%s***\n",data);
           pyval = PyBytes_FromChar(data);
           PyDict_SetItem(pydict, pyheader_key, pyval);
           Py_DECREF(pyval);
           Py_DECREF(pyheader_key);
         }
         break;
     case s_body:
         set_char(buf, data, i, &j);
         break;
     case s_stop:
         break;
     }
   }

   free(data);
   free(buf2);
   return pydict;
}



/*
This procedure generate some wsgi required parameters. Return a Python dictionary
*/
PyObject *py_build_method_variables( struct client *cli)
{
    PyObject* pydict = PyDict_New();
    char *rst_uri, *decoded_uri;
    int len=0;
    PyObject *pydummy=NULL;

    pydummy=PyBytes_FromChar(server_name);
    PyDict_SetItemString(pydict, "SERVER_NAME", pydummy);
    Py_DECREF(pydummy);
    pydummy=PyBytes_FromChar(server_port);
    PyDict_SetItemString(pydict, "SERVER_PORT", pydummy);
    Py_DECREF(pydummy);
   
    // Clean up the uri 
    len=strlen(cli->uri)-strlen(cli->uri_path)+1;
    rst_uri = (char *)calloc(len, sizeof(char));
    strncpy(rst_uri, cli->uri + strlen(cli->uri_path), len);
    pydummy=PyBytes_FromChar(cli->uri_path);
    PyDict_SetItemString(pydict, "SCRIPT_NAME", pydummy);
    Py_DECREF(pydummy);
    
    if (strchr(rst_uri, '?') == NULL) {
        decoded_uri=decode_uri(rst_uri);
        pydummy=PyBytes_FromChar(decoded_uri);
        free(decoded_uri);
        PyDict_SetItemString(pydict, "PATH_INFO", pydummy);
        Py_DECREF(pydummy);
        pydummy=PyBytes_FromChar("");
        PyDict_SetItemString(pydict, "QUERY_STRING", pydummy);    
        Py_DECREF(pydummy);
    }
    else {
        char  *path_info, *query_string;
        query_string=strdup(rst_uri);
        path_info=strsep(&query_string,"?");
        decoded_uri=decode_uri(path_info);
        pydummy=PyBytes_FromChar(decoded_uri);
        free(decoded_uri);
        PyDict_SetItemString(pydict, "PATH_INFO", pydummy);
        Py_DECREF(pydummy);
        pydummy=PyBytes_FromChar(query_string);        
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
PyObject *py_get_request_info(struct client *cli)
{
    PyObject* pydict = PyDict_New();
    PyObject *pydummy=NULL;
    
    pydummy=PyBytes_FromChar(cli->remote_addr);
    PyDict_SetItemString(pydict, "fapws.remote_addr", pydummy);
    PyDict_SetItemString(pydict, "REMOTE_ADDR", pydummy);
    Py_DECREF(pydummy);
    pydummy=Py_BuildValue("H",cli->remote_port);
    PyDict_SetItemString(pydict, "fapws.remote_port", pydummy);
    Py_DECREF(pydummy);
    pydummy=PyLong_FromLong(cli->fd);
    PyDict_SetItemString(pydict, "fapws.socket_fd", pydummy);
    Py_DECREF(pydummy);
    return pydict;
}

/*
In case of POST, we must populate some additional wsgi parameters.
*/
int manage_header_body(struct client *cli)
{
    PyObject *pydummy; 

    pydummy=PyDict_GetItemString(cli->pyenviron,"HTTP_CONTENT_LENGTH");
    if (pydummy==NULL) {
        //a POST without content-length is not a valid 
        if (debug) {
            printf("We cannot manage a POST without Content-Length\n");
            printf("Associated header:\n%s\n",cli->input_header);
        }
        return -411;
    }
    char *content_length_str = PyBytes_AsChar(pydummy);
    pydummy = PyLong_FromString(content_length_str, NULL, 10);
    PyDict_SetItemString(cli->pyenviron, "CONTENT_LENGTH", pydummy); 
    Py_DECREF(pydummy);

    //fapws.params cannot be done in case of multipart
    pydummy=PyDict_GetItemString(cli->pyenviron,"HTTP_CONTENT_TYPE");
    if (pydummy!=NULL)
    {
        PyDict_SetItemString(cli->pyenviron,"CONTENT_TYPE", pydummy);
    } else {
        PyDict_SetItemString(cli->pyenviron,"CONTENT_TYPE", Py_None);
    }
    //no incref because value not needed
    if (pydummy!=NULL)
    {
        char *ct=PyBytes_AsChar(pydummy);
        if (strncasecmp(ct, "application/x-www-form-urlencoded", 33)==0) 
        { 
            pydummy=parse_query(cli->input_body);
            PyDict_SetItemString(cli->pyenviron,"fapws.params",pydummy);
            Py_DECREF(pydummy);
        }
    }
    return 0;
}

