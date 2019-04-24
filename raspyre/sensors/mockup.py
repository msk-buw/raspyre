"""
A mockup sensor to test framework functionality. It returns random values. The only configurable parameter is "sps" that defines the samples per second the sensor produces. It implements the Sensor interface provided by the raspyre framework and can be used as a reference.
"""
import time
import random
import logging

from raspyre.sensor import Sensor
from raspyre.record import Record

class Mockup(Sensor) :
    sensor_attributes = { 'x': ('g', 'd'),
                          'y': ('g', 'd'),
                          'z': ('g', 'd')}

    def __init__(self , sps ) :
        super(Mockup , self).__init__()
        self.sps = sps
        self.lastSample = time.time()
        logger = logging.getLogger(__name__)
        logger.info("initialized mockup sensor with {sps} sps".format(sps = sps))

    def getRecord(self , *args) :
        period = 1./self.sps
        now = time.time()
        #while (now - self.lastSample < period):
        #    now = time.time()
        record = Record()
        for axis in args :
            if axis in ['x' , 'y' , 'z'] :
                record[axis] = random.random()
            else:
                raise KeyError('Invalid axis specifier given')
        self.lastSample = now
        return record

    def getAttributes(self) :
        return ['x' , 'y' , 'z']

    def getConfig(self) :
        return { 'type' : 'mockup' , 'sps' : self.sps }

    def updateConfig(self, **kwargs) :
        if 'sps' in kwargs:
            self.sps = float(kwargs.get('sps', 860))

def build(**kwargs) :
    logger = logging.getLogger(__name__)
    if not 'sps' in kwargs :
        logger.warning("sps not set in config")
    sps = float(kwargs.get('sps' , 860))
    return Mockup(sps)


