#include <ev.h>
#include <Python.h>


#define MAXHEADER 4096


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
        char *http_major_minor;
        char *uri_path;   //correspond to the registered uri_header 
        PyObject *wsgi_cb;
        int response_iter_sent; //-2: nothing sent, -1: header sent, 0-9999: iter sent
        char response_header[MAXHEADER];
        int response_header_length;
        PyObject *response_content;
        PyObject *response_content_obj;
        FILE *response_fp; // file of the sent file
};

struct TimerObj {
        ev_timer timerwatcher;
        float delay;
        PyObject *py_cb;
};


