"""Raspyre-RPCServer

This module is used to create a XMLRPC-Server for the Raspyre
SHM platform.

"""
from .. import _version
#from . import mplog
import multiprocessing_logging
from .functions import RaspyreService
import sys
if sys.version_info[0] == 3:
    from xmlrpc.server import SimpleXMLRPCServer
    from xmlrpc.server import SimpleXMLRPCRequestHandler
    from http.server import SimpleHTTPRequestHandler
    import xmlrpc.server as xmlrpclib
else:
    from SimpleXMLRPCServer import SimpleXMLRPCServer
    from SimpleXMLRPCServer import SimpleXMLRPCRequestHandler
    from SimpleHTTPServer import SimpleHTTPRequestHandler
    import xmlrpclib
import sys
import os
import logging
import logging.config
import argparse
import socketserver

logger = logging.getLogger(__name__)

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

            #logger = logging.getLogger(__name__)
            logger.error(
                "Dispatch exception", exc_info=(exc_type, exc_value, tb))
        return response


class ThreadedXMLRPCServer(SimpleXMLRPCServer, socketserver.ThreadingMixIn):
    pass

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
    #logger = logging.getLogger(__name__)

    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    logger.error(
        "Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))

def run_rpc_server(datadir, address="0.0.0.0", port=8000, logfile=None, configdir=None, verbose=False):
    root_logger = logging.getLogger()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    consolehandler = logging.StreamHandler(stream=sys.stdout)
    consolehandler.setFormatter(formatter)
    if verbose:
        consolehandler.setLevel(logging.DEBUG)
    else:
        consolehandler.setLevel(logging.INFO)
    root_logger.addHandler(consolehandler)

    if logfile is not None:
        logfile = os.path.abspath(logfile)
        handler = logging.handlers.RotatingFileHandler(
            filename=logfile,
            mode='a')
        handler.setFormatter(formatter)
        #mphandler = mplog.MultiProcessingLog(name=logfile, mode='a', maxsize=1024, rotate=0)
        #mphandler.setFormatter(formatter)

        if verbose:
            #mphandler.setLevel(logging.DEBUG)
            handler.setLevel(logging.DEBUG)
        else:
            #mphandler.setLevel(logging.INFO)
            handler.setLevel(logging.INFO)
        #root_logger.addHandler(mphandler)
        root_logger.addHandler(handler)
        multiprocessing_logging.install_mp_handler()


    sys.excepthook = handle_exception

    #logger = logging.getLogger(__name__)
    if verbose:
        logger.setLevel(logging.DEBUG)
        root_logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    logger.info("Starting Raspyre RPC Server")

    logger.debug("Logging verbose information")

    #server = VerboseFaultXMLRPCServer(
    #    (address, port), requestHandler=RequestHandler, allow_none=True, logRequests=True)
    #server = SimpleXMLRPCServer(
    #    (address, port), requestHandler=RequestHandler, allow_none=True, logRequests=True)
    server = ThreadedXMLRPCServer(
            (address, port), requestHandler=RequestHandler, allow_none=True, logRequests=True)

    raspyreservice = RaspyreService(data_directory=datadir,
                                    configuration_directory=configdir)
    server.register_instance(raspyreservice)
    server.register_introspection_functions()
    server.serve_forever()


def main():
    parser = argparse.ArgumentParser()
    __version__ = _version.get_versions()["version"]

    def storage_path(directory):
        if not os.path.exists(directory):
            raise argparse.ArgumentTypeError("Directory not found")
        if not os.access(directory, os.W_OK):
            raise argparse.ArgumentTypeError("Directory is not writable")
        return directory

    parser.add_argument(
        'datadir', action='store', type=storage_path, help="Data storage directory")
    parser.add_argument(
        '--address', '-a', nargs=1, action='store', help='Interface to bind for connections (default 0.0.0.0)', default=["0.0.0.0"])
    parser.add_argument(
        '--port', '-p',  nargs=1, action='store', type=int, default=[8000])
    parser.add_argument(
        '--logfile', '-l', help='Log file', nargs=1, action='store')
    parser.add_argument(
        '--configdir',
        '-c',
        help='Directory for configuration files',
        nargs=1,
        type=storage_path,
        action='store')
    parser.add_argument('--verbose', '-v', action='store_true', dest='verbose')
    parser.add_argument(
        '--version',
        action='version',
        version="%(prog)s {version}".format(version=__version__))

    args = parser.parse_args()
    args.address = args.address[0]
    if args.configdir is not None:
        args.configdir = args.configdir[0]
    else:
        args.configdir = args.datadir
    args.port = args.port[0]
    args.logfile = args.logfile[0]
    #print args.configdir

    run_rpc_server(datadir=args.datadir,
                   address=args.address,
                   port=args.port,
                   configdir=args.configdir,
                   logfile=args.logfile,
                   verbose=args.verbose)


if __name__ == "__main__":
    main()
    # rpc_server_main()
