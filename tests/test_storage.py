from raspyre import storage
import pytest
from mock import mock_open, patch
import struct


def setup_module(storage):
    import os
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

def test_csv_reader_constructor():
    # test instatiating a reader with a not existing file
    with pytest.raises(IOError):
        reader = storage.getReader("storage_tests/doesnotexist.rm01")


    reader = storage.getReader("storage_tests/csv.rm01")
    assert type(reader) == storage.CSVReader
    assert reader.filename == "storage_tests/csv.rm01"

@pytest.fixture
def binary_reader():
    reader = storage.BinReader('storage_tests/binary.rm01') # TODO: move filenames to path agnostic method 
    return reader

@pytest.fixture
def csv_reader():
    reader = storage.CSVReader('storage_tests/csv.rm01')
    return reader

@pytest.fixture
def binary_data():
    magic_bytes = b'\xeb\xff'
    version_bytes = struct.pack('BB', 0, 4)
    data = [magic_bytes,version_bytes]
    return data

def test_binary_magic(binary_data):
    m = mock_open(read_data=binary_data)
    with pytest.raises(IOError):
        reader = storage.BinReader('invalid_filename')

''' valid binary file missing
def test_binary_header(binary_reader):
    # header = """# RaspyreFile 0.0.1
    # # Time 2017-02-24 17:23:28
    # # Testing Platform
    # # Sample values
    # # time, accx, accy
    # # dt64, m/s^2, m/s^2"""

    header = {'version': '0.0.1', 'time': 1487953408.194, 'metadata': ['Testing Dataset', 'Synthetic dataset']} 
    #assert binary_reader.header == header

    columns = ('time', 'accx', 'accy')
    #assert binary_reader.columns == columns

    datatypes = ('dt64', 'm/s^2', 'm/s^2')
    #assert binary_reader.types == datatypes
#def test_headers():
#    headertest(reader)
#
#    reader = storage.getReader('tests/csv.r01')
#    headertest(reader)


def test_bin_reader_constructor():
    # test instatiating a reader with a not existing file
    with pytest.raises(IOError):
        reader = storage.getReader("tests/doesnotexist.bm01")

    with pytest.raises(storage.RaspyreFileFormatException):
        reader = storage.getReader("tests/wrongfiletype.txt")


    reader = storage.getReader("tests/binary.rm01")
    assert type(reader) == storage.BinReader
    assert reader.filename == "tests/binary.rm01"

'''

# def test_converters():
#     #test that the conversion is bijective
#     import time
#     import random
#     filename = "tests/temp.bin"
#     now = time.time()
#     meta = {"first row": "some numbers 123456", "SECOND row": "SomE mixed cases"}
#     fmt = "ddd"
#     units = ["dt64[s]", "g", "C"]
#     columns = ["time", "accx", "temperature"]
#     header = {"time": now, "metadata": meta, "datatypes": fmt, "units": units, "columns": columns}
#     writer = storage.Writer(filename, binary=True)
#     writer.writeHeader(header)
#     for i in range(100):
#         t = time.time()
#         accx = random.random()
#         temp = 10*random.random()
#         writer.writeRow((t, accx, temp))
#     writer.close()
#     from raspyre import converter
#     newfile = "tests/temp.csv"
#     finalfile = "tests/final.bin"
#     finalcsvfile = "tests/final.csv"
#     converter.main(filename, newfile)
#     converter.main(newfile, finalfile)
#     converter.main(finalfile, None)
#     import filecmp
#     assert filecmp.cmp(filename, finalfile)
#     assert filecmp.cmp(newfile, finalcsvfile)
#     assert not filecmp.cmp(filename, newfile)
#     import os
#     os.remove(filename)
#     os.remove(newfile)
#     os.remove(finalfile)
    # os.remove(finalcsvfile)

