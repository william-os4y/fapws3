# copy these lines to a file named: setup.py
# To build and install the elemlist module you need the following
# setup.py file that uses the distutils:
from distutils.core import setup, Extension
import os
import os.path 
import sys

setup (name = "fapws3",
       version = "0.1",
       maintainer = "William",
       maintainer_email = "william.os4y@gmail.com",
       description = "FAPWS Python module",
       packages= ['fapws','fapws/contrib'],

       ext_modules = [
	       Extension('fapws._evwsgi',
	       sources=['fapws/_evwsgi.c'],
           # I'm on an archlinux ;-)
           # Here I'm pointing to the direcoty where libevent has been build
           # In this directory wi can find sources and compiled objects (as after a "./configure; make")
	       #include_dirs=["/usr/include"],
	       #library_dirs=["/usr/local/lib"], # add LD_RUN_PATH in your environment
	       libraries=['ev'],
           #extra_compile_args=["-ggdb"],
           #define_macros=[("DEBUG", "1")],
	       )
	       ]
)

# end of file: setup.py
