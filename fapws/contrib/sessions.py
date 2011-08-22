#    Copyright (C) 2009 William.os4y@gmail.com
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, version 2 of the License.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
import binascii
import datetime
try:
    import cPickle as pickle
except ImportError:
    import pickle
import os
import time


class Session:
    """
      This class will manage the session's data for you. Will take into account the expiration date, ... 
      Data can be any picklable object. 
      
      This object must be managed by a SessionMgr acting like this:
      class SessionMgr:
          #This sessionMgr is using sessdb with get and save methods.
	  def __init__(self, environ, start_response):
	      #we retreive the Session object from our Storage object
	      self.sessdb=None  
	      self._sessionid=None
	      self.start_response=start_response
	      cook=base.parse_cookies(environ)
	      if cook and cook.get('sessionid', None):
		  self._sessionid=cook['sessionid'].value
		  self.sessdb= ... # you retreive your sessdb dictionary from your Storage object (mysql, sqlite3, ...)
	      if not self.sessdb:
		  self.sessdb=... # your create an empty sessdb dictionary 
	  def get(self, key, default=None):
	      #To get a element of the data dictionary
	      sess=Session(self.sessdb)
	      data=sess.getdata() or {}         #this session manager use dictionary data
	      return data.get(key, default)
	  def set(self, key, value):
	      #to set a key/element in our dictionary
	      sess=Session(self.sessdb)
	      data=sess.getdata() or {}         #this session manager use dictionary data
	      data[key]=value
	      sess.setdata(data)      #This dumps data in our sess object, thus is our sessdb object
	      self.sessdb.save()      #If you sessdb object is a Storage object it should have asave method. 
	  def delete(self, key):
	      #to delete a key from our dictionary
	      sess=sessions.Session(self.sessdb)
	      data=sess.getdata() or {}
	      if data.has_key(key):
		  del data[key]
	      sess.setdata(data)
	      self.sessdb.save()

    """
    def __init__(self, sessiondb, max_age=10 * 86400, datetime_fmt="%Y-%m-%d %H:%M:%S", prepare_data=None):
        """
           sessiondb:   this is in fact a record of your sessionDB. This can be an empty record. 
           max_age:     the session duration. After expiration the associated date will be lost
           datetime_fmt: the time format are we have in the cookies
           prepare_date: method required to treat the data. Can be str, ... 
        """
        self.sessiondb = sessiondb  # must have a get method and return dictionary like object with sessionid, strdata and expiration_date
        self.datetime_fmt = datetime_fmt
        self.max_age = max_age
        self.prepare_data=prepare_data
        #we should always have a sessionid and an expiration date
        if not self.sessiondb.get('sessionid', None):
            self.newid()
        if not self.sessiondb.get('expiration_date', None):
            self.update_expdate()

    def getdata(self):
        "return the python objected associated or None in case of expiration"
        exp = self.sessiondb.get('expiration_date', None)
        if not exp:
            return None
        if type(exp) is datetime.datetime:
            expdate = exp
        elif type(exp) in (str, unicode):
            expdate = datetime.datetime.fromtimestamp(time.mktime(time.strptime(exp, self.datetime_fmt)))
        else:
            raise ValueError("expiration_Date must be a datetime object or a string (%s)" % self.datetime_fmt)
        if expdate < datetime.datetime.now():
            #expired
            return None
        else:
            if self.sessiondb['strdata']:
                strdata = str(self.sessiondb['strdata'])
                data = pickle.loads(strdata)
                return data
            else:
                return None

    def setdata(self, data):
        strdata = pickle.dumps(data)
        if self.prepare_data:
             strdata=self.prepare_data(strdata)
        self.sessiondb['strdata'] = strdata

    def newid(self):
        sessid = binascii.hexlify(os.urandom(12))
        self.sessiondb['sessionid'] = sessid

    def getid(self):
        return self.sessiondb.get('sessionid')

    def update_expdate(self):
        self.sessiondb['expiration_date'] = self._getexpdate()

    def _getexpdate(self):
        now = datetime.datetime.now()
        exp = now + datetime.timedelta(seconds=self.max_age)
        return exp.strftime(self.datetime_fmt)


if __name__ == "__main__":
    DB={}
    s=Session(DB, max_age=2) # we store data for 2 seconds
    s.newid() # we request an ID
    s.setdata({'test':'fapws values'}) # we set some values
    print "Our DB:", s.getdata()
    print "Those values will be stored for 2 seconds"
    print "now we sleep for 3 seconds"
    time.sleep(3)
    print "Our DB:", s.getdata()
    
