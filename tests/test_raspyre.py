from raspyre import sensorbuilder as sb
from raspyre.sensor import Sensor
import pytest

class TestSensor(Sensor):
    sensor_attributes = { 'att1': ('m/s^2', 'd'),
                            'att2': ('s', 'i'),
                            'att3': ('C', 'f'),
                            'att4': ('g', 'd')}

def test_sensorbuilder():
    sb_built_sensor = sb.createSensor(sensor_type="mockup", sps=100)
    assert 1 == 1

def test_sensor_abstract_methods():
    sensor = Sensor()
    attributes = sensor.getAttributes()
    assert attributes == []

    with pytest.raises(NotImplementedError):
        sensor.getConfig()
    with pytest.raises(NotImplementedError):
        sensor.getRecord(['att1', 'att2'])
    with pytest.raises(NotImplementedError):
        sensor.updateConfig(foo='bar')

def test_sensor_struct_fmt():
    test_sensor = TestSensor()
    fmt1 = test_sensor.struct_fmt(['att2', 'att4', 'att3'])
    assert fmt1 == ['i', 'd', 'f']

    with pytest.raises(KeyError):
        fmt = test_sensor.struct_fmt(['att1', 'att2', 'att_not_in_sensor_attributes'])

def test_sensor_units():
    test_sensor = TestSensor()
    units = test_sensor.units(['att2', 'att4', 'att3'])
    assert units == ['s', 'g', 'C']
