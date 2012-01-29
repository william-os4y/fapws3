int PyFile_Check(PyObject *obj);

FILE *PyFile_AsFile(PyObject *pfd);

char *PyBytes_AsChar(PyObject *pyobj);

PyObject *PyBytes_FromChar(char * buf);

int PyDict_SetItemChar(PyObject *pydict, char *key, PyObject *pyval);

PyObject *PyDict_GetItemChar(PyObject *pydict, char *key);
