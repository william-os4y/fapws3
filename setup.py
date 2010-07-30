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
        #we don't find it, it can be located into a subdirectory ;-)
        localdirs=[]
        try:
            elems=os.listdir(ckdir)
        except:
            elems=[]
        for elem in elems:
            fpname=os.path.join(ckdir,elem)
            if os.path.isdir(fpname):
                localdirs.append(fpname)
            if elem[:len(fname)]==fname:
                founded=True
                break
        if founded:
            print "----------Find",fname," in ", ckdir
            return ckdir
        if localdirs:
            res=find_file(fname,localdirs)
            if res:
                return res
    return False            

readme = read_file('README.markdown')

if "posix" not in os.name:
    print "Are you really running a posix compliant OS ?"
    print "Be posix compliant is mandatory"
    sys.exit(1)

search_library_dirs=[]
search_include_dirs=[]
library_dirs=[]
include_dirs=[]


#we add, at the begining of the list, the existing environemental variables
if os.environ.has_key('C_INCLUDE_PATH'):
    search_include_dirs.extend(os.environ['C_INCLUDE_PATH'].split(':'))
if os.environ.has_key('LD_LIBRARY_PATH'):
    search_library_dirs.extend(os.environ['LD_LIBRARY_PATH'].split(':'))

#anyhow we include the standards directories
search_library_dirs.extend(['/usr/lib','/usr/local/lib','/opt/local/lib','/usr/lib64'])
search_include_dirs.extend(['/usr/include','/usr/local/include','/opt/local/include'])


res=find_file('ev.h',search_include_dirs)
if res==False:
    print "We don't find 'ev.h' which is a mandatory file to compile Fapws"
    print "Please install the sources of libev, or provide the path by setting the shell environmental variable C_INCLUDE_PATH"
    sys.exit(1)
include_dirs.append(res)
res=find_file('Python.h',search_include_dirs)
if res==False:
    print "We don't find 'Python.h' which is a mandatory file to compile Fapws"
    print "Please install the sources of python, or provide the path by setting the shell environmental variable C_INCLUDE_PATH"
    sys.exit(1)
include_dirs.append(res)
res=find_file('libev.so',search_library_dirs)
if res==False:
    print "We don't find 'libev.so' which is a mandatory file to run Fapws"
    print "Please install libev, or provide the path by setting the shell environmental variable LD_LIBRARY_PATH"
    sys.exit(1)
library_dirs.append(res)



setup(name='fapws3',
      version="0.7",
      description="Fast Asynchronous Python Web Server",
      long_description=readme,
classifiers=['Development Status :: 4 - Beta','Environment :: Web Environment','License :: OSI Approved :: GNU General Public License (GPL)','Programming Language :: C','Programming Language :: Python','Topic :: Internet :: WWW/HTTP :: HTTP Servers','Topic :: Internet :: WWW/HTTP :: WSGI :: Server'], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
      keywords='',
      author='William',
      author_email='william.os4y@gmail.com',
      url='http://www.fapws.org',
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
