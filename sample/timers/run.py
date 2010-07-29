# -*- coding: utf-8 -*-
#You have to install mako
from mako.lookup import TemplateLookup
import fapws._evwsgi as evwsgi
from fapws import base
#you have to install one of my other code: simple sqlite data mapper
from ssdm import ssdm

i=0

lookup = TemplateLookup(directories=['templates',], filesystem_checks=True, module_directory='./modules')
#Thanks to assure the database will first be created (create.py)
con=ssdm.connect('database.db')
db=ssdm.scan_db(con)

evwsgi.start("0.0.0.0", "8080")
evwsgi.set_base_module(base)
    
def names(environ, start_response):
    start_response('200 OK', [('Content-Type','text/html')])
    name=environ['PATH_INFO']
    rec=db.names.select("page='%s'" % name)
    template=lookup.get_template('names.html')
    if rec:
        rec=rec[0]
        ndisp=rec.display+1
        rec.set({'display':ndisp})
        rec.save()
        #uncomment the following to force a commit for each request
        #db.names.commit()
        return [template.render(**{"name":rec.name,"text":rec.text,"display":ndisp})]
    else:
        return["Name not found"]

def commit():
    con.commit()
    print "commit"

    
#he following trigger a commit every 2 seconds    
evwsgi.add_timer(2,commit)
evwsgi.wsgi_cb(("/names/", names))
evwsgi.set_debug(0)    
evwsgi.run()
  
con.close()
