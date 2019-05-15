"""
Raspyre Converter
CSV Version: 0.1
Binary Version: 0.4

This tool converts Raspyre files between CSV format and binary format.
If the input file is binary, the output will be CSV and vice versa.
If the output file parameter is omitted, the input name will be used with
a new file ending .csv or .bin
The tool does support converting entire folders if the input file is a
folder containing only valid measurement files.
"""

__version__ = "0.2"
import argparse
from . import storage
import os.path
import os
import sys

#from .storage import RaspyreFileFormatException


class RaspyreReaderException(Exception):
    pass


def _convert(conversion_function, binary, source, target):
    try:
        conversion_function(source, target)
        sys.stdout.write("Converted {}.\n".format(source))
    except RaspyreReaderException:
        sys.stderr.write(
            "Exception occurred while reading {}\n".format(source))
    except storage.RaspyreFileFormatException:
        if binary:
            sys.stderr.write(
                "Error! {} is not in CSV format.\n".format(source))
        else:
            sys.stderr.write(
                "Error! {} is not in binary format.\n".format(source))


def convert_binary_to_csv(source, target):
    try:
        reader = storage.getReader(source)
    except:
        raise RaspyreReaderException
    if not reader.binary:
        raise storage.RaspyreFileFormatException
    writer = storage.Writer(target, binary=False)
    writer.writeHeader(reader.header)

    for line in reader.data():
        writer.writeRow(line)
    writer.close()


def convert_csv_to_binary(source, target):
    try:
        reader = storage.getReader(source)
    except:
        raise RaspyreReaderException
    if reader.binary:
        raise storage.RaspyreFileFormatException
    writer = storage.Writer(target, binary=True)
    writer.writeHeader(reader.header)

    for line in reader.data():
        writer.writeRow(line)
    writer.close()


def main():
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument(
        "-o",
        "--out",
        action="store",
        default=None,
        help="filename or folder for the output",
        dest="output")
    parser.add_argument(
        "input",
        action="store",
        nargs='+',
        help="file or folder to be converted")
    parser.add_argument(
        "--version",
        action="version",
        version="Raspyre File converter {version}".format(version=__version__))
    parser.add_argument(
        "-f",
        "--force",
        action="store_true",
        help="overwrite existing files",
        default=False,
        dest="force_overwrite")
    parser.add_argument(
        "-r",
        "--recursive",
        action="store_true",
        help="convert directories and their contents recursively",
        default=False,
        dest="recursive")
    parser.add_argument(
        "-b",
        "--binary",
        action="store_true",
        help="convert csv to binary",
        default=False,
        dest="tobinary")

    results = parser.parse_args()
    #print results
    output_argument = results.output
    input_file_flag = False
    input_files = list()

    # determine file extension and conversion function based on input flag
    if results.tobinary:
        output_extension = ".bin"
        conversion_function = convert_csv_to_binary
    else:
        output_extension = ".csv"
        conversion_function = convert_binary_to_csv

    # create list of input files
    if os.path.isdir(results.input[0]):
        if len(results.input) > 1:
            sys.stderr.write(
                "Error! Please specify only _one_ input folder.\n")
            sys.exit(10)
        walkroot = os.walk(results.input[0])
        if results.recursive:
            for root, dirs, files in walkroot:
                for input_file in files:
                    input_files.append(os.path.join(root, input_file))
        else:
            root, dirs, files = next(walkroot)
            for input_file in files:
                input_files.append(os.path.join(root, input_file))

    elif os.path.isfile(results.input[0]):
        for input_argument in results.input:
            if not os.path.exists(input_argument):
                sys.stderr.write("Error! Input file \"{}\" not found.\n".
                                 format(input_argument))
                sys.exit(2)
            if os.path.isfile(input_argument):
                input_files.append(input_argument)
    else:
        sys.stderr.write(
            "Error! Input file \"{}\" not found.\n".format(results.input[0]))
        sys.exit(1)

    # process list of input files
    if len(input_files) > 1:
        if output_argument is not None:
            if not os.path.isdir(output_argument):
                sys.stderr.write(
                    "Error! Please specify an output folder if you want to convert more than one input file.\n"
                )
                sys.exit(3)
        for input_file in input_files:
            output_basename, ext = os.path.splitext(
                os.path.basename(input_file))

            if output_argument is None:
                output_folder = os.path.dirname(input_file)
                output_filename = os.path.join(
                    output_folder, (output_basename + output_extension))
                if os.path.exists(
                        output_filename) and not results.force_overwrite:
                    sys.stderr.write(
                        "File {} already exists. Can not convert! ".format(
                            output_filename))
                    sys.stderr.write("Use -f to overwrite.\n")
                    continue
                if output_filename != input_file:
                    _convert(conversion_function, results.tobinary, input_file,
                             output_filename)

            else:
                if os.path.isdir(output_argument):
                    output_filename = os.path.join(
                        output_argument, (output_basename + output_extension))
                    if os.path.exists(output_filename):
                        sys.stderr.write(
                            "File {} already exists. Can not convert!".format(
                                output_filename))
                        sys.stderr.write("Use -f to overwrite.\n")
                        continue
                    if output_filename != input_file:
                        _convert(conversion_function, results.tobinary,
                                 input_file, output_filename)

                else:
                    sys.stderr.write(
                        "Please specify an existing output folder.\n")
                    sys.exit(4)

    elif len(input_files) == 1:  # only one file has been specified
        input_file = input_files[0]
        output_basename, ext = os.path.splitext(os.path.basename(input_file))
        if output_argument is None:
            output_basename, ext = os.path.splitext(
                os.path.basename(input_file))
            output_folder = os.path.dirname(input_file)
            output_filename = os.path.join(
                output_folder, (output_basename + output_extension))
            if output_filename != input_file:
                _convert(conversion_function, results.tobinary, input_file,
                         output_filename)
        else:
            if os.path.isdir(output_argument):
                output_filename = os.path.join(
                    output_argument, (output_basename + output_extension))
                output_argument = output_filename
            elif os.path.isfile(output_argument):
                if not results.force_overwrite:
                    sys.stderr.write(
                        "File {} already exists. Can not convert! ".format(
                            output_argument))
                    sys.stderr.write("Use -f to overwrite.\n")
                    sys.exit(5)
                output_filename = output_argument
            else:
                raise Exception("Could not determine output file.")

            if output_filename != input_file:
                _convert(conversion_function, results.tobinary, input_file,
                         output_filename)
    else:
        sys.stderr.write("No valid file found to convert. Exiting.\n")
        sys.exit(11)


if __name__ == "__main__":  # pragma: no cover
    main()
