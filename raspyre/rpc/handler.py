from .writer import generate_binary_header
import multiprocessing
import logging
import time
import os
import datetime
import struct
import sys
import mmap
import ctypes


class HandlerProcess(multiprocessing.Process):
    __version = "1.3"

    def __init__(self,
                 sensor,
                 sensor_name,
                 config,
                 frequency,
                 axis,
                 mmap_file,
                 buffer_size,
                 data_dir,
                 csv=False,
                 chunked=False,
                 chunk_minutes=10):
        multiprocessing.Process.__init__(self)
        self.logger = logging.getLogger(__name__)
        self.logger.debug("Initializing HandlerProcess")

        self.measurement_name = 'unnamed'
        self.sensor = sensor
        self.sensor_name = sensor_name
        self.config = config
        self.frequency = frequency
        self.axis = axis
        self.fmt = 'd' + ''.join(sensor.struct_fmt(axis))
        self.struct = struct.Struct(self.fmt)
        self.data_dir = data_dir
        self.chunked = chunked
        self.chunk_minutes = chunk_minutes
        self.exitEvent = multiprocessing.Event()
        self.metadata = {
            "devicename": "Raspberry Pi 3 Model B+",
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

        self.units = ['dt64'] + sensor.units(axis)
        self.column_names = ['time'] + self.axis
        date_float = time.time()
        self.file_header = generate_binary_header(
            date_float, self.metadata, self.fmt, self.units, self.column_names)

        self.mmap_file = mmap_file
        self.buffer_size = buffer_size
        self.fd = os.open(self.mmap_file, os.O_RDONLY)
        self.buf = mmap.mmap(self.fd, self.buffer_size, mmap.MAP_SHARED, mmap.PROT_READ)
        self.start_offset = struct.calcsize(ctypes.c_int._type_)
        self.data_size = struct.calcsize(self.fmt)
        self.ring_size = (self.buffer_size - self.start_offset) // self.data_size

        self.logger.debug("Finished initialization of HandlerProcess")

    def setMeasurementName(self, measurement_name):
        self.measurement_name = measurement_name

    def run(self):
        filetimestamp = time.strftime('%Y-%m-%d-%H-%M-%S')
        filename = "_".join((self.measurement_name, self.sensor_name, filetimestamp)) + '.csv'
        filename = os.path.join('.', filename)

        self.logger.debug("Entering handler loop")
        while not self.exitEvent.is_set():
            old_index = 0
            with open(filename, 'w') as f:
                while True:
                    index = struct.unpack('i', self.buf[0:4])[0]
                    #self.logger.debug("Index: {}".format(index))
                    if old_index > index:
                        self.logger.debug("index overrun, processing till ring size")
                        for i in range(old_index):
                            offset = self.start_offset + i * self.data_size
                            values = struct.unpack(self.fmt, self.buf[offset:offset+self.data_size])
                            f.write("%f %f %f %f\n" % (values[0], values[1], values[2], values[3]))
                        old_index = 0
                    elif index > old_index:
                        for i in range(old_index, index + 1):
                            offset = self.start_offset + i * self.data_size
                            values = struct.unpack(self.fmt, self.buf[offset:offset+self.data_size])
                            f.write("%f %f %f %f\n" % (values[0], values[1], values[2], values[3]))
                        old_index = index + 1

                    time.sleep(0.1)
                    if(self.exitEvent.is_set()):
                        break
                f.flush()

    def terminate(self):
        self.exitEvent.set()
