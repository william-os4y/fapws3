import config
import fapws._evwsgi as wsgi
version = "%s with libev-%s" % (config.SERVER_IDENT, "%s.%s" % wsgi.libev_version())
