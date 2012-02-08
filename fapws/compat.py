# -*- coding: utf-8 -*-

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

import sys
def convert_to_bytes(data):
    if type(data)==bytes:   
        return data
    if type(data)==str:
        if sys.version_info[0] > 2:
            return bytes(data,'utf8')
        else:
            return data
    else:
        conv = str(data)
        if sys.version_info[0] > 2:
            return bytes(conv,'utf8')
        else:
            return conv

