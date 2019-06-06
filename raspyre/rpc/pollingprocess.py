from .writer import generate_binary_header
import multiprocessing
import logging
#import arrow
import time
import os
import datetime
import struct
import sys
import gc
import mmap
import ctypes

librt = ctypes.CDLL('librt.so')


class Timespec(ctypes.Structure):
    _fields_ = [('tv_sec', ctypes.c_long),
               ('tv_nsec', ctypes.c_long)]

class Sched_Param(ctypes.Structure):
    _fields_ = [('sched_priority', ctypes.c_int)]


CLOCK_MONOTONIC = ctypes.c_int(1)
TIMER_ABSTIME = ctypes.c_int(1)
MCL_CURRENT = ctypes.c_int(1)
MCL_FUTURE = ctypes.c_int(2)
SCHED_FIFO = ctypes.c_int(1)



class PollingProcess(multiprocessing.Process):
    __version = "1.3"
    PROCESS_PRIORITY = 90

    def __init__(self,
                 sensor,
                 sensor_name,
                 config,
                 frequency,
                 axis,
                 data_dir,
                 mmap_file,
                 buffer_size,
                 chunked=False,
                 chunk_minutes=10):
        multiprocessing.Process.__init__(self)
        self.logger = logging.getLogger(__name__)
        self.logger.debug("Initializing polling process")

        self.measurement_name = "unnamed"
        self.sensor = sensor
        self.sensor_name = sensor_name
        self.config = config
        self.frequency = frequency
        self.frequency_step = 1.0 / self.frequency
        self.axis = axis
        self.fmt = "d" + "".join(sensor.struct_fmt(axis))
        self.struct = struct.Struct(self.fmt)
        self.exitEvent = multiprocessing.Event()
        self.logger.debug("Preparing rt capabilities")
        self.scheduling_param = Sched_Param()
        self.scheduling_param.sched_priority = self.PROCESS_PRIORITY
        self.buffer_size = buffer_size
        self.mmap_file = mmap_file
        self.logger.debug("Opening shared memory buffer {}".format(self.mmap_file))

        self.fd = None
        self.fd = os.open(self.mmap_file, os.O_CREAT | os.O_TRUNC | os.O_RDWR)

        bs = b'\x00' * self.buffer_size
        ret = os.write(self.fd, bs)
        assert ret == self.buffer_size
        self.buf = mmap.mmap(self.fd, self.buffer_size, mmap.MAP_SHARED, mmap.PROT_WRITE | mmap.PROT_READ)

        self.index = ctypes.c_int.from_buffer(self.buf)
        self.start_offset = struct.calcsize(self.index._type_)
        self.data_size = struct.calcsize(self.fmt)
        self.ring_size = (self.buffer_size - self.start_offset) // self.data_size
        self.logger.debug("PollingProcess ring size: {}".format(self.ring_size))

    def setMeasurementName(self, measurement_name):
        self.measurement_name = measurement_name

    def run(self):
        self.logger.debug("Setting Real Time Process Priority")
        #self.scheduler.set_scheduler(self.PROCESS_PRIORITY)
        ret = librt.sched_setscheduler(0, SCHED_FIFO, ctypes.byref(self.scheduling_param))
        if ret != 0:
            self.logger.error("Could not set process priority! Exiting!")
            self.logger.error("(Are the user/process rights set correctly?)")
            return
        self.logger.debug("rt_priority set successfull")

        deadline = Timespec()
        s_nsec = 1000 * 1000 * 1000
        delay = int(self.frequency_step * s_nsec)
        counter = 0

        self.logger.debug("Disabling garbage collection for polling process")
        gc.disable()

        self.logger.debug("Locking memory pages for polling process")
        ret = librt.mlockall(MCL_CURRENT.value | MCL_FUTURE.value)
        self.logger.debug("mlockall() returned {}".format(ret))
        if ret == -1:
            self.logger.error("Error during mlockall()! Check user/process rights.")
            return

        self.logger.info(
            "Starting polling loop for sensor \"{}\"".format(self.sensor_name))
        librt.clock_gettime(CLOCK_MONOTONIC, ctypes.byref(deadline))

        while not self.exitEvent.is_set():
            deadline.tv_nsec += delay
            if deadline.tv_nsec >= s_nsec:
                deadline.tv_nsec -= s_nsec
                deadline.tv_sec += 1
            ret = librt.clock_nanosleep(CLOCK_MONOTONIC, TIMER_ABSTIME, ctypes.byref(deadline), 0)
            try:
                record = self.sensor.getRecord(*self.axis)
            except Exception as e:
                self.logger.error("Fatal error during sensor.getRecord()", exc_info=True)
                continue
            data = struct.pack(self.fmt, record.values['time'], *[record[x] for x in self.axis])
            offset = self.start_offset + counter % self.ring_size * self.data_size
            self.buf.seek(offset)
            self.buf.write(data)
            counter += 1
            self.index.value = counter % self.ring_size
            #toc = time.clock_gettime(time.CLOCK_MONOTONIC)

        self.logger.debug("polling loop terminated. Cleaning up.")
        gc.enable()
        os.close(self.fd)
        os.remove(self.mmap_file)
        self.logger.debug("Clean up successfull")
        return


    def shutdown(self):
        self.logger.info("shutdown() called. Setting exit event.")
        self.exitEvent.set()
