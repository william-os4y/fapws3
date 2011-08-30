#!/usr/bin/python

import os, signal
try:
	import posh
	use_posh = True
except:
	use_posh = True

import fapws._evwsgi as evwsgi
from fapws import base
import urlparse

class HttpStatus:
	status = {
		# 2xx Success
		200: 'OK',
		201: 'Created',
		202: 'Accepted',
		203: 'Partial Information',
		204: 'No Content',
		# 3xx Redirection
		301: 'Moved',
		302: 'Found',
		303: 'Method',
		304: 'Not Modified',
		# 4xx 5xx Error
		400: 'Bad request',
		401: 'Unauthorized',
		402: 'Payment Required',
		403: 'Forbidden',
		404: 'Not found',
		500: 'Internal Error',
		501: 'Not implemented',
		502: 'Service temporarily overloaded',
		503: 'Gateway timeout',
	}

	def __init__(self, code):
		print '+ HttpStatus %i' % code
		if HttpStatus.status.has_key(code):
			self.code = code
			self.status = '%i %s' % (code, self.status[code])
		else:
			self.code = 500
			self.status = '%i %s' % (self.code, self.status[self.code])

	def __str__(self):
		return self.status

#######################################################
# Message is a free string with some identifiers
#######################################################
class Message:
	def __init__(self, mid, timestamp, content):
		self.mid = mid
		self.timestamp = timestamp
		self.content = content
		print '+ Channel %s' % self

	def __str__(self):
		#[{"version":"1","operation":"INSERT","channelCode":"teste_17082011","reference":"0","payload":"Greetings from Porto Alegre, RS.","realtimeId":"2","dtCreated":"1314721007"},0]
		return self.content

#######################################################
# Client is a single HTTP client. Every client receives
# a single message and is disconnected
#######################################################
class Client:
	def __init__(self, environ, start_response):
		self.environ = environ
		self.start_response = start_response
		print '+ Client %s' % self

#######################################################
# Channel is an aggregator for subscribers and messages
#######################################################
class Channel:
	def __init__(self, name):
		self.last = None
		self.name = name
		self.subs = dict() # Subscribers for this channel
		self.mesgs = dict() # message posted on this channel
		print '+ Channel %s' % self

	def get_message(self, mid=None):
		print 'Channel> get_message %s' % mid
#		try:
		if self.mesgs.has_key(mid):
			print 1
			return self.mesgs[mid]
		elif self.last > mid:
			print self.last > mid
			print 2
			raise HttpStatus(204)
		elif mid == None and self.last:
			print 3
			return self.mesgs[self.last]
		else:
			print 4
			return None
#		except KeyError:
#			return None

	def subscribe(self, client):
		print 'Channel> subscribe %s' % client
		self.subs[len(self.subs)] = client

	def send_message(self, client, message):
		print 'Channel> send_message %s - %s' % (client, message)
		client.start_response('200 OK', [('Content-Type','application/json; charset="ISO-8859-1"')])
		evwsgi.write_response(client.environ, client.start_response, ['[%s,0]' % message])

	def send_error(self, client, http_error):
		print 'Channel> send_error %s - %i' % (client, http_error.code)
		client.start_response(http_error.status, [('Content-Type','text/plain; charset="ISO-8859-1"')])
		evwsgi.write_response(client.environ, client.start_response, [http_error.status])

	def publish(self, message):
		# save for future requests
		self.mesgs[message.mid] = message
		self.last = message.mid
		print 'Channel> publish %s' % message.mid

		# broadcast to subscribers
		for n, client in self.subs.items():
			try:
				self.send_message(client, self.get_message(message.mid))
			except HttpStatus, ex:
				self.send_error(client, ex)

		# unregister subscribers
		total = len(self.subs)
		del self.subs
		self.subs = dict();
		return total

#######################################################
# ChannelPool handles an arbitrary number of Channels
#######################################################
class ChannelPool:
	def __init__(self):
		self.pool = dict()
		print '+ ChannelPool %s' % self

	def create_channel(self, name):
		print 'ChannelPool> create_channel %s' % name
		try:
			return self.pool[name]
		except:
			ch = Channel(name)
			self.pool[name] = ch
			return ch

	def get_channel(self, name):
		print 'ChannelPool> get_channel %s' % name
		try:
			return self.pool[name]
		except:
			return None

cpool = ChannelPool()

#######################################################
# this is our 'main loop", where we handle client
# requests and do our publisher/subscriber logic
#######################################################
def start(no=0, shared=None):

	if shared and use_posh == True:
		print 'child[%i]: %i' % (no, posh.getpid())

	#def on_interrupt(signum, frame):
	#	print 'Child %i received SIGINT. Exiting...' % no
	#	posh.exit(0)
	#signal.signal(signal.SIGINT, on_interrupt)

	# Subscriber handler
	def subscribe(environ, start_response):
		# Req:
		# GET /broadcast/sub/ch=teste_17082011&m=2&s=M HTTP/1.1
		# Res:
		#[{
		#	"version": "1",
		#	"operation":"INSERT",
		#	"channelCode":"teste_17082011",
		#	"reference":"0",
		#	"payload":"Greetings from Porto Alegre, RS.",
		#	"realtimeId":"2",
		#	"dtCreated":"1314721007"
		#}, 0]

		print '######## start subscriber ########'
		try:
			qs = urlparse.parse_qs(environ['QUERY_STRING'])

			# find channel
			_ch = qs['ch'][0]
			ch = cpool.get_channel(_ch)
			if not ch:
				start_response('404 Not Found', [('Content-Type','text/plain')])
				return ['invalid channel %s' % _ch]

			# find message
			_m = int(qs['m'][0])
			mesg = ch.get_message(_m)
			if mesg:
				# got it! send imediatelly
				#ch.send_message(Client(environ, start_response), mesg)
				start_response('200 OK', [('Content-Type','application/json; charset="ISO-8859-1"')])
				return ['[%s,0]' % mesg]
			else:
				# mesg not found, subscribe this client
				ch.subscribe(Client(environ, start_response))
				return True
		except HttpStatus, ex:
			start_response('%s' % ex.status, [('Content-Type','text/plain')])
			return ['invalid parameter: %s' % ex]
		except Exception, ex:
			start_response('400 Bad request', [('Content-Type','text/plain')])
			return ['invalid parameter: %s' % ex]
			

