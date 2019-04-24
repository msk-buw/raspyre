"""This module provides the functions to create a sensor from a kwargs
   parameter.
"""
from raspyre.sensor import Sensor
from importlib import import_module
import logging
import inspect


def createSensor(sensor_type, **kwargs):
    logger = logging.getLogger(__name__)
    typename = sensor_type.lower()
    module = import_module("raspyre.sensors." + typename)
    logger.debug("Imported driver module \"{}\"".format(typename))
    # get module classes
    classes = inspect.getmembers(module, inspect.isclass)
    # Filter found classes in module. We need to find a class that is a
    # descendant of raspyre.sensor.Sensor but not of type raspyre.sensor.Sensor
    classes = [
        class_ for class_ in classes
        if class_[1] != Sensor and issubclass(class_[1], Sensor)
    ]
    if len(classes) > 1:
        raise TypeError("Module defines more than one Sensor class!")
    if len(classes) == 0:
        raise TypeError(
            "Module defines no class that extents raspyre.sensor.Sensor")
    sensor_class = classes[0][1]
    # Determine the arguments of the constructor
    sensor_args = inspect.getargspec(sensor_class.__init__).args
    if 'self' in sensor_args:
        sensor_args.remove('self')
    init_args = {k: v for k, v in kwargs.items() if k in sensor_args}
    # Pass every named parameter that the constructor understands and
    # instantiate the specific sensor object
    sensor = sensor_class(**init_args)
    return sensor
