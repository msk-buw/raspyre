'''
This module provides the functionality to read and write data files.
Supported for reading are all (including old) binary and csv formats,
whereas for writing, we only support the newest binary and csv
formats.

Also the functionality to resample data is included. Goal is to reduce
the size of the stored data for longterm measurements. The following
levels are available and can be derived from the file extension:

Level   Interval        Blocksize
----------------------------------
rm01    sampling rate   variable
rm02    1 second        1 hour
rm03    1 second        1 day
rm04    1 minute        1 day
rm05    1 minute        1 week
rm06    1 minute        1 month
rm07    1 hour          1 month

The filename consists of a descriptive name, the timestamp for the
beginning of the file and the file extension that specifies the level
of sampling. The file contains a timestamp as the first column
followed by a number of value columns. The firs line of the file
contains the name of the columns.
'''

import os
import struct
import datetime
import csv
import io
import logging

MAGIC_ID_BYTES = [0xEB, 0xFF]
TIME_FORMAT = "%Y-%m-%d %H:%M:%S"


class RaspyreFileFormatException(Exception):
    pass


def process_files(in_folder, out_folder, level):
    """
    This function processes all the files in the in_folder such that
    it resamples them to the required sampling rate and stores them in
    the according blocksize in new files in the out_foler. It has the
    ability to see, which data has already been resampled, so that it
    can be called multiple times with the same arguments and only
    updates the new data.
    """
    raise NotImplementedError


def getReader(filename):
    try:
        with open(filename, 'rb') as f:
            magic = f.read(2)
    except:
        raise
    if magic == b'\xeb\xff':
        reader = BinReader(filename)
    else:
        reader = CSVReader(filename)
    return reader


class Reader(object):
    def __init__(self, filename):
        self.filename = filename


