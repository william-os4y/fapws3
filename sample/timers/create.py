# -*- coding: utf-8 -*-
import sqlite3

con=sqlite3.connect('database.db')
c=con.cursor()
c.execute("""create table names(
          page text primary key,
          text text,
          display int)""")

temp_text="""Lorem ipsum dolor sit amet, consectetur adipiscing elit. Etiam sed ipsum purus, a tincidunt elit. Fusce id lectus et elit varius suscipit. Duis accumsan varius orci ac auctor. Quisque at feugiat mauris. Vestibulum velit lectus, lacinia ac cursus id, volutpat id justo. Quisque varius mauris eu mauris tempus venenatis. Vivamus pretium lacinia pretium. Praesent sed elit tortor. Phasellus eu turpis in metus commodo dapibus volutpat quis metus. Nulla egestas aliquam commodo. Etiam dictum consequat pharetra. Phasellus molestie pellentesque velit, in pretium velit interdum nec. Quisque egestas ipsum in nisi hendrerit dapibus. Vivamus aliquam enim ut diam laoreet sit amet tristique neque viverra. Cras felis dolor, tempor a tristique ac, lacinia ut neque."""

for i in range(1000):
   name="page%s" %i
   c.execute("insert into names values (?,?,?)", (name, temp_text,0))

con.commit()
con.close()
