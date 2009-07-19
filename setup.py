from setuptools import setup, find_packages, Extension
import os
import sys

def read_file(name):
    return open(os.path.join(os.path.dirname(__file__),name)).read()

readme = read_file('README')

setup(name='fapws3',
      version="0.3",
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
                  #include_dirs=["/usr/include"],
                  #library_dirs=["/usr/local/lib"], # add LD_RUN_PATH in your environment
                  libraries=['ev'],
                  #extra_compile_args=["-ggdb"],
                  #define_macros=[("DEBUG", "1")],
                  )
                  ]
      )


# end of file: setup.py
