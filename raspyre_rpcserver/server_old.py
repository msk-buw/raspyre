from raspyre import sensorbuilder, helpers
from SimpleXMLRPCServer import SimpleXMLRPCServer
from SimpleXMLRPCServer import SimpleXMLRPCRequestHandler
from ctypes import c_char_p
import xmlrpclib
import logging
import arrow
import datetime
import time
import json
import struct
import sys
import os
import multiprocessing
import logging.config
import yaml
import ConfigParser

measure_process = 0
logger = logging.getLogger("rpc_server")
sensor = 0
csv_column_titles = ()
manager = multiprocessing.Manager()
shared_filename = manager.Value(c_char_p, "")

class RequestHandler(SimpleXMLRPCRequestHandler):
    rpc_paths = ("/RPC2",)

class MeasureProcess(multiprocessing.Process):
    def __init__(self, sensor, axis, fmt, shared_filename):
        multiprocessing.Process.__init__(self)

        self.sensor = sensor
        self.fmt = fmt
        self.axis = axis

        self.exitEvent = multiprocessing.Event()
        self.shared_filename = shared_filename
        self.logger = logging.getLogger("measurement")



    def run(self):
        self.logger.info("Starting measurement")
        updateConfigFile("Configuration", "resume", "true")
        start = time.time()
        count = 0
        rec = []
        filetimestamp = arrow.utcnow().format('YYYY-MM-DD-HH-mm-ss')
        #current_dir = os.path.dirname(os.path.realpath(__file__))
        current_dir = os.getcwd()
        path = os.path.join(current_dir, "rpcdata/")

        sensor.logParameters()

        while not self.exitEvent.is_set():
            endTime = datetime.datetime.now() + datetime.timedelta(minutes=5)
            filetimestamp = arrow.utcnow().format('YYYY-MM-DD-HH-mm-ss')
            filename = path + "measurements_fs_raw_" + filetimestamp + ".bin"
            with open(filename, 'wb') as f:
                self.shared_filename.value = filename
                self.logger.info("Starting file: %s" % filename)
                while True:
                    next_call = time.time() + 0.005
                    record = self.sensor.getRecord('acc0', 'temperature')
                    #rec.append(pointValue)
                    count += 1
                    timenow = arrow.utcnow()
                    #self.logger.debug("Fetched value: {}".format(record))
                    data_entry = struct.pack("dii", timenow.float_timestamp, record.values['acc0'], record.values['temperature'])

                    f.write(data_entry)
                    if self.exitEvent.is_set():
                        self.logger.info("Received exit event. Closing measurement file.")
                        f.close()
                        self.logger.info("Disabling resume in configuration file.")
                        updateConfigFile("Configuration", "resume", "false")
                        break

                    if datetime.datetime.now() >= endTime:
                        f.close()
                        break

                    sleeptime = next_call - time.time()
                    if sleeptime > 0:
                        time.sleep(sleeptime)




       #
           # record = self.sensor.getRecord(*self.axis)
# ar[count] = (record['time'], record['acc0'], record['temperature'])
           # count += 1

           # #if count == size:
           # if count % 100 == 0:
           # #    if True:
           #     if self.exitEvent.is_set():
           #         self.logger.info("Received exit event. Writing measurement file.")
           #         #ar.resize(count + 1)
           #         #ar.tofile(filename)
           #         with open(filename, 'wb') as f:
           #             for i in xrange(count):
           #                 f.write(struct.pack("dii", ar[i][0], ar[i][1], ar[i][2]))
           #         break

    def terminate(self):
        self.logger.info("terminate() called. Setting exit event.")
        self.exitEvent.set()

def start():
    global measure_process
    logger = logging.getLogger("rpc_server")
    if type(measure_process) is MeasureProcess and not measure_process.is_alive():
        logger.info("Starting measurement subprocess")
        measure_process.start()
        return True
    else:
        return False

def updateConfigFile(section, key, value):
    logger.info("Updating configuration file.")
    config_file = "rpc_server.ini"
    #current_dir = os.path.dirname(os.path.realpath(__file__))
    current_dir = os.getcwd()
    config_path = os.path.join(current_dir, config_file)
    config = ConfigParser.SafeConfigParser()
    config.read(config_path)
    try:
        config.add_section(section)
    except ConfigParser.DuplicateSectionError as e:
        logger.info("Configuration section already exists - updating...")
        pass

    config.set(section, key, value)

    logger.info("Writing configuration to {}".format(config_path))
    with open(config_path, "wb") as f:
        config.write(f)

def setupProcess():
    global measure_process, sensor, shared_filename
    return MeasureProcess(sensor, ['acc0', 'temperature'], "dii", shared_filename)

