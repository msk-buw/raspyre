"""This module implements the functions exposed by the Rapsyre RPC interface.

The functions are grouped in classes and should be invoked into different
prefix namespaces.
e.g.:
class MeasurementHandler consists of functions to handle the Measurement
Processes of the Pi's GPIO interface and should reside in a namespace 
that identifies this behaviour as such.
"""

from .pollingprocess import PollingProcess
from .handler import HandlerProcess
from .blink import BlinkProcess
from raspyre import sensorbuilder

import sys
if sys.version_info[0] == 3:
    import xmlrpc.server as xmlrpclib
else:
    import xmlrpclib
import logging
import os
import subprocess
import shutil
#import subprocess
import datetime
import json
import traceback
import mmap

import socket
import fcntl
import struct


import python_hosts
import netifaces

logger = logging.getLogger(__name__)

import socket
import fcntl
import struct

class IPContextFilter(logging.Filter):
    def __init__(self):
        self.ip_address = get_ip_address('mesh0') 
    def filter(self, record):
        record.ip = self.ip_address
        return True

def get_ip_address(ifname):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    return socket.inet_ntoa(fcntl.ioctl(
        s.fileno(),
        0x8915,  # SIOCGIFADDR
        struct.pack('256s', bytes(ifname[:15], 'utf-8'))
    )[20:24])


class RaspyreDirectoryNotFound(Exception):
    pass

class RaspyreDirectoryInvalid(Exception):
    pass

class RaspyreFileInvalid(Exception):
    pass



