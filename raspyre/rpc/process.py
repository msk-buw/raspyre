import multiprocessing
import logging
import arrow
import time
import os
import datetime
import struct
from .writer import generate_binary_header


class MeasureProcess(multiprocessing.Process):
    __version = "0.5"

    def __init__(self,
                 sensor,
                 sensor_name,
                 config,
                 frequency,
                 axis,
                 data_dir,
                 chunked=False,
                 chunk_minutes=10):
        multiprocessing.Process.__init__(self)
        self.measurement_name = "unnamed"
        self.sensor = sensor
        self.sensor_name = sensor_name
        self.config = config
        self.frequency = frequency
        self.frequency_step = 1.0 / self.frequency
        self.axis = axis
        self.fmt = "d" + "".join(sensor.struct_fmt(axis))
        self.struct = struct.Struct(self.fmt)
        self.data_dir = data_dir
        self.chunked = chunked
        self.chunk_minutes = chunk_minutes
        self.exitEvent = multiprocessing.Event()
        self.logger = logging.getLogger("measurement")
        self.metadata = {
            "devicename": "Raspberry Pi 2 Model B",
            "version": self.__version,
            "frequency": self.frequency,
            "type": "manual",
            "sensors": 1,
            "vendor": str(self.sensor.__class__.__name__),
            "name": self.sensor_name,
            "delay": 0,
            "range": 0,
            "resolution": 0,
            "power": 0
        }
        date_float = arrow.utcnow().float_timestamp
        self.units = ['dt64'] + sensor.units(axis)
        self.column_names = ['time'] + self.axis
        self.file_header = generate_binary_header(
            date_float, self.metadata, self.fmt, self.units, self.column_names)

    def setMeasurementName(self, measurement_name):
        self.measurement_name = measurement_name

    def run(self):
        self.logger.info(
            "Starting measurement \"{}\"".format(self.measurement_name))
        # TODO!!!! REIMPLEMENT THIS FEATURE!
        #updateConfigFile("Configuration", "resume", "true")
        start = time.time()
        count = 0
        rec = []
        filetimestamp = arrow.utcnow().format('YYYY-MM-DD-HH-mm-ss')
        #current_dir = os.getcwd()
        #path = os.path.join(current_dir, "rpcdata/")
        path = self.data_dir

        #sensor.logParameters()

        while not self.exitEvent.is_set():
            endTime = datetime.datetime.now() + datetime.timedelta(
                minutes=self.chunk_minutes)
            filetimestamp = arrow.utcnow().format('YYYY-MM-DD-HH-mm-ss')
            filename = os.path.join(
                path, self.measurement_name + "_" + self.sensor_name + "_" +
                filetimestamp + ".bin")
            with open(filename, 'wb') as f:
                f.write(self.file_header)
                self.logger.info("Starting file: %s" % filename)
                while True:
                    next_call = time.time() + self.frequency_step
                    record = self.sensor.getRecord(*self.axis)
                    #rec.append(pointValue)
                    count += 1
                    timenow = arrow.utcnow()
                    #self.logger.debug("Fetched value: {}".format(record))
                    #record['time'] = timenow.float_timestamp
                    #print "record"
                    #print record.values

                    # TODO: refactor this abomination!
                    magic = [record[x] for x in self.axis]
                    #data_entry = struct.pack('d' + self.fmt, record.values['time'], *magic)
                    data_entry = self.struct.pack(timenow.float_timestamp,
                                                  *magic)

                    f.write(data_entry)
                    if self.exitEvent.is_set():
                        self.logger.info(
                            "Received exit event. Closing measurement file.")
                        f.close()
                        self.logger.info(
                            "Disabling resume in configuration file.")
                        # TODO: IMPLEMENT THIS FEATURE!!
                        #updateConfigFile("Configuration", "resume", "false")
                        break

                    if self.chunked and datetime.datetime.now() >= endTime:
                        f.close()
                        break

                    sleeptime = next_call - time.time()
                    if sleeptime > 0:
                        time.sleep(sleeptime)

    def terminate(self):
        self.logger.info("terminate() called. Setting exit event.")
        self.exitEvent.set()
