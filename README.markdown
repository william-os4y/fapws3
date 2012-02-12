Fast Asynchronous Python Web Server (Fapws in short)
====================================================

This is a python web server using the wonderfull [libev](http://software.schmorp.de/pkg/libev.html) library. Thus this is yet an another asynchronous web server like Medusa, Twisted, Apricot.
And Fapws is WSGI compliant.

A bit history of Fapws3 
------------------------
Fapws1, Fapws2 and Fapws3 are "internal" project's name. The rename correspond to a full re-write. 

In the begining I made Fapws1, a Python extension based on the Apricot code. Then, quickly comes the need to have much more features in it, and I've called it Fapws2. Fapws1 has never been publically published.
Fapws2 is rebuild based on the http library of libevent. Works great, but I've been forced to modify the evhttp_handle_request of libevent. Despite several mails to the libevent mailing list, no one was agreed to accept my patch. Thus, this is was a bit complicated to use. 
At a moment, Marc Lehmann posts, in the libevent mailinglist, a mail describing the creation of a "new" and optimized event's library similar to libevent: libev. Because the code was much more clean (personnal point of view) and because the [documentation provided](http://cvs.schmorp.de/libev/ev.pod) was very clear, I've decided to give it a try. Thus, in December 2008, came Fapws3; a full re-write of Fapws2, but based on libev.  

Support for Fapws2 will be strictly limited to bug fixing. My current work will be focused on Fapws3. 


Why a new python web server ?
-----------------------------
In that case, the usual question is why an new one ? In short, the answer is because it sounds that Apricot is not more maintained, and because Medusa and Twisted can not go as fast as Apricot. Indeed, after several pure performance tests it appears that, thanks to a library like libevent or libev the webserver build on top of it is really fast.

But that's not the only reason. Personnally, I prefer event's web server. Indeed, such architecture gives more performant web server and with a much more limited memory foot print. You can easly install them into a memory limited machines (like VDS for example).

Philosophy:
-----------
Fapws must stay the most simple web server and the fastest. Thus the core of the application is quite limited. Every contributions will be placed inside a "contrib" sub-directory. If disk space is so important for you, you can easily remove this contrib sub-directory. 
Moreover, I will not implement in Fapws what other application can do. Thus for eample, proxying, load balancing, SSL will not be implemented. Tools like [pound](http://www.apsis.ch/pound/) do that very well.

How to install Fapws:
---------------------
Please read the INSTALL document provided. 

How to use Fapws ?
------------------
Using Fapws is quite simple and must be done in 4 major steps:

1. You define the main parameters of your webserve with the method "start" and the method "base". Unless you really know what you 
   are doing, I strongly suggest to use the "base" module provided within the package.
2. You define your WSGI python callbacks. 
3. You link the URL path with the python callbacks previously created. 
4. You start you webserver by triggering the "run" method. 
5. As describbed in the Libev documentation, you can controle the Event Loop used. By default Libev estimate what's the best one 
   for your architecture, but you can overwrite this selection by using the environment variable: LIBEV_FLAGS.

Choices are: 1=select, 2=poll (everywhere except windows), 4=epoll (Linux), 8=kqueue (BSD clones), 16=devpoll (solaris 8), 32=port (solaris 10)

For you help, check the samples.

How to got news about Fapws ?
-----------------------------
You will find information concerning Fapws on [my own blog](http://william-os4y.livejournal.com/)    
You can also join us in the [Fapws mailing list](http://groups.google.com/group/fapws) (because of spams, registration is required).      
And since 2010 you have the [Fapws website](http://www.fapws.org/)      

Where it can run ?
------------------
Theoritically anywhere where both Python (2.6 or above) and Libev are running.   

It has been reported as running fine on: Freebsd, OpenBSD, NetBsd, Debian (and ubuntu), Gentoo, Archlinux, Fedora.

But note that it will not run on 64bit machines using python 2.4 or lower. 
And it has not yet been ported to python 3.x

Contribution
-------------
People interested to contribute to the development of Fapws3 can contact me on william _dot_ os4y -at- gmail.com


The following people sent in patches or made other noteworthy
contributions.

If I forgot to include you, please shout at me, (it was an accident): 

jerzyk : https://github.com/william-os4y/fapws3/pull/17

shigin : https://github.com/william-os4y/fapws3/pull/19

shigin : https://github.com/william-os4y/fapws3/pull/21

Aleksey : did extra tests on python 2.4 and python 2.5

Liu Qishuai : Code improvement

Stiletto : implementation of tuple

Keith : Implementation of sockets

License
-------

    Copyright (C) 2009 William.os4y@gmail.com

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, version 2 of the License.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.



Have fun with Fapws3. 

William
