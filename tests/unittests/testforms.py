from fapws.contrib.siforms import widgets, forms 

class myform(forms.Form):
    __metaclass__ = forms.FormFactory
    name = widgets.Text("First name", required=True)
    personid = widgets.Integer("Person ID", required=True)
    personcode = widgets.Dropdown("Person's code")
    _add_html_form=['name', 'personid', 'personcode']
    _edit_html_form=['name', 'personid', 'personcode']
    _html_list=['name','personid', 'personcode']



m=myform(id="test", class_="test")
m.personcode.options=[(0,"-----"),(1,"master"),(2,"intermediate")]
print m.render_form(m._add_html_form)
print "="*15
m.validate({'personcode':1,'personid':4,'name':'rrr'},m._add_html_form)
print m.render_form(m._add_html_form)


import doctest 
print doctest.testmod(widgets, verbose=True)







    
            
        
         
