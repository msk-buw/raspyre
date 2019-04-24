from raspyre import converter
import pytest
import os


def setup_function(function):
    os.chdir(os.path.dirname(os.path.abspath(__file__)))


def test__convert(mocker, capsys):
    def raise_reader_exception(source, target):
        raise converter.RaspyreReaderException

    def raise_wrong_fileformat_exception(source, target):
        raise converter.RaspyreFileFormatException

    # The function should report an error message if a
    # RaspyreReaderException occured
    converter._convert(raise_reader_exception, True, None, None)
    out, err = capsys.readouterr()
    assert err.startswith("Exception occurred")

    # The function should report an error message if a
    # RaspyreFileFormatException occured
    out = ""
    err = ""
    converter._convert(raise_wrong_fileformat_exception, True, None, None)
    out, err = capsys.readouterr()
    assert "CSV" in err

    out = ""
    err = ""
    converter._convert(raise_wrong_fileformat_exception, False, None, None)
    out, err = capsys.readouterr()
    assert "binary" in err


def test_convert_binary_to_csv(mocker):
    with pytest.raises(converter.RaspyreReaderException):
        converter.convert_binary_to_csv(
            "converter_tests/input_folder/file_does_not_exist.bin", None)

    with pytest.raises(converter.RaspyreFileFormatException):
        converter.convert_binary_to_csv(
            "converter_tests/input_folder/level0_test3.csv", None)

    mocker.patch.object(converter.storage, 'Writer', autospec=True)
    converter.convert_binary_to_csv(
        "converter_tests/input_folder/level0_test3.bin",
        "converter_tests/output_folder/output.csv")
    converter.storage.Writer.assert_called_once_with(
        "converter_tests/output_folder/output.csv", binary=False)
    # TODO: find a better testing method?


def test_convert_csv_to_binary(mocker):
    with pytest.raises(converter.RaspyreReaderException):
        converter.convert_csv_to_binary(
            "converter_tests/input_folder/file_does_not_exist.bin", None)

    with pytest.raises(converter.RaspyreFileFormatException):
        converter.convert_csv_to_binary(
            "converter_tests/input_folder/level0_test1.bin", None)

    mocker.patch.object(converter.storage, 'Writer', autospec=True)
    converter.convert_csv_to_binary(
        "converter_tests/input_folder/level0_test3.csv",
        "converter_tests/output_folder/output.bin")
    converter.storage.Writer.assert_called_once_with(
        "converter_tests/output_folder/output.bin", binary=True)
    # TODO: find a better testing method?


def test_argparse_single_input(mocker):
    testargs = ["prog", "converter_tests/input_folder/level0_test1.bin"]
    mocker.patch.object(converter.sys, 'argv', testargs)
    mocker.patch.object(converter, 'convert_binary_to_csv')
    converter.main()
    converter.convert_binary_to_csv.assert_called_once_with(
        "converter_tests/input_folder/level0_test1.bin",
        "converter_tests/input_folder/level0_test1.csv")


def test_argparse_single_input_not_found(mocker):
    testargs = ["prog", "converter_tests/input_folder/file_does_not_exist"]
    mocker.patch.object(converter.sys, 'argv', testargs)
    with pytest.raises(SystemExit) as e:
        converter.main()
    assert e.type == SystemExit
    assert e.value.code == 1


def test_argparse_multi_input(mocker):
    testargs = [
        "prog", "converter_tests/input_folder/level0_test1.bin",
        "converter_tests/input_folder/level0_test2.bin"
    ]
    mocker.patch.object(converter.sys, 'argv', testargs)
    mocker.patch.object(converter, 'convert_binary_to_csv')
    converter.main()
    assert converter.convert_binary_to_csv.call_count == 2
    converter.convert_binary_to_csv.assert_any_call(
        "converter_tests/input_folder/level0_test1.bin",
        "converter_tests/input_folder/level0_test1.csv")
    converter.convert_binary_to_csv.assert_any_call(
        "converter_tests/input_folder/level0_test2.bin",
        "converter_tests/input_folder/level0_test2.csv")


