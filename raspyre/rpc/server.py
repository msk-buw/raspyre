from .process import MeasureProcess
import raspyre.sensorbuilder
from SimpleXMLRPCServer import SimpleXMLRPCServer
from SimpleXMLRPCServer import SimpleXMLRPCRequestHandler
from SimpleHTTPServer import SimpleHTTPRequestHandler

import xmlrpclib
import datetime
import sys
import os
import logging
import logging.config
import subprocess


class VerboseFaultXMLRPCServer(SimpleXMLRPCServer):
    def _marshaled_dispatch(self, data, dispatch_method=None, path=None):
        try:
            params, method = xmlrpclib.loads(data)

            # generate response
            if dispatch_method is not None:
                response = dispatch_method(method, params)
            else:
                response = self._dispatch(method, params)
            # wrap response in a singleton tuple
            response = (response, )
            response = xmlrpclib.dumps(
                response,
                methodresponse=1,
                allow_none=self.allow_none,
                encoding=self.encoding)
        except:
            # report low level exception back to server
            # (each dispatcher should have handled their own exceptions)
            exc_type, exc_value, tb = sys.exc_info()
            # while tb.tb_next is not None:
            #    tb = tb.tb_next  # find last frame of the traceback
            # lineno = tb.tb_lineno
            # code = tb.tb_frame.f_code
            # filename = code.co_filename
            # name = code.co_name
            # response = xmlrpclib.dumps(
            #     xmlrpclib.Fault(1, "%s:%s FILENAME: %s LINE: %s NAME: %s" % (
            #         exc_type, exc_value, filename, lineno, name)),
            #     encoding=self.encoding, allow_none=self.allow_none)
            response = xmlrpclib.dumps(
                xmlrpclib.Fault(1, "%s:%s" % (exc_type, exc_value)),
                encoding=self.encoding,
                allow_none=self.allow_none)

            logger = logging.getLogger(__name__)
            logger.error(
                "Dispatch exception", exc_info=(exc_type, exc_value, tb))
        return response


class RequestHandler(SimpleXMLRPCRequestHandler, SimpleHTTPRequestHandler):
    rpc_paths = ('/RPC2', '/')
    __version__ = "0.4"
    server_version = "RaspyreRPC/" + __version__

    def do_GET(self):
        f = self.send_head()
        if f:
            self.copyfile(f, self.wfile)
            f.close()

    def send_head(self):
        path = self.translate_path(self.path)

        f = None
        if os.path.isdir(path):
            self.send_response(400, "Directory listing not allowed")
            return None
        ctype = self.guess_type(path)
        try:
            f = open(path, 'rb')
        except IOError:
            self.send_response(404)
            return None
        self.send_response(200)
        self.send_header("Content-type", ctype)
        fs = os.fstat(f.fileno())
        self.send_header("Content-Length", str(fs[6]))
        self.send_header("Last-Modified", self.date_time_string(fs.st_mtime))
        self.end_headers()
        return f



def handle_exception(exc_type, exc_value, exc_traceback):
    print "handler called"

    logger = logging.getLogger(__name__)

    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    logger.error(
        "Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))


def rpc_server_main():
    # setup
    logging_config = {
        'disable_existing_loggers': False,
        'formatters': {
            'extended': {
                'format':
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            },
            'simple': {
                'format': '%(name)-20s%(levelname)-8s%(message)s'
            }
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'formatter': 'extended',
                'level': 'DEBUG',
                'stream': 'ext://sys.stderr'
            },
            'mplog': {
                'class': 'raspyre_rpcserver.mplog.MultiProcessingLog',
                'formatter': 'extended',
                'level': 'INFO',
                'maxsize': 1024,
                'mode': 'a',
                'name': 'rpc_server.log',
                'rotate': 0
            }
        },
        'root': {
            'handlers': ['console', 'mplog'],
            'level': 'DEBUG'
        },
        'version': 1
    }

    if len(sys.argv) < 2:
        sys.exit('Usage: {} /data/directory/path [/logging/directory]'.format(
            sys.argv[0]))

    logging_path = '/tmp'
    if len(sys.argv) == 3:
        logging_path = sys.argv[2]

    logger = logging.getLogger(__name__)
    data_directory = os.path.abspath(sys.argv[1])
    logging_config['handlers']['mplog']['name'] = \
        os.path.join(logging_path, logging_config['handlers']['mplog']['name'])
    logging.config.dictConfig(logging_config)

    sys.excepthook = handle_exception

    logger.info("Starting Raspyre RPC Server")

    server = VerboseFaultXMLRPCServer(
        ("0.0.0.0", 8000), requestHandler=RequestHandler, allow_none=True)

    raspyre_rpc = RaspyreRPC(data_directory=data_directory)
    server.register_introspection_functions()
    server.register_instance(raspyre_rpc)
    server.serve_forever()


if __name__ == "__main__":
    rpc_server_main()
