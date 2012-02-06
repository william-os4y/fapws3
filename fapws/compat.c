

#include <Python.h>
#include "common.h"

#if PY_MAJOR_VERSION >= 3
/* 
For PYthon3 compatibility 
*/
extern PyTypeObject PyIOBase_Type;
int PyFile_Check(PyObject *obj) 
{
    return PyObject_IsInstance(obj, (PyObject *)&PyIOBase_Type);
}

FILE *PyFile_AsFile(PyObject *pfd)
{
   FILE *fp;
   int fd = PyObject_AsFileDescriptor(pfd);
   fp = fdopen(fd, "r");
   return fp;
}
#endif

char *PyBytes_AsChar(PyObject *pyobj)
{
   
#if PY_MAJOR_VERSION >= 3
   char *buf=NULL;
   if (!pyobj)
       printf("You are trying to convert a NULL object!!\n");
   
   if (!PyBytes_Check(pyobj))
   {
       PyObject *pydummy = PyUnicode_AsEncodedString(pyobj, "utf-8", "Error"); 
       buf = PyBytes_AsString(pydummy); 
       Py_DECREF(pydummy);
   }
   else
   {
       buf = PyBytes_AsString(pyobj); 
   }
#else
   char *buf = PyString_AsString(pyobj); 
#endif
   return buf;
}


PyObject *PyBytes_FromChar(char * buf)
{
   PyObject *pyres ;
#if PY_MAJOR_VERSION >= 3
   pyres = PyBytes_FromString(buf);
#else
   pyres = PyString_FromChar(buf):
#endif
   return pyres;
}

int PyDict_SetItemChar(PyObject *pydict, char *key, PyObject *pyval)
{
    PyObject *pykey = PyBytes_FromChar(key);
    PyObject *pyret = PyDict_SetItem(pydict, pykey, pyval);
    Py_DECREF(pykey);
    return pyret;
}


PyObject *PyDict_GetItemChar(PyObject *pydict, char *key)
{
    PyObject *pykey = PyBytes_FromChar(key);
    PyObject *pyret = PyDict_GetItem(pydict, pykey);
    Py_DECREF(pykey);
    return pyret;
}




