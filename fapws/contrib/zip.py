try:
    import cStringIO as StringIO
except:
    import StringIO
import gzip

class Gzip:
    #wsgi gzip middelware
    def __call__(self, f):
        def func(environ, start_response):
            content=f(environ, start_response)
            if 'gzip' in environ.get('HTTP_ACCEPT_ENCODING', ''):
                if type(content)==type([]):
                    content="".join(content)
                else:
                    #this is a stream
                    content=content.read()
                sio = StringIO.StringIO()
                comp_file = gzip.GzipFile(mode='wb', compresslevel=6, fileobj=sio)
                comp_file.write(content)
                comp_file.close()
                start_response.add_header('Content-Encoding', 'gzip')
                res=sio.getvalue()
                start_response.add_header('Content-Length', len(res))
                return [res]
            else:
                return content
        return func