class CSVReader(Reader):
    def __init__(self, filename):
        Reader.__init__(self, filename)
        self.binary = False
        self.f = open(filename)
        version_line = self.f.readline()
        if version_line.startswith("# RaspyreFile 0.1"):
            logger = logging.getLogger(__name__)
            logger.info("File with deprecated format")
        elif not version_line.startswith("# RaspyreFile"):
            raise RaspyreFileFormatException(
                "File is not a valid Raspyre file")
        version_line = cleanCSVLine(version_line)
        version_string = version_line.split()[1]
        (major_version, minor_version) = version_string.split(".")
        self.version = (int(major_version), int(minor_version))

        #parse the header with regard to the version number
        self.delimiter = " "
        self.parseHeader()

        self.reader = csv.reader(self.f, delimiter=self.delimiter)

    def data(self):
        """returns a generator for all the data rows in the csv file.
       :returns: tuple -- the parsed values from the data row 
        """
        if self.f.closed:
            raise
        datatypes = self.header["datatypes"]
        for row in self.reader:
            data = []
            for value, datatype in zip(row, datatypes):
                if datatype in ["f", "d"]:
                    data.append(float(value))
                elif datatype == "i":
                    data.append(int(value))
                elif datatype == "B":
                    data.append(bool(int(value)))
            yield tuple(data)
        self.f.close()

    def _getNextLine(self):
        l = cleanCSVLine(self.f.readline())
        while not l:
            l = cleanCSVLine(self.f.readline())
        return l

    def parseHeader(self):
        """parses a CSV header, assuming all lines starting with #<space>
        currently supported versions: 0.1
        """

        major_version, minor_version = self.version
        if major_version == 0 and minor_version == 1:
            """
            parser for version 0.1
            header names and types are:
            time: float
            metadata: list of strings
            datatypes: string of datatype chars
            units: list of unit strings
            columns: list of column name strings
            data column delimiter: ;<space>
            """
            self.delimiter = ";"
            header = {}
            timeline = self._getNextLine()
            if not timeline.lower().startswith("time "):
                raise RaspyreFileFormatException(
                    "No file creation time specified")
            try:
                time_float = float(timeline[5:])
                datetime.datetime.utcfromtimestamp(float(timeline[5:]))
                header['time'] = time_float
            except ValueError:
                raise RaspyreFileFormatException("Invalid timestamp given")

            metaline = self._getNextLine()
            header["metadata"] = {}
            while not metaline.lower().startswith("datatypes "):
                key, value = metaline.split(" ", 1)
                header["metadata"][key] = value
                metaline = self._getNextLine()

            datatypes = metaline.split()[1]
            try:
                valid_format_string = struct.calcsize(datatypes)
            except struct.error:
                raise RaspyreFileFormatException("Invalid datatypes")
            header["datatypes"] = datatypes

            unitline = self._getNextLine()
            if not unitline.lower().startswith("units "):
                raise RaspyreFileFormatException(
                    "No unit definition specified")
            header["units"] = unitline[6:].split()

            columnline = self._getNextLine()
            if not columnline.lower().startswith("columns "):
                raise RaspyreFileFormatException(
                    "No column definition specified")
            header["columns"] = columnline[8:].split()

            self.header = header

        elif major_version == 0 and minor_version == 2:
            # parser for version 0.2
            # header names and types are:
            # created: float
            # metadata: list of strings
            # datatypes: string of datatype chars
            # units: list of unit strings
            # columns: list of column name strings
            # data column delimiter: <space>
            self.delimiter = " "
            header = {}
            timeline = self._getNextLine()
            if not timeline.startswith("created "):
                raise RaspyreFileFormatException(
                    "No file creation time specified")
            try:
                time_float = float(timeline.split()[1])
                d = datetime.datetime.utcfromtimestamp(float(time_float))
                header['time'] = time_float
            except ValueError:
                raise RaspyreFileFormatException("Invalid timestamp given")

            metaline = self._getNextLine()
            header["metadata"] = {}
            while not metaline.startswith("datatypes "):
                key, value = metaline.split(" ", 1)
                value = value.strip('"')
                header["metadata"][key] = value
                metaline = self._getNextLine()

            datatypes = metaline.split()[1]
            try:
                valid_format_string = struct.calcsize(datatypes)
            except struct.error:
                raise RaspyreFileFormatException("Invalid datatypes")
            header["datatypes"] = datatypes

            unitline = self._getNextLine()
            if not unitline.startswith("units "):
                raise RaspyreFileFormatException(
                    "No unit definition specified")
            header["units"] = unitline[6:].split()

            columnline = self._getNextLine()
            if not columnline.startswith("columns "):
                raise RaspyreFileFormatException(
                    "No column definition specified")
            header["columns"] = columnline[8:].split()

            self.header = header
        else:
            raise RaspyreFileFormatException(
                "Unknown file format version {}.{}".format(
                    major_version, minor_version))


class BinReader(Reader):
    def __init__(self, filename):
        Reader.__init__(self, filename)
        self.binary = True

        self.f = open(filename, 'rb')
        magic_bytes = self.f.read(2)
        if not (magic_bytes[0] == b'\xeb' and magic_bytes[1] == b'\xff'):
            raise RaspyreFileFormatException(
                "Magic bytes not found in binary file")
        version_bytes = self.f.read(2)
        self.version = struct.unpack('BB', version_bytes)

        self.parseHeader()

    def data(self):
        while True:
            data_bytes = self.f.read(self.chunksize)
            if data_bytes:
                yield struct.unpack(self.header['datatypes'], data_bytes)
            else:
                break
        self.f.close()

    def parseHeader(self):
        header = {}
        if self.version == (0, 4):
            """
            Parser for version 0.4
            """
            try:
                time_bytes = self.f.read(8)
                time_float = struct.unpack('d', time_bytes)
                datetime.datetime.utcfromtimestamp(time_float[0])
                header['time'] = time_float[0]
            except:
                raise RaspyreFileFormatException(
                    "Invalid date format specified")

            len_metadata = struct.unpack('i', self.f.read(4))[0]
            len_types = struct.unpack('i', self.f.read(4))[0]
            len_units = struct.unpack('i', self.f.read(4))[0]
            len_column_names = struct.unpack('i', self.f.read(4))[0]

            try:
                meta_bytes = self.f.read(len_metadata)
                meta_data = struct.unpack('{}s'.format(len_metadata),
                                          meta_bytes)[0]
                meta_lines = meta_data.split('\r\n')
                header['metadata'] = {}
                for line in meta_lines:
                    if line:
                        key, value = line.split(" ", 1)
                        header['metadata'][key] = value
            except:
                raise RaspyreFileFormatException("Error in metadata string")

            header['datatypes'] = self.f.read(len_types)
            try:
                self.chunksize = struct.calcsize(header['datatypes'])
            except:
                raise RaspyreFileFormatException("Invalid datatypes")

            header['units'] = self.f.read(len_units).split()

            header['columns'] = self.f.read(len_column_names).split()

        else:
            raise RaspyreFileFormatException(
                "Unknown file format version {}.{}".format(*self.version))
        self.header = header


