# -*- coding: utf-8 -*-


import string

#TODO: manage multiple values in isvalid

def makeid(name):
    """
    >>> t=u"this is oéké\t"
    >>> makeid(t)
    'thisisok'
    >>> 
    """
    #turn it to a real string
    res=name.encode('ascii','ignore')
    #remove all unneeded char
    res=res.translate(None, string.punctuation+' \t\n\r')
    return res

class Widget(object):
    """This is the metaclass from which all from's element will come from
    self.label is the label of the associate html's  input (must be unicode)
    If self.required is True the label's class with receive "required".
    self.default contains the default value of your html input
    Other parameters can be provided and will be added to the input's form (class, must be written class_)
    You can provide additonal label's parameter by extending the dictionary label_attr
    """
    def __init__(self, label, required=False, default="", **kw):
        self.base=""
        self.list_attrs=""
        self.params=kw
        self.label=unicode(label)
        self.required=required
        self.default=default
        self.label_attr={'class':"table"}
    def getlabel(self, name):
        """Generate the label in html
        """
        if not self.label:
            return u""
        lid=makeid(name)
        if self.required and "required" not in self.label_attr.get('class',''):
            self.label_attr['class']+=" required"
        attrs=""
        for key,val in self.label_attr.items():
            attrs+='%s="%s" ' % (key, val)
        return u"""<label for="%s" %s>%s</label>""" % (lid, attrs, self.label)
    def _manage_class(self):
        if self.params.has_key("class_"):
            self.params["class"]=self.params["class_"]
            del self.params["class_"]

    def render(self, name, value):
        """This is the main method of this object, and will generated the whole html (lable and input element). 
        This method receiv 2 parameters: the input's name and input's value
        """
        #the 2 following lines must aways be present
        self._manage_class()
        parameters=" ".join(['%s="%s"' % (k,v) for k,v in self.params.items()])
        res=self.getlabel(name)
        if not value:
            value=self.default
        res+="""<%s name="%s" value="%s" %s/>""" % (self.base, name, unicode(value), parameters)
        return res
    def isrequired(self, value):
        """Intern method to return an error message in case the value is not provided"""
        res=[]
        if self.required and value in [None, ""]:
            res.append("Value cannot be empty")
        return res
    def isvalid(self, value):
        """Method that the forms.validate will call to assure the data provided are correct"""
        #the following line must always be present
        return self.isrequired(value)
    

class Text(Widget):
    """
    >>> t=Text("label")
    >>> t.render("name","val")
    u'<label for="name" class="table" >label</label><input name="name" value="val" type="text"/>'
    >>> t.isvalid("value")
    []
    >>> 
    >>> t=Text(u"label", required=True, id="text", class_="input")
    >>> t.render("name","val")
    u'<label for="name" class="table required" >label</label><input name="name" value="val" type="text" id="text" class="input"/>'
    >>> t.isvalid("value")
    []
    >>> t.isvalid("")
    ['Value cannot be empty']
    >>> 
    >>> t=Text("label")
    >>> t.label_attr['id']='input'
    >>> t.render("name","val")
    u'<label for="name" class="table" id="input" >label</label><input name="name" value="val" type="text"/>'
    >>> 
    >>> t=Text("label", default="why not")
    >>> t.render("name","value")
    u'<label for="name" class="table" >label</label><input name="name" value="value" type="text"/>'
    >>> t.render("name","")
    u'<label for="name" class="table" >label</label><input name="name" value="why not" type="text"/>'
    >>> 

    """
    def __init__(self, *lw, **kw):
        super(Text, self).__init__(*lw, **kw)
        self.params['type']='text'
        self.base="input"

class ReadonlyText(Text):
    """
    >>> r=ReadonlyText("label")
    >>> r.render("name","value")
    u'<label for="name" class="table" >label</label><input name="name" value="value" readonly="1" type="text"/>'
    >>> 
    """
    def __init__(self, *lw, **kw):
        super(ReadonlyText, self).__init__(*lw, **kw)
        self.params['readonly']="1"

class Hidden(Widget):
    """
    >>> h=Hidden("")
    >>> h.render("name","value")
    u'<input name="name" value="value" type="hidden"/>'
    >>> 
    """
    def __init__(self, *lw, **kw):
        super(Hidden, self).__init__(*lw, **kw)
        self.params['type']='hidden'
        self.base="input"
    