def test_argparse_multi_input_first_not_found(mocker):
    testargs = [
        "prog", "converter_tests/input_folder/file_does_not_exist.bin",
        "converter_tests/input_folder/level0_test2.bin"
    ]
    mocker.patch.object(converter.sys, 'argv', testargs)
    with pytest.raises(SystemExit) as e:
        converter.main()
    assert e.type == SystemExit
    assert e.value.code == 1


def test_argparse_multi_input_second_not_found(mocker):
    testargs = [
        "prog", "converter_tests/input_folder/level0_test2.bin",
        "converter_tests/input_folder/file_does_not_exist.bin"
    ]
    mocker.patch.object(converter.sys, 'argv', testargs)
    with pytest.raises(SystemExit) as e:
        converter.main()

    assert e.type == SystemExit
    assert e.value.code == 2


def test_argparse_multi_input_single_output(mocker):
    testargs = [
        "prog", "converter_tests/input_folder/level0_test1.bin",
        "converter_tests/input_folder/level0_test2.bin",
        "-o", "converter_tests/output_folder/level0_test1.csv"
    ]
    mocker.patch.object(converter.sys, 'argv', testargs)
    with pytest.raises(SystemExit) as e:
        converter.main()

    assert e.type == SystemExit
    assert e.value.code == 3
    

def test_argparse_multi_input_file_folder(mocker):
    # if the first input is a file, following non-file inputs should be
    # ignored
    testargs = [
        "prog", "converter_tests/input_folder/level0_test1.bin",
        "converter_tests/input_folder/level1",
    ]
    mocker.patch.object(converter.sys, 'argv', testargs)
    mocker.patch.object(converter, 'convert_binary_to_csv')
    converter.main()
    assert converter.convert_binary_to_csv.call_count == 1
    converter.convert_binary_to_csv.assert_any_call(
        "converter_tests/input_folder/level0_test1.bin",
        "converter_tests/input_folder/level0_test1.csv")

    
def test_argparse_multi_input_file_exists(mocker, capsys):
    testargs = [
        "prog", "converter_tests/input_folder/level0_test1.bin",
        "converter_tests/input_folder/level0_test2.bin",
        "-o", "converter_tests/output_folder"
    ]
    mocker.patch.object(converter.sys, 'argv', testargs)
    mocker.patch.object(converter, 'convert_binary_to_csv')
    converter.main()
    assert converter.convert_binary_to_csv.call_count == 1
    converter.convert_binary_to_csv.assert_any_call(
        "converter_tests/input_folder/level0_test2.bin",
        "converter_tests/output_folder/level0_test2.csv")
    out, err = capsys.readouterr()
    assert "already exists" in err


def test_argparse_multi_input_folders(mocker):
    testargs = [
        "prog", "converter_tests/input_folder/level1/level2",
        "converter_tests/input_folder/level2",
    ]
    mocker.patch.object(converter.sys, 'argv', testargs)
    
    with pytest.raises(SystemExit) as e:
        converter.main()

    assert e.type == SystemExit
    assert e.value.code == 10

def test_argparse_single_input_folder_recursive_force(mocker):
    testargs = [
        "prog", "converter_tests/input_folder", "-r", "-f",
    ]
    mocker.patch.object(converter.sys, 'argv', testargs)
    mocker.patch.object(converter, 'convert_binary_to_csv')
    converter.main()

    assert converter.convert_binary_to_csv.call_count == 7
    converter.convert_binary_to_csv.assert_any_call(
        "converter_tests/input_folder/level0_test1.bin",
        "converter_tests/input_folder/level0_test1.csv")
    converter.convert_binary_to_csv.assert_any_call(
        "converter_tests/input_folder/level0_test2.bin",
        "converter_tests/input_folder/level0_test2.csv")
    converter.convert_binary_to_csv.assert_any_call(
        "converter_tests/input_folder/level0_test3.bin",
        "converter_tests/input_folder/level0_test3.csv")
    converter.convert_binary_to_csv.assert_any_call(
        "converter_tests/input_folder/level1/level1_test1.bin",
        "converter_tests/input_folder/level1/level1_test1.csv")
    converter.convert_binary_to_csv.assert_any_call(
        "converter_tests/input_folder/level1/level1_test2.bin",
        "converter_tests/input_folder/level1/level1_test2.csv")
    converter.convert_binary_to_csv.assert_any_call(
        "converter_tests/input_folder/level1/level2/level2_test1.bin",
        "converter_tests/input_folder/level1/level2/level2_test1.csv")
    converter.convert_binary_to_csv.assert_any_call(
        "converter_tests/input_folder/level1/level2/level2_test2.bin",
        "converter_tests/input_folder/level1/level2/level2_test2.csv")
    

