# -*- coding: utf-8 -*-

import time


def application(environ, start_response):
    status = b'404 Not Found'
    output = b'Pong!'

    response_headers = [('Content-type', 'text/plain')]
    #response_headers = [('Content-type', 'text/plain'),
    #                    ('Content-Length', str(len(output)))]

    start_response(status, response_headers)
    # return [output] # <- works OK
    yield output # <- does not convey 404 status to client
    time.sleep(5)
    yield b" and "
    time.sleep(5)
    yield b"Ping!!!"

if __name__=="__main__":
    import fapws._evwsgi as evwsgi
    from fapws import base

    evwsgi.start("0.0.0.0", "8080")
    evwsgi.set_base_module(base)
    evwsgi.wsgi_cb(("/", application))
    evwsgi.set_debug(1)
    evwsgi.run()