def stop():
    global measure_process, sensor
    logger = logging.getLogger("rpc_server")
    if measure_process.is_alive():
        logger.info("Shutting down measurement subprocess")
        measure_process.terminate()
        measure_process.join()
        measure_process = 0
        measure_process = setupProcess()
        return True
    else:
        return False

def status():
    global measure_process
    #print("Child process state: %d" % measure_process.is_alive())
    return measure_process.is_alive()

#def convertBinToCSV(inputpath, outputpath, fmt, writeHeader=False, delimiter=',', convertTimeStamps=False, convertTimeZone='Europe/Berlin'):
#    logger = logging.getLogger("rpc_server")
#    if measure_process.is_alive():
#        logger.error("Cannot convert data while measurement is running!")
#        return False
#
#    logger.debug("Converting input file %s to csv output file %s with format %s." % (inputpath, outputpath, fmt))
#    print "Column titles:", csv_column_titles
#    convertbin2csv.convertBinToCSV(inputpath, outputpath, fmt, writeHeader, csv_column_titles, delimiter, convertTimeStamps, convertTimeZone)
#    return True

def setColumnTitles(*titles):
    global csv_column_titles
    csv_column_titles = titles
    return True

def downloadFile(filepath):
    with open(filepath, 'rb') as handle:
        return xmlrpclib.Binary(handle.read())

def getLastFilename():
    global shared_filename
    return shared_filename.value

def ping():
    return True

def setupSensor(fs):
    global measure_process, sensor
    logger.info("setupSensor() - config: {}".format(fs))
    sensor.updateRawConfig("/home/pi/raspyre/config/fs_{}.dump".format(fs))
    time.sleep(0.5)
    measure_process = setupProcess()
    return True

def setupSensorConfig(config_file, update_config_file=True):
    global measure_process, sensor
    logger.info("setupSensorConfig() - config: {}".format(config_file))
    sensor.updateRawConfig(config_file)
    if update_config_file:
        logger.info("Updating settings file")
        updateConfigFile("Configuration", "fs_configuration", config_file)
    measure_process = setupProcess()
    return True

def loadConfigFile():
    config_file = "rpc_server.ini"
    current_dir = os.path.dirname(os.path.realpath(__file__))
    config_path = os.path.join(current_dir, config_file)
    logger.info("Reading configuration file: {}".format(config_path))
    config = ConfigParser.SafeConfigParser()
    config.read(config_path)
    fs_configuration = ""
    resume = False
    options = {}
    options["resume"] = False
    options["fs_configuration"] = ""
    options["chunk_minutes"] = 10
    for option in ["resume", "fs_configuration", "chunk_minutes"]:
        try:
            if option == "resume":
                options[option] = config.getboolean("Configuration", option)
            else:
                options[option] = config.get("Configuration", option)
            logger.info("config: {}: {}".format(option, options[option]))
        except ConfigParser.NoSectionError as e:
            logger.warn("loadConfigFile() Warning. Could not find section! Continueing without configuration...")
        except ConfigParser.NoOptionError as e:
            logger.warn("loadConfigFile() Warning. Could not find option: {}".format(e))


    if os.path.isfile(options["fs_configuration"]):
        logger.info("Found sensor configuration option - setting up sensor")
        setupSensorConfig(options["fs_configuration"], update_config_file=False)

        if options["resume"]:
            logger.info("Found resume option - resuming measurement")
            start()

def setup():
    #current_dir = os.path.dirname(os.path.abspath(__file__))
    current_dir = os.getcwd()
    logging_conf_file = 'logging.yaml'
    path = os.path.join(current_dir, logging_conf_file)
    print path
    if os.path.exists(path):
        with open(path, 'rt') as f:
            config = yaml.load(f.read())
        logging.config.dictConfig(config)
    else:
        print "could not find logging configuration file"


    logger.info("RPC Server setup finished.")
    #keep_fds = [fh.stream.fileno(), measure_fh.stream.fileno()]

def main():
    global measure_process, sensor, shared_filename
    setup()
    logger = logging.getLogger("rpc_server")
    logger.info("Started RPC Server daemon.")

    #sensor = sensorbuilder.createSensor(type="mockup", sps=600)
    sensor = sensorbuilder.createSensor(type="mockup", sps=100)

    loadConfigFile()

    server = SimpleXMLRPCServer(("0.0.0.0", 8000),
                                requestHandler=RequestHandler)
    server.register_introspection_functions()
    server.register_function(start)
    server.register_function(stop)
    server.register_function(status)
    server.register_function(setColumnTitles)
    server.register_function(downloadFile)
    server.register_function(getLastFilename)
    server.register_function(ping)
    server.register_function(setupSensor)
    server.register_function(setupSensorConfig)
    server.serve_forever()

if __name__ == "__main__":
    main()
