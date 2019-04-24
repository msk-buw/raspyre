"""
Some helper functions for frequent tasks:
    write Records to file
    create Pandas Dataframe from Records (not jet tested)
    change the name of the wifi the Pi hosts (only if the pi is configured accordingly)
"""
from .record import Record
from os.path import isfile


def rec2DF(records):
    """ 
    Convert a list of Records into a Pandas DataFrame with column headers according to the attributes of the first object. NOT TESTED. Only works if all records have the same attribtues
    """
    import pandas
    columns = [name for name in records[0]]
    return pandas.DataFrame([ [rec[name] for name in columns] for rec in records], columns = columns)

def rec2File(file, records, append=True, header=True, delimiter=", "):
    '''
    This function writes a list of Records into a file. You can choose whether to append or override the file 
    if it allready exists and decide, if you want the attribute names asheader displayed. Also you can specify a column delimiter
    that defaults to ", ".
    The header is proceeded with a # sign to be marked as not data. The first column is the timestamp, after that the columns are ordered
    alphabetically
    '''
    writemode = "w"
    if isfile(file) and append:
        writemode = "a"
        header = False
    columns = [c for c in records[0] if c != "time"]
    columns.sort()
    columns = ['time'] + columns
    with open(file, writemode) as myfile:
        if header:
            myfile.write("#" + delimiter.join(columns))
        for record in records:
            myfile.write("\n")
            myfile.write(delimiter.join(["{:7f}".format(record[col]) for col in columns]))
        myfile.flush()
        os.fsync(myfile.fileno())



def changeWifiName(name, path="/home/pi/wifi.conf", reboot=False):
    '''
    This function changes the SSID the Wifi created by the Pi uses. This SSID is in a config file. The default is the file wifi.conf in the home directory
    For the changes to take effect, the system has to be rebooted. This can be done with the reboot option.
    '''
    if not isfile(path):
        raise IOError("File {} not found".format(path))
    else:
        lines = []
        with open(path) as infile:
            for line in infile:
                if "ssid" in line:
                    lines.append("ssid="+name+"\n")
                else :
                    lines.append(line)
        with open(path, "w") as outfile:
            for line in lines:
                outfile.write(line)
        if reboot:
            command = "/usr/bin/sudo /sbin/shutdown -r now"
            import subprocess
            process = subprocess.Popen(command.split(), stdout=subprocess.PIPE)
            output = process.communicate()[0]
            print(output)