class Integer(Widget):
    """
    >>> i=Integer("label")
    >>> i.render("name","value")
    u'<label for="name" class="table" >label</label><input name="name" value="value" type="text" size="5"/>'
    >>> i.isvalid("value")
    ['Value is not an integer']
    >>> i.isvalid(12)
    []
    """
    def __init__(self, *lw, **kw):
        super(Integer, self).__init__(*lw, **kw)
        self.params['type']='text'
        self.params['size']=5
        self.base="input"
        self.list_attrs='class="nowrap"'
    def isvalid(self, value):
        res=super(Integer, self).isvalid(value)
        if not self.required and not value:
            return []
        try:
            val=int(value)
        except:
            res.append("Value is not an integer")
        return res

class Area(Widget):
    """
    >>> a=Area("label", cols="100")
    >>> a.render("name","value")
    u'<label for="name" class="bellow" >label</label><textarea name="name" rows="10" cols="100">value</textarea>'
    >>> a.isvalid("value")
    []
    """
    def __init__(self, *lw, **kw):
        super(Area, self).__init__(*lw, **kw)
        if not kw.has_key('cols'):
            self.params['cols']=40
        if not kw.has_key('rows'):
            self.params['rows']=10
        self.base="textarea"
        self.label_attr['class']='bellow'
    def render(self, name, content):
        self._manage_class()
        parameters=" ".join(['%s="%s"' % (k,v) for k,v in self.params.items()])
        res=self.getlabel(name)
        if not content:
            content=self.default
        res+= """<%(base)s name="%(name)s" %(args)s>%(content)s</%(base)s>""" % {'name':name, 'base': self.base, 'args': parameters, 'content':content}
        return res
        

class Check(Widget):
    """
    >>> c=Check("label", required=True)
    >>> c.render("name","value")
    u'<label for="name" class="table required" >label</label><input name="name" value="1" checked="checked" type="checkbox"/>'
    >>> c.render("name","")
    u'<label for="name" class="table required" >label</label><input name="name" value="1" type="checkbox"/>'
    >>> c.isvalid("")
    []
    >>> c=Check("label", default="1")
    >>> c.render("name","value")
    u'<label for="name" class="table" >label</label><input name="name" value="1" checked="checked" type="checkbox"/>'
    >>> c.render("name","")
    u'<label for="name" class="table" >label</label><input name="name" value="1" checked="checked" type="checkbox"/>'
    >>> 
    """
    def __init__(self, *lw, **kw):
        super(Check, self).__init__(*lw, **kw)
        self.params['type']='checkbox'
        self.base="input"
    
    def render(self, name, value):
        self._manage_class()
        if self.default or value:
            self.params['checked']="checked"
        else:
            if self.params.has_key('checked'):
                del self.params['checked']
        parameters=" ".join(['%s="%s"' % (k,v) for k,v in self.params.items()])
        res=self.getlabel(name)
        res+="""<%s name="%s" value="1" %s/>""" % (self.base, name, parameters)
        return res
    def isvalid(self, value):
        #in this case no need to verify the isrequired
        return []

class Boolean(Check):
    """
    >>> b=Boolean("label")
    >>> b.render("name","value")
    u'<label for="name" class="table" >label</label><input name="name" value="1" checked="checked" type="checkbox"/>'
    >>> 
    """
    pass

class Password(Text):
    """
    >>> p=Password("label")
    >>> p.render("name","value")
    u'<label for="name" class="table" >label</label><input name="name" value="value" type="password"/>'
    >>> p.isvalid("value")
    []
    >>> p.isvalid("")
    []
    >>> 
    """
    def __init__(self, *lw, **kw):
        super(Password, self).__init__(*lw, **kw)
        self.params['type']='password'


class Dropdown(Widget):
    """
    >>> d=Dropdown("label")
    >>> d.options=[("-1","-----"),("1","value")]
    >>> len(d.render("name","1"))
    164
    >>> len(d.render("name",""))
    144
    >>> d.isvalid("1")
    []
    >>> d=Dropdown("label", required=True)
    >>> d.options=[("-1","-----"),("1","value")]
    >>> d.isvalid("1")
    []
    >>> d.isvalid("2")
    ['Value not in the list']
    >>> d.isvalid("-1")
    ['Not a valid value']
    >>> 
    """
    def __init__(self, *lw, **kw):
        super(Dropdown, self).__init__(*lw, **kw)
        self.base='select'
    
    def render(self, name, value_selected):
        self._manage_class()
        res=self.getlabel(name)
        parameters=" ".join(['%s="%s"' % (k,v) for k,v in self.params.items()])
        res+='<%s name="%s" %s>\n' % (self.base, name, parameters) 
        if not value_selected:
            value_selected=self.default
        for oval, oname in self.options:
            if unicode(oval) == unicode(value_selected):
                res+='<option value="%s" selected="selected">%s</option>\n' % (oval,oname)
            else:
                res+='<option value="%s">%s</option>\n' % (oval,oname)
        res+="</select>"
        return res
    def isvalid(self, value):
        res=super(Dropdown, self).isvalid(unicode(value))
        if self.required:        
            if unicode(value) not in [unicode(k) for k,e in self.options]:
                res.append("Value not in the list")
            if unicode(value)=="-1":
                res.append("Not a valid value")
        return res

