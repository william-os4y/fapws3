#!/usr/bin/python

import os, signal
import posh
import fapws._evwsgi as evwsgi
from fapws import base

class Client:
	def __init__(self, environ, start_response):
		self.environ = environ
		self.start_response = start_response

queue = list()

def start(no, shared):
	print 'child[%i]: %i' % (no, posh.getpid())

	def on_interrupt(signum, frame):
		print 'Child %i received SIGINT. Exiting...' % no
		posh.exit(0)
	signal.signal(signal.SIGINT, on_interrupt)

	def on_get(environ, start_response):
		print 'new client'
		queue.append(Client(environ, start_response))
		return True

	def on_post(environ, start_response):
		print 'got message'
		message = 'xalala' #environ['XXX']
		for client in queue:
			client.start_response('200 OK', [('Content-Type','text/plain')])
			evwsgi.write_response(client.environ, client.start_response, [ message ])
		start_response('200 OK', [('Content-Type','text/html')])
		return ['<hello>']

	evwsgi.wsgi_cb(('/get', on_get))
	evwsgi.wsgi_cb(('/post', on_post))

	evwsgi.set_debug(0)
	evwsgi.run()

def create_shared():
	return {'name': 'realtime'}

def main(child_no=1):
	print 'parent:', os.getpid()

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

if __name__ == '__main__':
	main()
