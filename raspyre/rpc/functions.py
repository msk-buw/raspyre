from process import MeasureProcess
from raspyre import sensorbuilder
import xmlrpclib
import logging
import os
import subprocess
import datetime


class MeasurementHandler(object):
    def __init__(self, data_directory):
        self.sensors = {}
        self.measurement_processes = {}
        self.data_directory = data_directory

    def ping(self):
        """This function simply returns True.
        It is used as simple connectivity checking function.

        :returns: True
        :rtype: Boolean

        """
        return True

    def startMeasurement(self, measurementname, sensornames=None):
        """This function starts a measurement process for the specified sensors.

        :param measurementname: String describing the measurement
        :param sensornames: None [all sensors], String [one specific sensor], List of Strings (optional)
        :returns: True
        :rtype: Boolean

        """
        sensorlist = []
        if sensornames is None:  # start all sensors
            sensorlist = self.sensors.keys()
        elif isinstance(sensornames, (str, unicode)):
            sensorlist = [sensornames]
        else:
            sensorlist = sensornames
        if not self.sensors:
            raise xmlrpclib.Fault(1, 'No sensors have been configured!')

        for sensorname in sensorlist:
            if sensorname not in self.sensors:
                raise xmlrpclib.Fault(
                    1,
                    'Sensor "{}" is not in the sensorlist'.format(sensorname))
            else:
                self.measurement_processes[sensorname].setMeasurementName(
                    measurementname)
                self.measurement_processes[sensorname].start()
                self.sensors[sensorname]["measuring"] = True
        return True

    def stopMeasurement(self, sensornames=None):
        """This function stops a currently running measurement.

        :param sensornames: None [all sensors], String [one specific sensor], List of Strings (optional)
        :returns: True
        :rtype: Boolean

        """
        sensorlist = []
        if sensornames is None:  # start all sensors
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
                raise xmlrpclib.Fault(
                    1,
                    'Sensor "{}" is not in the sensorlist'.format(sensorname))
            else:
                # TODO stop measurement
                logger.info(
                    "Shutting down measurement subprocess with sensor \"{}\"".
                    format(sensorname))
                if self.measurement_processes[sensorname].is_alive():
                    self.measurement_processes[sensorname].terminate()
                    self.measurement_processes[sensorname].join()
                    self.measurement_processes[sensorname] = 0
                    self.measurement_processes[sensorname] = MeasureProcess(
                        self.sensors[sensorname]['sensor'], sensorname,
                        self.sensors[sensorname]['configuration'],
                        self.sensors[sensorname]['configuration']['frequency'],
                        self.sensors[sensorname]['configuration']['axis'],
                        self.data_directory)
                self.sensors[sensorname]["measuring"] = False
        return True

    def isMeasuring(self, sensorname):
        """This function returns True if the specified sensor is currently 
        used by a measurement process.

        :param sensorname: String of sensor name
        :returns: True|False
        :rtype: Boolean

        """
        if sensorname not in self.sensors:
            raise xmlrpclib.Fault(
                1, 'Sensor "{}" is not in the sensorlist'.format(sensorname))
        else:
            return self.sensors[sensorname]["measuring"]

    def getFiles(self):
        """This function lists the filenames in the data directory.

        :returns: List of file names
        :rtype: List of Strings

        """
        files = [
            f for f in os.listdir(self.data_directory)
            if os.path.isfile(os.path.join(self.data_directory, f))
        ]
        return files

    def getNetworkNodes(self):
        """FIXME: This function is not implemented

        :returns: empty List
        :rtype: List

        """
        return []

    def getSensors(self):
        """This function returns the internal sensor dictionary.

        :returns: Dictionary of current configuration
        :rtype: Dictionary

        """
        return self.sensors

    def addSensor(self, sensorname, config={}):
        """This function adds a sensor to the current setup.
        Each installed raspyre-sensor-driver package can be used to instantiate
        a sensor for measurement usage (e.g. raspyre-mpu6050, raspyre-ads1115)
        Example call:
        >>> addSensor("S1_left_bridge", config={type="MPU6050", address=0x69})

        :param sensorname: Unique String to identify sensor
        :param config: Dictionary of sensor configuration data.
                       A key "type" is used to specify which sensor driver package to load.
                       The remaining dictionary keys are passed as it to the corresponding
                       initialization function of the given sensor driver package.
        :returns: True
        :rtype: Boolean

        """
        if sensorname in self.sensors:
            raise xmlrpclib.Fault(
                1, 'Sensor "{}" already exists!'.format(sensorname))

        sensor = sensorbuilder.createSensor(**config)
        self.sensors[sensorname] = {
            "configuration": config,
            "measuring": False,
            "stream": "",
            "sensor": sensor
        }
        self.measurement_processes[sensorname] = MeasureProcess(
            sensor, sensorname, config, config['frequency'], config['axis'],
            self.data_directory)

        return True

    def deleteSensor(self, sensorname):
        """Removes the sensor specified by its name from the current setup.

        :param sensorname: String identifying sensor
        :returns: True
        :rtype: Boolean

        """
        if sensorname not in self.sensors:
            raise xmlrpclib.Fault(
                1, 'Sensor "{}" does not exist'.format(sensorname))
        del self.sensors[sensorname]
        return True

    def modifySensor(self, sensorname, config):
        """FIXME: This function updates the configuration of a given sensor.

        :param sensorname: String identifying the sensor
        :param config: Dictionary of changes configuration parameters.
                       Each key value pair is passed to the sensor's updateConfiguration()
        :returns: True
        :rtype: Boolean

        """
        if sensorname not in self.sensors:
            raise xmlrpclib.Fault(
                1, 'Sensor "{}" does not exist'.format(sensorname))
        self.sensors[sensorname]["config"].update(config)
        return True

    def getSystemDate(self):
        """This function returns a string representation of the current system time.

        :returns: String of current datetime
        :rtype: String

        """
        return str(datetime.datetime.now())

    def setSystemDate(self, date):
        """This function sets the current system date.
        NOTICE: This function does not modify any modified realtime clock!

        :param date: String of date.
                     The parameter is passed to the system's date operation thus
                     accepts its format strings. Please refer to the Linux manpage date(1).
        :returns: True
        :rtype: Boolean

        """

        p = subprocess.Popen(
            ['date', '-s', date],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)
        output, errors = p.communicate()
        if errors:
            raise xmlrpclib.Fault(
                1, "Error during date setting: {}".format(errors))
        return True

    def setExtra(self, extra={}):
        """This function is reserved for future usage.

        :param extra: Dictionary
        :returns: True
        :rtype: Boolean

        """
        return True

    def getExtra(self, extra):
        """This function is reserved for future usage

        :param extra: Dictionary
        :returns: True
        :rtype: Boolean

        """
        return {}

    def clearSensors(self):
        """This function removes all configured sensors from the current setup.

        :returns: True
        :rtype: Boolean

        """
        self.sensors = {}
        return True