def test_argparse_single_input_folder_recursive_nonforce(mocker):
    testargs = [
        "prog", "converter_tests/input_folder", "-r",
    ]
    mocker.patch.object(converter.sys, 'argv', testargs)
    mocker.patch.object(converter, 'convert_binary_to_csv')
    converter.main()



    assert converter.convert_binary_to_csv.call_count == 6
    converter.convert_binary_to_csv.assert_any_call(
        "converter_tests/input_folder/level0_test1.bin",
        "converter_tests/input_folder/level0_test1.csv")
    converter.convert_binary_to_csv.assert_any_call(
        "converter_tests/input_folder/level0_test2.bin",
        "converter_tests/input_folder/level0_test2.csv")

    # NOTE! converter_tests/input_folder/level0_test3.csv
    # should _not_ be overwritten!

    converter.convert_binary_to_csv.assert_any_call(
        "converter_tests/input_folder/level1/level1_test1.bin",
        "converter_tests/input_folder/level1/level1_test1.csv")
    converter.convert_binary_to_csv.assert_any_call(
        "converter_tests/input_folder/level1/level1_test2.bin",
        "converter_tests/input_folder/level1/level1_test2.csv")
    converter.convert_binary_to_csv.assert_any_call(
        "converter_tests/input_folder/level1/level2/level2_test1.bin",
        "converter_tests/input_folder/level1/level2/level2_test1.csv")
    converter.convert_binary_to_csv.assert_any_call(
        "converter_tests/input_folder/level1/level2/level2_test2.bin",
        "converter_tests/input_folder/level1/level2/level2_test2.csv")



def test_argparse_single_input_folder_nonrecursive_force(mocker):
    testargs = [
        "prog", "converter_tests/input_folder", "-f",
    ]
    mocker.patch.object(converter.sys, 'argv', testargs)
    mocker.patch.object(converter, 'convert_binary_to_csv')
    converter.main()

    assert converter.convert_binary_to_csv.call_count == 3
    converter.convert_binary_to_csv.assert_any_call(
        "converter_tests/input_folder/level0_test1.bin",
        "converter_tests/input_folder/level0_test1.csv")
    converter.convert_binary_to_csv.assert_any_call(
        "converter_tests/input_folder/level0_test2.bin",
        "converter_tests/input_folder/level0_test2.csv")
    converter.convert_binary_to_csv.assert_any_call(
        "converter_tests/input_folder/level0_test3.bin",
        "converter_tests/input_folder/level0_test3.csv")


    
def test_argparse_single_input_folder_nonrecursive_nonforce(mocker):
    testargs = [
        "prog", "converter_tests/input_folder", 
    ]
    mocker.patch.object(converter.sys, 'argv', testargs)
    mocker.patch.object(converter, 'convert_binary_to_csv')
    converter.main()

    assert converter.convert_binary_to_csv.call_count == 2
    converter.convert_binary_to_csv.assert_any_call(
        "converter_tests/input_folder/level0_test1.bin",
        "converter_tests/input_folder/level0_test1.csv")
    converter.convert_binary_to_csv.assert_any_call(
        "converter_tests/input_folder/level0_test2.bin",
        "converter_tests/input_folder/level0_test2.csv")

    
def test_argparse_non_existing_output_folder(mocker):
    pass
    #testargs = [
    #    "prog", "converter_tests/input_folder/level0_test1.bin",
    #    "-o", "converter_tests/output_folder/doesnotexist"
    #]
    #mocker.patch.object(converter.sys, 'argv', testargs)
    #
    #with pytest.raises(SystemExit) as e:
    #    converter.main()

    #assert e.type == SystemExit
    #assert e.value.code == 4
