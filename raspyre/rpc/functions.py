"""This module implements the functions exposed by the Rapsyre RPC interface.

The functions are grouped in classes and should be invoked into different
prefix namespaces.
e.g.:
class MeasurementHandler consists of functions to handle the Measurement
Processes of the Pi's GPIO interface and should reside in a namespace 
that identifies this behaviour as such.
"""

from process import MeasureProcess
from raspyre import sensorbuilder
import xmlrpclib
import logging
import os
import shutil
import subprocess
import datetime
import json

logger = logging.getLogger(__name__)

class RaspyreDirectoryNotFound(Exception):
    pass

class RaspyreDirectoryInvalid(Exception):
    pass

class RaspyreFileInvalid(Exception):
    pass



class RaspyreService(object):
    def __init__(self, data_directory, configuration_directory):
        self.sensors = {}
        self.measurement_processes = {}
        self.data_directory = os.path.normpath(data_directory)
        self.configuration_directory = os.path.normpath(configuration_directory)
        logger.debug("Initialized RaspyreService")

    def ping(self):
        """This function simply returns True.
        It is used as simple connectivity checking function.

        :returns: True
        :rtype: Boolean

        """
        logger.debug("ping() called")
        return True

    def start_measurement(self, measurementname, sensornames=None):
        """This function starts a measurement process for the specified sensors.

        :param measurementname: String describing the measurement
        :param sensornames: None [all sensors],
                            String [one specific sensor],
                            List of Strings (optional)
        :returns: True
        :rtype: Boolean

        """
        logger.debug("start_measurement() called")
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
                logger.debug("measurement name set")
                self.measurement_processes[sensorname].start()
                logger.debug("started measurement process")
                self.sensors[sensorname]["measuring"] = True
        return True

    def stop_measurement(self, sensornames=None):
        """This function stops a currently running measurement.

        :param sensornames: None [all sensors],
                            String [one specific sensor],
                            List of Strings (optional)
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

        #logger = logging.getLogger("rpc_server")
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
                        self.sensors[sensorname]['frequency'],
                        self.sensors[sensorname]['axis'],
                        self.data_directory)
                self.sensors[sensorname]["measuring"] = False
        return True

    def is_measuring(self, sensorname):
        """This function returns True if the specified sensor is currently
        used by a measurement process.

        :param sensorname: String of sensor name
        :returns: True|False
        :rtype: Boolean

        """
        if sensorname not in self.sensors:
            raise xmlrpclib.Fault(
                1, 'Sensor "{}" is not registered in the sensor list'.format(
                    sensorname))
        else:
            return self.sensors[sensorname]["measuring"]

    def list_files(self):
        """DEPRECATED! This function lists the filenames in the data directory.
        ATTENTION: This function is DEPRECATED and will be removed in a later
        version. Please use fs_ls()

        :returns: List of file names
        :rtype: List of Strings

        """
        files = [
            f for f in os.listdir(self.data_directory)
            if os.path.isfile(os.path.join(self.data_directory, f))
        ]
        return files

    def get_network_nodes(self):
        """FIXME: This function is not implemented

        :returns: empty List
        :rtype: List

        """
        return []

    def get_info(self):
        """This function returns the internal sensor dictionary.

        :returns: Dictionary of current configuration
        :rtype: Dictionary

        """
        return self.sensors

    def add_sensor(self, sensorname, sensortype, config, frequency, axis):
        """This function adds a sensor to the current setup.
        Each installed raspyre-sensor-driver package can be used to instantiate
        a sensor for measurement usage (e.g. raspyre-mpu6050, raspyre-ads1115)
        Example call:

        >>> add_sensor(sensorname="S1_left_bridge", sensor_type="MPU6050", 
                       config={address=0x69}, 
                       frequency=100, axis=['accx', 'accy', 'accz']) 

        :param sensorname: Unique String to identify sensor
        :param sensortype: String specifying the sensor driver package
        :param config: Dictionary of sensor configuration data.
                       The dictionary keys are passed to the initialization 
                       method of the specified sensor driver package
        :param frequency: Polling frequency for the measurement
        :param axis: List of parameters to be polled from the sensor
        :returns: True
        :rtype: Boolean

        """
        if sensorname in self.sensors:
            raise xmlrpclib.Fault(
                1, 'Sensor "{}" already exists!'.format(sensorname))

        try:
            sensor = sensorbuilder.createSensor(sensor_type=sensortype, **config)
            self.measurement_processes[sensorname] = MeasureProcess(
                sensor, sensorname, config, frequency,
                axis, self.data_directory)
            self.sensors[sensorname] = {
                "sensortype" : sensortype,
                "configuration": config,
                "frequency": frequency,
                "axis": axis,
                "measuring": False,
                "stream": "",
                "sensor": sensor
            }
        except Exception as e:
            #print e
            raise e

        return True

    def remove_sensor(self, sensorname):
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

    def update_sensor(self, sensorname, config):
        """FIXME: This function updates the configuration of a given sensor.

        :param sensorname: String identifying the sensor
        :param config: Dictionary of changes configuration parameters.
                       Each key value pair is passed to the sensor's
                       updateConfiguration()
        :returns: True
        :rtype: Boolean

        """
        if sensorname not in self.sensors:
            raise xmlrpclib.Fault(
                1, 'Sensor "{}" does not exist'.format(sensorname))
        self.sensors[sensorname]["configuration"].update(config)
        return True

    def get_system_date(self):
        """This function returns a string representation of the current system time.

        :returns: String of current datetime
        :rtype: String

        """
        return str(datetime.datetime.now())

    def set_system_date(self, date):
        """This function sets the current system date.
        NOTICE: This function does not modify any modified realtime clock!

        :param date: String of date.
                     The parameter is passed to the system's date operation
                     thus accepts its format strings. Please refer to the Linux
                     manual page date(1).
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

    def set_extra(self, extra={}):
        """This function is reserved for future usage.

        :param extra: Dictionary
        :returns: True
        :rtype: Boolean

        """
        return True

    def get_extra(self, extra):
        """This function is reserved for future usage

        :param extra: Dictionary
        :returns: True
        :rtype: Boolean

        """
        return {}

    def clear_sensors(self):
        """This function removes all configured sensors from the current setup.

        :returns: True
        :rtype: Boolean

        """
        self.sensors = {}
        return True

    def _sanitize_path(self, root, path):
        """This function checks if the path is under the root directory.

        :param root: root directory under where the path should reside
        :param path: path to be checked
        :returns: normalized path relative to the root directory
        :rtype: path
        """
        request_path = os.path.join(root, path)
        normalized_path = os.path.normpath(request_path)
        if not os.path.commonprefix([normalized_path, root]) == root:
            raise RaspyreDirectoryInvalid("Requested path is not under the data directory")
        return normalized_path

    def configuration_save(self, sensorname, path):
        """This function saves the configuration state of a sensor.

        :param sensorname: String of sensor name
        :param path: Path relative to the configuration directory
        :returns: True
        :rtype: Boolean

        """
        if sensorname not in self.sensors:
            raise xmlrpclib.Fault(
                1, 'Sensor "{}" is not registered in the sensor list'.format(
                    sensorname))

        state = {}
        state['configuration'] = self.sensors[sensorname].dump()
        state['frequency'] = self.sensors[sensorname]['configuration']
        state['axis'] = self.sensors[sensorname]['axis']

        filepath = self._sanitize_path(self.configuration_directory, path)
        with open(filepath, 'w') as fp:
            json.dump(state, fp)

    def configuration_restore(self, sensorname, path):
        """This function restores a sensor from a given configuration file.

        :param sensorname: Unique String identifying the sensor
        :param path: File path relative to the configuration_directory
        :returns: True
        :rtype: Boolean

        """
        filepath = self._sanitize_path(self.configuration_directory, path)

        state = None
        with open(filepath, 'r') as fp:
            state = json.load(fp)
        self.add_sensor(sensorname, state['configuration'], state['frequency'],
                        state['axis'])
        return True

    def fs_ls(self, path='.'):
        """This function lists the contents of the data storage directory.
        It returns a list of 2 lists. The first list contains directories
        of the queried path, the second list contains the file names.

        :param path: path to be queried relative to the data directory
        :returns: list of 2 lists with [[directories], [files]]
        :rtype: list of lists

        """
        normalized_path = self._sanitize_path(self.data_directory, path)
        if not os.path.exists(normalized_path):
            raise RaspyreDirectoryNotFound("Requested path was not found")
        # take one filesystem walk of the top level
        first_level_walk = os.walk(normalized_path)
        _, dirnames, filenames = first_level_walk.next()
        return [dirnames, filenames]

    def fs_mkdir(self, path):
        """This function creates a directory in the specified path below
        the data storage directory.

        :param path: Path relative to the data directory
        :returns: True
        :rtype: Boolean

        """
        normalized_path = self._sanitize_path(self.data_directory, path)
        os.mkdir(normalized_path)
        return True

    def fs_rmdir(self, path, recursive=False):
        """This function removes a directory relative to the data storage

        :param path: Path relative to the data directory
                     - not the data directory itself
        :param recursive: Boolean flag indicating recursive deletion
        :returns: True
        :rtype: Boolean

        """
        normalized_path = self._sanitize_path(self.data_directory, path)
        if normalized_path == os.path.normpath(self.data_directory):
            raise RaspyreDirectoryInvalid("Cannot delete data directory root.")
        if not os.path.exists(normalized_path):
            raise RaspyreDirectoryNotFound("Path is not a directory")
        if recursive is False:
            os.rmdir(normalized_path)
        else:
            shutil.rmtree(normalized_path)

    def fs_rm(self, path):
        """This function removes the specified file from the file system.

        :param path: Path relative to the data directory
        :returns: True
        :rtype: Boolean

        """
        normalized_path = self._sanitize_path(self.data_directory, path)
        if not os.path.isfile(normalized_path):
            raise RaspyreFileInvalid("File does not exist")
        if os.path.isdir(normalized_path):
            raise RaspyreFileInvalid("Specified path is a directory, not a file")
        os.remove(normalized_path)
        return True

    def fs_mv(self, src, dst):
        """This function renames src to dst.
        If dst is a directory an error will be raised. If dst is a file, it will
        be silently replaced.

        :param src: Path relative to the data directory
        :param dst: Path relative to the data directory
        :returns: True
        :rtype: Boolean

        """
        normalized_src = self._sanitize_path(self.data_directory, src)
        normalized_dst = self._sanitize_path(self.data_directory, dst)
        os.rename(normalized_src, normalized_dst)
        return True

    def fs_stat(self, path):
        """This function returns the POSIX information of a stat system call.
        Please refer to :py:func:`~os.stat`

        :param path: Path relative to the data directory
        :returns: True
        :rtype: Boolean

        """
        normalized_path = self._sanitize_path(self.data_directory, path)
        os.stat(normalized_path)
        return True
