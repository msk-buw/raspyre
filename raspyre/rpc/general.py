from .process import MeasureProcess
from raspyre import sensorbuilder
import xmlrpclib
import logging
import os
import subprocess
import datetime


class RaspyreRPC(object):
    def __init__(self, data_directory):
        self.sensors = {}
        self.measurement_processes = {}
        self.data_directory = data_directory

    def ping(self):
        """FIXME! briefly describe function

        :returns: 
        :rtype: 

        """
        return True

    def startMeasurement(self, measurementname, sensornames=None, delay=0):
        """FIXME! briefly describe function

        :param measurementname: 
        :param sensornames: 
        :param delay: 
        :returns: 
        :rtype: 

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

    def stopMeasurement(self, sensornames=None, delay=0):
        """FIXME! briefly describe function

        :param sensornames: 
        :param delay: 
        :returns: 
        :rtype: 

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

    def isMeasuring(self, sensorname=None):
        """FIXME! briefly describe function

        :param sensorname: 
        :returns: 
        :rtype: 

        """
        if sensorname not in self.sensors:
            raise xmlrpclib.Fault(
                1, 'Sensor "{}" is not in the sensorlist'.format(sensorname))
        else:
            return self.sensors[sensorname]["measuring"]

    def getFiles(self):
        """FIXME! briefly describe function

        :returns: 
        :rtype: 

        """
        files = [
            f for f in os.listdir(self.data_directory)
            if os.path.isfile(os.path.join(self.data_directory, f))
        ]
        return files

    def getNetworkNodes(self):
        """FIXME! briefly describe function

        :returns: 
        :rtype: 

        """
        return []

    def getSensors(self):
        """FIXME! briefly describe function

        :returns: 
        :rtype: 

        """
        return self.sensors

    def addSensor(self, sensorname, config={}):
        """FIXME! briefly describe function

        :param sensorname: 
        :param config: 
        :returns: 
        :rtype: 

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
        """FIXME! briefly describe function

        :param sensorname: 
        :returns: 
        :rtype: 

        """
        if sensorname not in self.sensors:
            raise xmlrpclib.Fault(
                1, 'Sensor "{}" does not exist'.format(sensorname))
        del self.sensors[sensorname]
        return True

    def modifySensor(self, sensorname, config):
        """FIXME! briefly describe function

        :param sensorname: 
        :param config: 
        :returns: 
        :rtype: 

        """
        if sensorname not in self.sensors:
            raise xmlrpclib.Fault(
                1, 'Sensor "{}" does not exist'.format(sensorname))
        self.sensors[sensorname]["config"].update(config)
        return True

    def getSystemDate(self):
        """FIXME! briefly describe function

        :returns: 
        :rtype: 

        """
        return str(datetime.datetime.now())

    def setSystemDate(self, date):
        """FIXME! briefly describe function

        :param date: 
        :returns: 
        :rtype: 

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
        """FIXME! briefly describe function

        :param extra: 
        :returns: 
        :rtype: 

        """
        return True

    def getExtra(self, extra):
        """FIXME! briefly describe function

        :param extra: 
        :returns: 
        :rtype: 

        """
        return {}

    def clearSensors(self):
        """FIXME! briefly describe function

        :returns: 
        :rtype: 

        """
        self.sensors = {}
        return True