class Foreignkey(Dropdown):
    """
    >>> f=Foreignkey("label")
    >>> f.options=[("-1","-----"),("1","value")]
    >>> len(f.render("name","1"))
    164
    >>> len(f.render("name",""))
    144
    >>> f.url_other_table="/admin/tablea/add"
    >>> len(f.render("name","1"))
    346
    >>> 
    """
    def __init__(self, *lw, **kw):
        super(Foreignkey, self).__init__(*lw, **kw)
        self.url_other_table=""
    def render(self, name, value):
        res=super(Foreignkey,self).render(name, value)
        if self.url_other_table:
            res+="""<a href="#" onClick="window.open('%s?_open=popup','mywindow','width=900,height=600,scrollbars=yes,resizable=yes')"> <img src="/static/images/add.png" height="12"/></a>""" % self.url_other_table
        return res

    

class Date(Widget):
    """
    >>> d=Date("label")
    >>> d.render("name","2011-01-01")
    u'<label for="name" class="table" >label</label><input name="name" value="2011-01-01" type="text"/>'
    >>> d.isvalid("2011-01-01")
    []
    >>> d.isvalid("2011-011-01")
    ['Date must have the format yyyy-mm-dd']
    >>> 
    """
    def __init__(self, *lw, **kw):
        super(Date, self).__init__(*lw, **kw)
        self.params['type']='text'
        self.base="input"
    def isvalid(self, value):
        res=super(Date, self).isvalid(value)
        if (self.required and value) or value:
            if (len(value)!= 10) or (value[4]!="-" and value[7]!="-"):
                res.append("Date must have the format yyyy-mm-dd")
        return res

class DateTime(Widget):
    """
    >>> dt=DateTime("label")
    >>> dt.render("name","2011-01-01 10:10:10")
    u'<label for="name" class="table" >label</label><input name="name" value="2011-01-01 10:10:10" type="text"/>'
    >>> dt.isvalid("2011-01-01 10:10:10")
    []
    >>> dt.isvalid("2011-01-01 10:10")
    ['Date must have the format yyyy-mm-dd HH:MM:SS']
    >>> 

    """
    def __init__(self, *lw, **kw):
        super(DateTime, self).__init__(*lw, **kw)
        self.params['type']='text'
        self.base="input"
    def isvalid(self, value):
        res=super(DateTime, self).isvalid(value)
        if (self.required and value) or value:
            if (len(value)!= 19) or (value[4]!="-" and value[7]!="-" and value[13]!=":" and value[16]!=":"):
                res.append("Date must have the format yyyy-mm-dd HH:MM:SS")
        return res

class File(Widget):
    """
    >>> f=File("label")
    >>> f.render("name","")
    u'<label for="name" class="table" >label</label><input name="name" value="" type="file"/>'
    >>> f.render("name","value")
    u'<label for="name" class="table" >label</label><input name="name" value="value" type="file"/>'
    >>> 
    """
    def __init__(self, *lw, **kw):
        super(File, self).__init__(*lw, **kw)
        self.params['type']='file'
        self.base="input"


class jFile(File):
    """
    >>> f=jFile("label")
    >>> f.render("name","value")
    u'<label for="name" class="table" >label</label><input name="name" value="value" type="text"/><a id="em"><img src="/static/images/add.png" height="15"/></a> '
    >>> 
    This is a File object to use with jquery fileupload
    """
    def __init__(self, *lw, **kw):
        super(jFile, self).__init__(*lw, **kw)
        self.params['type']='text'
        self.base="input"
    def render(self, name, value):
        #the 2 following lines must aways be present
        self._manage_class()
        parameters=" ".join(['%s="%s"' % (k,v) for k,v in self.params.items()])
        res=self.getlabel(name)
        if not value:
            value=self.default
        res+="""<%s name="%s" value="%s" %s/><a id="em"><img src="/static/images/add.png" height="15"/></a> """ % (self.base, name, unicode(value), parameters)
        return res





if __name__=="__main__":
    import doctest
    doctest.testmod()
