from setuptools import setup, find_packages, Extension
import os
import sys
import os.path

def read_file(name):
    return open(os.path.join(os.path.dirname(__file__),name)).read()

def find_file(fname, dirs):
    founded=False
    for ckdir in dirs:
        fpname=os.path.join(ckdir,fname)
        if os.path.isfile(fpname):
            founded=True
        if founded:
            #print "----------Find",fname," in ", ckdir
            return True
        #we don't find it, it can be located into a subdirectory ;-)
        localdirs=[]
        for elem in os.listdir(ckdir):
            fpname=os.path.join(ckdir,elem)
            if os.path.isdir(fpname):
                localdirs.append(fpname)
        if localdirs:
            res=find_file(fname,localdirs)
            if res:
                return True
    return False            

readme = read_file('README.markdown')

if "posix" not in os.name:
    print "Are you really running a posix compliant OS ?"
    print "Be posix compliant is mandatory"
    sys.exit(1)

library_dirs=[]
include_dirs=[]

#we add, at the begining of the list, the existing environemental variables
if os.environ.has_key('C_INCLUDE_PATH'):
    include_dirs.extend(os.environ['C_INCLUDE_PATH'].split(':'))
if os.environ.has_key('LD_LIBRARY_PATH'):
    library_dirs.extend(os.environ['LD_LIBRARY_PATH'].split(':'))

#anyhow we include the standards directories
library_dirs.extend(['/usr/lib','/usr/local/lib','/opt/local/lib'])
include_dirs.extend(['/usr/include','/usr/local/include','/opt/local/include'])

if find_file('ev.h',include_dirs)==False:
    print "We don't find 'ev.h' which is a mandatory file to compile Fapws"
    print "Please install the sources of libev, or provide the path by setting the shell environmental variable C_INCLUDE_PATH"
    sys.exit(1)
if find_file('Python.h',include_dirs)==False:
    print "We don't find 'Python.h' which is a mandatory file to compile Fapws"
    print "Please install the sources of python, or provide the path by setting the shell environmental variable C_INCLUDE_PATH"
    sys.exit(1)
if find_file('libev.a',library_dirs)==False:
    print "We don't find 'libev.a' which is a mandatory file to run Fapws"
    print "Please install libev, or provide the path by setting the shell environmental variable LD_LIBRARY_PATH"
    sys.exit(1)




setup(name='fapws3',
      version="0.5",
      description="Fast Asynchronous Python Web Server",
      long_description=readme,
classifiers=['Development Status :: 4 - Beta','Environment :: Web Environment','License :: OSI Approved :: GNU General Public License (GPL)','Programming Language :: C','Programming Language :: Python','Topic :: Internet :: WWW/HTTP :: HTTP Servers','Topic :: Internet :: WWW/HTTP :: WSGI :: Server'], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
      keywords='',
      author='William',
      author_email='william.os4y@gmail.com',
      url='http://william-os4y.livejournal.com/',
      license='GPL',
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          # -*- Extra requirements: -*-
      ],
      entry_points="""
      # -*- Entry points: -*-
      """,

      packages= find_packages(),
      ext_modules = [
          Extension('fapws._evwsgi',
                  sources=['fapws/_evwsgi.c'],
                  include_dirs=include_dirs,
                  library_dirs=library_dirs, # add LD_RUN_PATH in your environment
                  libraries=['ev'],
                  #extra_compile_args=["-ggdb"],
                  #define_macros=[("DEBUG", "1")],
                  )
                  ]
      )


# end of file: setup.py
