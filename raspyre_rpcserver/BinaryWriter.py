import io
import struct
import arrow
import csv

MAGIC_ID_BYTES = [0xEB, 0xFF]
MAJOR_VERSION = 0
MINOR_VERSION = 4

date_float = arrow.utcnow().float_timestamp
example_metadata = {
    "devicename": "Raspberry Pi 2 Model B",
    "version": "0.5",
    "axis": "attr1, attr2, attr3",
    "frequency": "100",
    "type": "permanent",
    "time": "indefinite",
    "sensors": "2",
    "vendor": "mpu6050",
    "name": "mpu6050",
    "delay": "0",
    "range": "0",
    "resolution": "0",
    "power": "0"
}

metadata = example_metadata

column_names = ['time', 'attr1', 'attr2', 'attr3']

def generate_binary_header(date_float, metadata, fmt, units, column_names):
    byte_buffer = io.BytesIO()
    byte_buffer.write(struct.pack('2B', *MAGIC_ID_BYTES))
    byte_buffer.write(struct.pack('2B', MAJOR_VERSION, MINOR_VERSION))
    byte_buffer.write(struct.pack('d', date_float))

    metadatastring = io.BytesIO()
    metadatawriter = csv.writer(metadatastring, delimiter=' ')
    for key, value in metadata.items():
        metadatawriter.writerow([key, value])
    metadatasize = len(metadatastring.getvalue())

    fmt_size = len(fmt)

    column_names_line = " ".join(column_names)
    column_names_size = len(column_names_line)

    units_line = " ".join(units)
    units_size = len(units_line)

    # write size of metadatastring
    byte_buffer.write(struct.pack('i', metadatasize))

    # write size of fmt
    byte_buffer.write(struct.pack('i', fmt_size))

    # write size of column_names
    byte_buffer.write(struct.pack('i', column_names_size))

    # write size of units
    byte_buffer.write(struct.pack('i', units_size))


    # write actual metadatastring
    byte_buffer.write(metadatastring.getvalue())

    # write fmt
    byte_buffer.write(fmt)

    # write column names
    byte_buffer.write(column_names_line)

    # write units_line
    byte_buffer.write(units_line)
    byte_buffer.seek(0)
    return byte_buffer.read()


#units = ['dt64', 'm/s^2', 'm/s^2', 'm/s^2']
#buf = generate_binary_header(date_float, metadata, "dddd", units, column_names)
#buf.seek(0)
#with open('test.bin', 'wb') as binfile:
#    binfile.write(buf.read())

