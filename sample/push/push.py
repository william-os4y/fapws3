#!/usr/bin/python

import os, signal
try:
	import posh
	noposh = False
except:
	noposh = True

import fapws._evwsgi as evwsgi
from fapws import base

class Client:
	def __init__(self, environ, start_response):
		self.environ = environ
		self.start_response = start_response
#		print '__init__', self

queue = list()

def start(no=0, shared=None):
	if shared and noposh == False:
		print 'child[%i]: %i' % (no, posh.getpid())

	#def on_interrupt(signum, frame):
	#	print 'Child %i received SIGINT. Exiting...' % no
	#	posh.exit(0)
	#signal.signal(signal.SIGINT, on_interrupt)

	def on_get(environ, start_response):
		client = Client(environ, start_response)
#		print 'python: on_get', client
		queue.append(client)
		if len(queue) % 100 == 0:
			print len(queue), 'clients'
		# by returning True we signal write_cb() this is not a ordinary connection.
		# instead, it will store struct client* and 'block' the socket, wayting for
		# an event to unblock and feed it.
		return True

	def on_post(environ, start_response):
		message = 'Hello from %s:%s!\n' % (environ['fapws.remote_addr'], environ['fapws.remote_port'])
#		print 'python: queue=%i' % len(queue)
		# for each client we saved in on_get(), we schedule a write with anything
		# we want to send them.
		for client in globals()['queue']:
#			print 'python: on_post', client
			client.start_response('200 OK', [('Content-Type','text/plain')])
			evwsgi.write_response(client.environ, client.start_response, [message])
#			print 'python: on_post', client, 'end'
#			queue.remove(client)
		start_response('200 OK', [('Content-Type','text/html')])
#		print 'python: on_post end'
		del globals()['queue']
		globals()['queue'] = list()
		return ['<hello>\n']

	evwsgi.wsgi_cb(('/get', on_get))
	evwsgi.wsgi_cb(('/post', on_post))

	evwsgi.set_debug(0)
	evwsgi.run()

def fork_main(child_no=1):
	print 'parent:', os.getpid()

	def create_shared():
		return {'name': 'realtime'}

	channels = create_shared()
	posh.share(channels)

	evwsgi.start('0.0.0.0', '8080')
	evwsgi.set_base_module(base)

	child = list()
	for i in range(child_no):
		child.append(posh.forkcall(start, i, channels))

	def on_interrupt(signum, frame):
		print 'terminating %i children' % len(child)
		for pid in child:
			print 'kill(%i)' % pid
			os.kill(pid, signal.SIGINT)
	signal.signal(signal.SIGINT, on_interrupt)

	print 'forked %i childs' % len(child)
	posh.waitall()

def main():
	evwsgi.start('0.0.0.0', '8080')
	evwsgi.set_base_module(base)
	start()

if __name__ == '__main__':
	import sys
	if noposh:
		print 'install posh module to enable shared objects between child process: http://poshmodule.sourceforge.net/'
		fork_main()
	elif len(sys.argv) > 1 and sys.argv[1] == '-f':
		fork_main()
	else:
		main()