#		print 'python: on_get', client
		
		#if len(queue) % 100 == 0:
		#	print len(queue), 'clients'

		# by returning True we signal write_cb() this is not a ordinary connection.
		# instead, it will store struct client* and 'block' the socket, waiting for
		# an event to unblock and feed it.
		#return True

	# Publisher handler
	def publish(environ, start_response):

		# example message
		#{
		#	'fapws.params': {
		#		'rt_message': ['{"version":"1","operation":"INSERT","channelCode":"ch_teste","reference":"0","payload":"This is Spartaaaaaaa!!!","realtimeId":"1","dtCreated":"1314721709"},']
		#	},
		#	'SERVER_PORT': '8080',
		#	'CONTENT_TYPE': 'application/x-www-form-urlencoded',
		#	'fapws.uri': '/broadcast/pub?ch=ch_teste&m=ch_teste&t=1314721709',
		#	'SERVER_PROTOCOL': 'HTTP/1.1',
		#	'fapws.raw_header': 'POST /broadcast/pub?ch=ch_teste&m=ch_teste&t=1314721709 HTTP/1.1\r\nUser-Agent: curl/7.21.3 (i686-pc-linux-gnu) libcurl/7.21.3 OpenSSL/0.9.8o zlib/1.2.3.4 libidn/1.18\r\nHost: localhost:8080\r\nAccept: */*\r\nContent-Length: 167\r\nContent-Type: application/x-www-form-urlencoded\r\n\r\nrt_message={"version":"1","operation":"INSERT","channelCode":"ch_teste","reference":"0","payload":"This is Spartaaaaaaa!!!","realtimeId":"1","dtCreated":"1314721709"},',
		#	'SCRIPT_NAME': '/broadcast/pub',
		#	'wsgi.input': <cStringIO.StringO object at 0xb7741a60>,
		#	'REQUEST_METHOD': 'POST',
		#	'HTTP_HOST': 'localhost:8080',
		#	'PATH_INFO': '',
		#	'wsgi.multithread': False,
		#	'QUERY_STRING': 'ch=ch_teste&m=ch_teste&t=1314721709',
		#	'HTTP_CONTENT_TYPE': 'application/x-www-form-urlencoded',
		#	'REQUEST_PROTOCOL': 'HTTP/1.1',
		#	'HTTP_ACCEPT': '*/*',
		#	'fapws.remote_port': 52908,
		#	'HTTP_USER_AGENT': 'curl/7.21.3 (i686-pc-linux-gnu) libcurl/7.21.3 OpenSSL/0.9.8o zlib/1.2.3.4 libidn/1.18',
		#	'wsgi.version': (1, 0),
		#	'fapws.major_minor': '1.1',
		#	'SERVER_NAME': '0.0.0.0',
		#	'REMOTE_ADDR': '127.0.0.1',
		#	'wsgi.run_once': False,
		#	'wsgi.errors': <cStringIO.StringO object at 0xb7741a40>,
		#	'wsgi.multiprocess': True,
		#	'wsgi.url_scheme': 'HTTP',
		#	'fapws.remote_addr': '127.0.0.1',
		#	'HTTP_CONTENT_LENGTH': '167',
		#	'CONTENT_LENGTH': 167
		#}

		print '######## start publisher ########'

		if environ['REQUEST_METHOD'] != 'POST':
			start_response('400 Bad request', [('Content-Type','text/plain')])
			return ['invalid method. Expected POST.']

		try:
			qs = urlparse.parse_qs(environ['QUERY_STRING'])
			_ch = qs['ch'][0]
			_m = int(qs['m'][0])
			_t = qs['t'][0]
			_mesg = environ['fapws.params']['rt_message'][0]
			mesg = Message(_m, _t, _mesg)
			ch = cpool.get_channel(_ch)
			if not ch:
				ch = cpool.create_channel(qs['ch'][0])
		except KeyError, ex:
			start_response('400 Bad request', [('Content-Type','text/plain')])
			return ['invalid parameter: %s' % ex]

		# for each subscriber we saved in on_get(), schedule a write.
		ch.publish(mesg)

		# response to publisher
		start_response('200 OK', [('Content-Type','text/plain')])
		return ['queued messages: %i\nlast requested: %i sec. ago (-1=never)\nactive subscribers: %i\n' % (1, -1, len(ch.subs)) ] #TODO

	evwsgi.wsgi_cb(('/broadcast/sub', subscribe))
	evwsgi.wsgi_cb(('/broadcast/pub', publish))

	evwsgi.set_debug(0)
	evwsgi.run()

######################
# ignore this for now
######################
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

#############################
# start WSGI
#############################
def main():
	evwsgi.start('0.0.0.0', '8080')
	evwsgi.set_base_module(base)
	start()

if __name__ == '__main__':
		main()
#	import sys
#	if use_posh == True:
#		print 'install posh module to enable shared objects between child process: http://poshmodule.sourceforge.net/'
#		fork_main()
#	elif len(sys.argv) > 1 and sys.argv[1] == '-f':
#		fork_main()
#	else:
#		main()
