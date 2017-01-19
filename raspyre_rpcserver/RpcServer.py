from MeasureProcess import MeasureProcess
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
            #self.send_error(404, "File not found")
            self.send_response(404)
            return None
        self.send_response(200)
        self.send_header("Content-type", ctype)
        fs = os.fstat(f.fileno())
        self.send_header("Content-Length", str(fs[6]))
        self.send_header("Last-Modified", self.date_time_string(fs.st_mtime))
        self.end_headers()
        return f

class RaspyreRPC(object):
    def __init__(self, data_directory):
        self.sensors = {}
        self.measurement_processes = {}
        self.data_directory = data_directory

    def ping(self):
        return True

    def startMeasurement(self, measurementname, sensornames=None, delay=0):
        sensorlist = []
        if sensornames == None: # start all sensors
            sensorlist = self.sensors.keys()
        elif isinstance(sensornames, (str, unicode)):
            sensorlist = [sensornames]
        else:
            sensorlist = sensornames
        if not self.sensors:
            raise xmlrpclib.Fault(1, 'No sensors have been configured!')

        for sensorname in sensorlist:
            if sensorname not in self.sensors:
                raise xmlrpclib.Fault(1, 'Sensor "{}" is not in the sensorlist'.format(sensorname))
            else:
                # TODO start measurement
                #self.sensors[sensorname].start(measurementname)
                self.measurement_processes[sensorname].setMeasurementName(measurementname)
                self.measurement_processes[sensorname].start()
                self.sensors[sensorname]["measuring"] = True
        return True

    def stopMeasurement(self, sensornames=None, delay=0):
        sensorlist = []
        if sensornames == None: # start all sensors
            sensorlist = self.sensors.keys()
        elif isinstance(sensornames, (str, unicode)):
            sensorlist = [sensornames]
        else:
            sensorlist = sensornames
        if not self.sensors:
            raise xmlrpclib.Fault(1, 'No sensors have been configured!')

        logger = logging.getLogger("rpc_server")
        for sensorname in sensorlist:
            if sensorname not in self.sensors:
                raise xmlrpclib.Fault(1, 'Sensor "{}" is not in the sensorlist'.format(sensorname))
            else:
                # TODO stop measurement
                logger.info("Shutting down measurement subprocess with sensor \"{}\"".format(sensorname))
                if self.measurement_processes[sensorname].is_alive():
                    self.measurement_processes[sensorname].terminate()
                    self.measurement_processes[sensorname].join()
                    self.measurement_processes[sensorname] = 0
                    self.measurement_processes[sensorname] = MeasureProcess(self.sensors[sensorname]['sensor'],
                                                                            sensorname,
                                                                            self.sensors[sensorname]['configuration'],
                                                                            self.sensors[sensorname]['configuration']['frequency'],
                                                                            self.sensors[sensorname]['configuration']['axis'],
                                                                            self.data_directory)
                self.sensors[sensorname]["measuring"] = False
        return True

    def isMeasuring(self, sensorname=None):
        if sensorname not in sensors:
            raise xmlrpclib.Fault(1, 'Sensor "{}" is not in the sensorlist'.format(sensorname))
        else:
            return self.sensors[sensorname]["measuring"]

    def getFiles(self):
        files = [f for f in os.listdir(self.data_directory) if os.path.isfile(os.path.join(self.data_directory, f))]
        return files
        #return ["mockmeasurement_mocksensor1_2016-12-24-23-42-00.bin",
        #        "mockmeasurement_mocksensor1_2016-12-24-23-52-00.bin",
        #        "mockmeasurement_mocksensor2_2016-12-24-23-42-00.bin"]

    def getNetworkNodes(self):
        return []

    def getSensors(self):
        return self.sensors

    def addSensor(self, sensorname, config={}):
        if sensorname in self.sensors:
            raise xmlrpclib.Fault(1, 'Sensor "{}" already exists!'.format(sensorname))
        #self.sensors[sensorname] = { "configuration": config, "measuring": False, "stream": ""}

        #sensors[sensorname] = rpcSensor.Sensor(configuration = config, measuring = False, stream = "")
        sensor = raspyre.sensorbuilder.createSensor(**config)
        self.sensors[sensorname] = { "configuration": config,
                                     "measuring": False,
                                    "stream": "",
                                     "sensor": sensor }
        #self.sensors[sensorname]["sensor"] = sensor
        self.measurement_processes[sensorname] = MeasureProcess(sensor, sensorname, config, config['frequency'], config['axis'], self.data_directory)

        #except:
        #    raise xmlrpclib.Fault(1, 'Invalid configuration')
        # TODO setup sensor
        return True

    def deleteSensor(self, sensorname):
        if sensorname not in self.sensors:
            raise xmlrpclib.Fault(1, 'Sensor "{}" does not exist'.format(sensorname))
        del self.sensors[sensorname]
        return True

    def modifySensor(self, sensorname, config):
        if sensorname not in self.sensors:
            raise xmlrpclib.Fault(1, 'Sensor "{}" does not exist'.format(sensorname))
        self.sensors[sensorname]["config"].update(config)
        return True

    def getSystemDate(self):
        return str(datetime.datetime.now())

    def setSystemDate(self, date):
        print type(date)
        print date
        if not isinstance(date, datetime.datetime):
            raise xmlrpclib.Fault(1, 'Must provide a DATE type!')
        return True

    def setExtra(self, extra={}):
        return True

    def getExtra(self, extra):
        return {}

    def clearSensors(self):
        self.sensors = {}



def rpc_server_main():
    # setup
    logging_config = {
        'disable_existing_loggers': False,
        'formatters': {
            'extended': {
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
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
        'version': 1}


    if len(sys.argv) < 2:
        sys.exit('Usage: {} /data/directory/path [/logging/directory]'.format(sys.argv[0]))

    logging_path = '/tmp'
    if len(sys.argv) == 3:
        logging_path = sys.argv[2]

    logger = logging.getLogger("rpc_server")
    data_directory = os.path.abspath(sys.argv[1])
    #logging_conf_file = 'logging.yaml'
    #current_dir = os.getcwd()
    #path = os.path.join(current_dir, logging_conf_file)
    #config = {}
    #if os.path.exists(path):
    #    with open(path, 'rt') as f:
    #        config = yaml.load(f.read())
    #        print config
    #    logging.config.dictConfig(config)
    logging_config['handlers']['mplog']['name'] = \
        os.path.join(logging_path, logging_config['handlers']['mplog']['name'])
    logging.config.dictConfig(logging_config)
    #else:
    #    print "could not find logging configuration file"



    logger.info("Starting Raspyre RPC Server")

    server = SimpleXMLRPCServer(("0.0.0.0", 8000),
                                requestHandler=RequestHandler)

    raspyre_rpc = RaspyreRPC(data_directory=data_directory)
    server.register_introspection_functions()
    server.register_instance(raspyre_rpc)
    server.serve_forever()


if __name__ == "__main__":
    rpc_server_main()