def cleanCSVLine(line):
    """cleans a CSV header line from leading # and whitespaces and
    trailing \n and whitespaces used for header parsing :param line:
    string to be cleaned
    """
    if not line.startswith("#"):
        raise RaspyreFileFormatException(
            "Invalid data in CSV Header: {}".format(line))
    line = line.strip("#")
    line = line.strip()
    return line


class Writer(object):
    # TODO: this class should implement the Context Manager Interface
    def __init__(self, filename, binary=True):
        self.filename = filename
        self.binary = binary
        self.f = open(filename, "w")

    def writeHeader(self, header):
        meta = header['metadata']
        fmt = header['datatypes']
        self.fmt = fmt
        units = header['units']
        column_names = header['columns']
        date = header['time']
        if self.binary:
            header_string = build_binary_header(date, meta, fmt, units,
                                                column_names)
        else:
            header_string = build_csv_header(date, meta, fmt, units,
                                             column_names)
        self.f.write(header_string)

    def writeRow(self, row):
        if self.binary:
            self.f.write(struct.pack(self.fmt, *row))
        else:
            self.f.write(" ".join(["{:.19f}".format(val)
                                   for val in row]) + "\r\n")

    def close(self):
        self.f.close()


def build_binary_header(date_float, metadata, fmt, units, column_names):
    (MAJOR_VERSION, MINOR_VERSION) = (0, 4)
    byte_buffer = io.BytesIO()
    byte_buffer.write(struct.pack('2B', *MAGIC_ID_BYTES))
    byte_buffer.write(struct.pack('2B', MAJOR_VERSION, MINOR_VERSION))
    byte_buffer.write(struct.pack('d', date_float))
    metadatastring = "\r\n".join([
        key + " " + str(value) for key, value in metadata.items()
    ])  # TODO: does the string concat explode?
    metadatasize = len(metadatastring)
    fmt_size = len(fmt)
    column_names_line = " ".join(column_names)
    column_names_size = len(column_names_line)
    units_line = " ".join(units)
    units_size = len(units_line)
    # write size of metadatastring
    byte_buffer.write(struct.pack('i', metadatasize))
    # write size of fmt
    byte_buffer.write(struct.pack('i', fmt_size))
    # write size of units
    byte_buffer.write(struct.pack('i', units_size))
    # write size of column_names
    byte_buffer.write(struct.pack('i', column_names_size))
    # write actual metadatastring
    byte_buffer.write(metadatastring)
    # write fmt
    byte_buffer.write(fmt)
    # write units_line
    byte_buffer.write(units_line)
    # write column names
    byte_buffer.write(column_names_line)
    # header finished
    byte_buffer.seek(0)
    return byte_buffer.read()


def build_csv_header(date, metadata, fmt, units, column_names):
    """build csv header for the file writer version 0.2
    """
    (MAJOR_VERSION, MINOR_VERSION) = (0, 2)
    out = ""
    out += "# RaspyreFileCSV {}.{}\n".format(MAJOR_VERSION, MINOR_VERSION)
    out += "# created {:6f}\n".format(date)
    for key, value in metadata.items():
        out += '# {} "{}"\n'.format(key, value)
    out += "# datatypes {}\n".format(fmt)
    out += "# units {}\n".format(" ".join(units))
    out += "# columns {}\n".format(" ".join(column_names))
    return out
