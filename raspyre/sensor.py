
class Sensor(object):
    """Base class for all concrete sensor implementations.

    The derived classes have to call the base class constructor at the
    beginning of their own constructor.
    This is minimal interface the derived classes have to implement to comply
    with the frameworks requirements. Further expansion of the interface may
    be used to add functionality for special uses, but may not be used for the
    basic functionality.

    .. note::
        Each derived class must provide a class variable :py:attr:`sensor_attributes` that
        maps attribute strings to a datatype format character.

        Example: A class for a sensor with attributes for 2 acceleration axes of type double
        and one temperature field of type integer would need to provide the
        :py:attr:`sensor_attributes` as follows::

            sensor_attributes = { 'acceleration_1': 'd', 'acceleration_2': 'd', 'temperature': 'i' }

        .. seealso::

            :python:ref:`format-characters`
    """

    sensor_attributes = {}

    def getAttributes(self):
        return self.sensor_attributes.keys()

    def getRecord(self, *args):
        """ Returns a Record object containing the requested values.
        The Parameters to the function specify the attributes that will be measured.
        """
        raise NotImplementedError('getRecord called on base class')

    def updateConfig(self, **kwargs):
        """Pass a list of parameter names and values.
        The parameters of the sensor will be changed accordingly
        """
        raise NotImplementedError('updateConfig called on base class')

    def getConfig(self):
        """Returns a dictionary of all configuration parameters the sensor has with their values.
        """
        raise NotImplementedError('getConfig called on base class')

    def struct_fmt(self, attributes):
        """Returns a struct format string representing the datatypes of the attributes parameter.

        :param attributes: a list of a subset of the sensor's :py:attr:`sensor_attributes`
        :type attributes: list of strings
        :returns: a lift of format characters
        :rtype: list of characters

        :Example:

        >>> from raspyre.sensors.mockup.mockup import Mockup
        >>> sensor = Mockup(sps=100)
        >>> sensor.struct_fmt(['y', 'x'])
        ['d', 'd']

        .. seealso::

            :python:ref:`struct-format-strings`
        """
        return [self.sensor_attributes[x][1] for x in attributes]
        return fmt

    def units(self, attributes):
        return [self.sensor_attributes[x][0] for x in attributes]

