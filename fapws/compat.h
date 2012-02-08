#if PY_MAJOR_VERSION >= 3
int PyFile_Check(PyObject *obj);
#endif

char *PyBytes_AsChar(PyObject *pyobj);

PyObject *PyBytes_FromChar(char * buf);

int PyDict_SetItemChar(PyObject *pydict, char *key, PyObject *pyval);

PyObject *PyDict_GetItemChar(PyObject *pydict, char *key);
