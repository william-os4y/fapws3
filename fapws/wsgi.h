

PyObject *parse_query(char * uri);

void transform_header_key_to_wsgi_key(char *src, char *dest);

PyObject * header_to_dict(struct client *cli);

PyObject *py_build_method_variables( struct client *cli);

PyObject *py_get_request_info(struct client *cli);

int manage_header_body(struct client *cli, PyObject *pyenviron);
