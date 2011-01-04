# -*- coding: utf-8 -*-
        
class FormFactory(type):
    """This is the factory required to gather every Form components"""
    def __init__(cls, name, bases, dct):
        cls.datas={}
        for k,v in dct.items():
            if k[0]!="_":
                cls.datas[k]=v
        return type.__init__(cls, name, bases, dct)
        
        
class Form(object):
    def __init__(self, action="", method="post", **kw):
        """You have to provide the form's action, the form's method and some additional parameters.
           You can put any type of form's parameter expect "class" which must be written "class_"
        """
        self.errors={}
        self.values={}
        self.action=action
        self.method=method
        self.parameters=""
        for k,v in kw.items():
            if k=="class_":
                self.parameters+=' class="%s"' % (v)
            else:
                self.parameters+=' %s="%s"' % (k, v)
        self.submit_text=""
    def submit(self, buttons):
        """Generate self.submit_text
        parameters must be a list of (value, name, params).
        params is here a string
        
        sample:
          <fieldset class="submit">
            <input type="submit" value="send" name="bt1"/>
            <input type="submit" value="cancel" name="bt1"/>
          <fieldset>
        """
        res='<fieldset class="submit">'
        for value, name, params in buttons:
            res+='<input type="submit" value="%s" name="%s" %s/>' % (value, name, params)
        res+="</fieldset>"
        self.submit_text=res
    def render_error(self, name):
        """generate a list of error messages.
        
        sample:
         <ul class="errorlist">
           <li><rong value</li>
         </ul>
        """
        err="""<ul class="errorlist">"""
        for error in self.errors[name]:
            err+="<li>%s</li>" % error
        err+="</ul>"
        return "<div>%s</div>" % err
    def render_form(self, form_fields):
        """Generate the html's form with all fields provided and the self.submit_text previously generated. 
        This is the main method to generate the form. 
        Parameter is a list of field's names you want to see in the form. 
        """
        res='<form action="%s" method="%s" %s>\n' % (self.action, self.method, self.parameters)
        res+="<fieldset>\n<ol>\n"
        for name in form_fields:
            obj=self.datas[name]
            if self.errors.has_key(name):
                res+= '<li class="error">'
                errormsg=self.render_error(name)+"\n"
            else:
                res+= "<li>"
                errormsg=None
            value=self.values.get(name, "")
            res+= obj.render(name, value)
            if errormsg:
                res+=errormsg
            res+= "</li>\n"
        res+="</ol>\n</fieldset>\n"
        res+=self.submit_text
        res+="</form>\n"
        return res
    def validate(self, input_values, form_fields):
        """Validate the data provided in the 1st parameter (a dictionary) agains the fields provided in the 2nd parameter (a list).
        and store the values in self.values
        
        This is an important medthod that allow you to generate self.values. 
        
        self.values is the actual result of the form. 
        """
        self.errors={}
        for name in form_fields:
            obj=self.datas[name]
            if input_values.has_key(name):
                data=input_values[name]
            else:
                data=""
            err=obj.isvalid(data)
            if err:
                self.errors[name]=err
            else:
                self.values[name]=data
    def render_list(self, records):
        """Generate a table with a list of possible values associated with this form.
        1st parameter must be a list of dictionary.
        
        The first column of the generated table will receive the hyperlink: /admin/edit/<table name>/<record id> to the real form
        """
        res="""<table class="tablesorter">\n<thead>\n<tr>"""
        for name in self._html_list:
            res+="<th>%s</th>" % name
        res+="</tr>\n</thead>\n<tbody>"
        i=1
        for data in records:
            if i%2==0:
                class_="odd"
            else:
                class_="even"
            res+='<tr class="%s">' % class_
            j=1
            for name in self._html_list:
                obj=self.datas[name]
                if j==1:
                    pk_path=[]
                    for key in self._dbkey:
                        pk_path.append(unicode(data[key]))
                    res+="""<td %s><a href="/admin/edit/%s/%s">%s</a></td>""" % (obj.list_attrs,self.__class__.__name__, "/".join(pk_path),unicode(data[name] or ""))
                else:
                    res+="<td %s>%s</td>" % (obj.list_attrs, unicode(data[name] or ""))
                j+=1
            res+="</tr>\n"
            i+=1
        res+="\n</tbody>\n</table>"
        return res