class RaspyreService(object):
    PROCESS_TIMEOUT = 3

    def __init__(self, data_directory, configuration_directory):
        self.sensors = {}
        self.polling_processes = {}
        self.handler_processes = {}
        self.buffer_size = mmap.PAGESIZE * 100
        self.data_directory = os.path.normpath(data_directory)
        self.configuration_directory = os.path.normpath(configuration_directory)
        self.sensor_count = 0
        
        self.is_ntp_master = False

        self.blink_process = None
        self.is_blinking = False

        self.socketHandler = None
        self.ip_addr = get_ip_address('mesh0') 
        
        logger.debug("Initialized RaspyreService")

    def ping(self):
        """This function simply returns True.
        It is used as simple connectivity checking function.

        :returns: True
        :rtype: Boolean

        """
        logger.debug("ping() called")
        return True


    def start_blink(self):
        logger.debug("start_blink() called")
        self.is_blinking = True
        if self.blink_process is None:
            self.blink_process = BlinkProcess()
            self.blink_process.start()
            return True
        else:
            return False

    def stop_blink(self):
        logger.debug("stop_blink() called")
        self.is_blinking = False
        if self.blink_process is not None:
            self.blink_process.terminate()
            self.blink_process.join(self.PROCESS_TIMEOUT)
            self.blink_process = None
            return True
        else:
            return False

    def toggle_blink(self):
        if not self.is_blinking:
            self.start_blink()
        else:
            self.stop_blink()
        return True

    def start_ntp(self):
        #rt = os.system('sudo systemctl start ntp.service &')
        #return rt
        subprocess.Popen(['sudo', '/bin/systemctl', 'start', 'ntp.service'])
        return True

    def stop_ntp(self):
        #rt = os.system('sudo systemctl stop ntp.service &')
        subprocess.Popen(['sudo', '/bin/systemctl', 'stop', 'ntp.service'])
        return True

    def ntp_sync(self):
        #rt = os.system('sudo ntpd -q -g &')
        subprocess.Popen(['sudo', 'ntpd', '-g', '-q'])
        return True

    def ntp_set_server(self, ip_str):
        with open('/etc/ntp.conf', 'w') as ntpfile:
            ntpfile.write('driftfile /var/lib/ntp/ntp.drift\n')
            ntpfile.write('statsdir /var/log/ntpstats/\n')
            ntpfile.write('statistics loopstats peerstats clockstats\n')
            ntpfile.write('filegen loopstats file loopstats type day enable\n')
            ntpfile.write('filegen peerstats file peerstats type day enable\n')
            ntpfile.write('filegen clockstats file clockstats type day enable\n')
            ntpfile.write('server {} minpoll 3 maxpoll 5 iburst prefer\n'.format(ip_str))
            ntpfile.write('restrict -4 default kod notrap nomodify nopeer noquery\n')
            ntpfile.write('restrict 10.0.0.0 mask 255.0.0.0 nomodify notrap\n')
            ntpfile.write('restrict 127.0.0.1\n')
        self.is_ntp_master = False
        subprocess.Popen(['sudo', '/bin/systemctl', 'restart', 'ntp.service'])
        return True

    def ntp_master(self):
        with open('/etc/ntp.conf', 'w') as ntpfile:
            ntpfile.write('driftfile /var/lib/ntp/ntp.drift\n')
            ntpfile.write('statsdir /var/log/ntpstats/\n')
            ntpfile.write('statistics loopstats peerstats clockstats\n')
            ntpfile.write('filegen loopstats file loopstats type day enable\n')
            ntpfile.write('filegen peerstats file peerstats type day enable\n')
            ntpfile.write('filegen clockstats file clockstats type day enable\n')
            ntpfile.write('server 127.127.1.0 prefer\n')
            ntpfile.write('restrict -4 default kod notrap nomodify nopeer noquery\n')
            ntpfile.write('restrict 10.0.0.0 mask 255.0.0.0 nomodify notrap\n')
            ntpfile.write('restrict 127.0.0.1\n')
        self.is_ntp_master = True
        subprocess.Popen(['sudo', '/bin/systemctl', 'restart', 'ntp.service'])
        return True

    def get_dns_info(self):
        hosts = python_hosts.Hosts(path='/tmp/hosts.olsr')
        if len(hosts.entries) > 0:
            raspyre_hosts = { entry.names[0]:entry.address for entry in hosts.entries if entry.entry_type == 'ipv4' and entry.address.startswith('10')}
            return raspyre_hosts
        else:
            return False

    def start_measurement(self, measurementname, sensornames=None):
        """This function starts a measurement process for the specified sensors.

        :param measurementname: String describing the measurement
        :param sensornames: None [all sensors],
                            String [one specific sensor],
                            List of Strings (optional)
        :returns: True
        :rtype: Boolean

        """
        try:
            logger.debug("start_measurement() called")
            sensorlist = []
            #import pdb; pdb.set_trace()
            if sensornames is None:  # start all sensors
                sensorlist = list(self.sensors.keys())
            elif isinstance(sensornames, str):
                sensorlist = [sensornames]
            else:
                sensorlist = sensornames
            if not self.sensors:
                raise xmlrpclib.Fault(1, 'No sensors have been configured!')

            logger.debug("Trying to start measurement.")

            for sensorname in sensorlist:
                if sensorname not in self.sensors:
                    raise xmlrpclib.Fault(
                        1,
                        'Sensor "{}" is not in the sensorlist'.format(sensorname))
                else:

                    #self.polling_processes[sensorname].setMeasurementName(
                    #    measurementname)
                    self.handler_processes[sensorname].setMeasurementName(measurementname)
                    logger.debug("measurement name set")
                    self.polling_processes[sensorname].start()
                    logger.debug("started polling process")
                    self.handler_processes[sensorname].start()
                    logger.debug("started handler process")
                    self.sensors[sensorname]["measuring"] = True
        except Exception as e:
            logger.error("Exception occured during start_measurement()")
            logger.error("Traceback:")
            logger.error(traceback.format_exc())
            return False
        return True


    def stop_measurement(self, sensornames=None):
        """This function stops a currently running measurement.

        :param sensornames: None [all sensors],
                            String [one specific sensor],
                            List of Strings (optional)
        :returns: True
        :rtype: Boolean

        """
        #import pdb; pdb.set_trace()
        try:
            sensorlist = []
            if sensornames is None:  # start all sensors
                sensorlist = list(self.sensors.keys())
            elif isinstance(sensornames, str):
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
                    logger.debug("terminating handler process")
                    if self.handler_processes[sensorname].is_alive():
                        self.handler_processes[sensorname].shutdown()
                        self.handler_processes[sensorname].join(self.PROCESS_TIMEOUT)
                        self.handler_processes[sensorname].terminate()
                        self.sensor_count -= 1
                        self.handler_processes[sensorname] = 0

                    logger.debug("terminating polling process")
                    if self.polling_processes[sensorname].is_alive():
                        self.polling_processes[sensorname].shutdown()
                        self.polling_processes[sensorname].join(self.PROCESS_TIMEOUT)
                        self.polling_processes[sensorname].terminate()
                        self.polling_processes[sensorname] = -1

                        logger.debug("subprocesses successfully terminated")

                        mmap_file = '/dev/shm/raspyre_buf' + str(self.sensor_count)
                        self.polling_processes[sensorname] = PollingProcess(
                            sensor=self.sensors[sensorname]['sensor'],
                            sensor_name=sensorname,
                            config=self.sensors[sensorname]['configuration'],
                            frequency=self.sensors[sensorname]['frequency'],
                            axis=self.sensors[sensorname]['axis'],
                            data_dir=self.data_directory,
                            mmap_file=mmap_file,
                            buffer_size=self.buffer_size)
                        self.handler_processes[sensorname] = HandlerProcess(
                            sensor=self.sensors[sensorname]['sensor'],
                            sensor_name=sensorname,
                            config=self.sensors[sensorname]['configuration'],
                            frequency=self.sensors[sensorname]['frequency'],
                            axis=self.sensors[sensorname]['axis'],
                            data_dir=self.data_directory,
                            mmap_file=mmap_file,
                            buffer_size=self.buffer_size,
                        )

                    self.sensors[sensorname]["measuring"] = False

        except Exception as e:
            logger.error("Exception occured during start_measurement()")
            logger.error("Traceback:")
            logger.error(traceback.format_exc())
            return False
        return True
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

    def get_status(self):
        # collect status information about this node
        is_portal = False
        if 'ap0' in netifaces.interfaces():
            is_portal = True
        is_ntp_master = self.is_ntp_master
        sensors = {}
        for sensorname, sensor in self.sensors.items():
            # extract relevant information out of sensor dictionary
            sensors[sensorname] = {k : sensor[k] for k in ('sensortype', 'configuration', 'frequency', 'axis', 'measuring', 'zmq_port')}
        ret =  {"is_portal":is_portal,
                "is_ntp_master":is_ntp_master,
                "ip_addr":self.ip_addr,
                "sensors":sensors}
        return ret
        

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

        logger.debug('add_sensor() called')
        if sensorname in self.sensors:
            logger.error('Sensor "{}" already exists.'.format(sensorname))
            raise xmlrpclib.Fault(
                1, 'Sensor "{}" already exists!'.format(sensorname))

        try:
            sensor = sensorbuilder.createSensor(sensor_type=sensortype, **config)
            logger.debug("Successfully instantiated sensor")

            mmap_file = '/dev/shm/raspyre_buf' + str(self.sensor_count)
            self.polling_processes[sensorname] = PollingProcess(
                sensor=sensor,
                sensor_name=sensorname,
                config=config,
                frequency=frequency,
                axis=axis,
                data_dir=self.data_directory,
                mmap_file=mmap_file,
                buffer_size=self.buffer_size)
            self.handler_processes[sensorname] = HandlerProcess(
                sensor=sensor,
                sensor_name=sensorname,
                config=config,
                frequency=frequency,
                axis=axis,
                data_dir=self.data_directory,
                mmap_file=mmap_file,
                buffer_size=self.buffer_size,
            )
            self.sensors[sensorname] = {
                "sensortype": sensortype,
                "configuration": config,
                "frequency": frequency,
                "axis": axis,
                "measuring": False,
                "stream": "",
                "sensor": sensor,
                "mmap_file": mmap_file,
                "zmq_port": self.sensor_count + 1
            }
            self.sensor_count += 1
            logger.debug("Successfully instantiated polling process")
            
        except Exception as e:
            #print e
            logger.error("Exception occured during add_sensor()")
            logger.error(e)
            logger.error("Traceback:")
            logger.error(traceback.format_exc())
            raise e

        return True

    def remove_sensor(self, sensorname):
        """Removes the sensor specified by its name from the current setup.

        :param sensorname: String identifying sensor
        :returns: True
        :rtype: Boolean

        """
        if sensorname is None:
            self.sensors = {}
            self.polling_processes = {}
            self.handler_processes = {}
        if sensorname not in self.sensors:
            raise xmlrpclib.Fault(
                1, 'Sensor "{}" does not exist'.format(sensorname))
        del self.sensors[sensorname]
        del self.polling_processes[sensorname]
        del self.handler_processes[sensorname]
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
        _, dirnames, filenames = next(first_level_walk)
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

    def set_network_logger(self, host, loglevel=logging.DEBUG):
        rootLogger = logging.getLogger('')
        f = IPContextFilter()
        #rootLogger.addFilter(f)
        #logger.addFilter(f)
        rootLogger.setLevel(loglevel)

        # remove previously configured socket handler
        if self.socketHandler is not None:
            rootLogger.removeHandler(self.socketHandler)

        self.socketHandler = logging.handlers.SocketHandler(host,
                logging.handlers.DEFAULT_TCP_LOGGING_PORT)
        self.socketHandler.addFilter(f)
        rootLogger.addHandler(self.socketHandler)
        logger.debug("Set up network logging handler successfull to host {}".format(host))

        return True

    def debug_log_msg(self):
        logger.debug("test debug log msg")
        logger.info("test info log msg")
        logger.warn("test warn log msg")
        logger.critical("test critical log msg")
        logger.error("test error log msg")

        return True


