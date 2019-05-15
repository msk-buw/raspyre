==========
Quickstart
==========

Installation of caSHMere
------------------------

Linux: Install the packages by using the Python package manager::

    $ pip install cashmere.whl

Ensure that the package zeroconf is installed on your machine. Please refer to the manual of your Linux distribution for this step.

Windows: 
Install the CASHMERE interface with setup_cashmere.exe.

First Usage
-----------

1. Setup the raspyre nodes and supply each with a power source.
Choose a portal node that can be reached via WiFi by plugging in the USB network adapter into a free USB port.
Note: You can change the portal node at will by unplugging the USB network adapter and plugging it into a different node.

2. Allow ~30 seconds for the system to set up its network configuration correctly and for the nodes in the mesh network to exchange routing information.
Connect your local machine to the open WiFi access point named **“RaspyreAP”**

3. Start up CASHMERE. You will be greeted by a splash screen and the main interface is visible.

   .. image:: images/cashmere_main.png

The main interface is composed of three widgets.
On the left is the central control widget to discover nodes in the sensor network and to send commands to individual nodes or groups of nodes.
The right widget is dedicated to different widgets to visualize received sensor signals. The bottom area displays logging output during the runtime.

4. Discovery of nodes:
Click the button labeled “Autodetect portal node” and wait a few seconds for the bonjour service to locate the portal node.
When the portal node is found, its host name will be displayed in the field above the button.

   .. image:: images/cashmere_discovery.png

Click “Refresh node list” to query the portal node for the routing information of the nodes in the sensor network. 
The list in the upper left corner should then be populated with reachable nodes and its IP addresses.
Note: please allow up to 2 minutes for the routing information to be correct if you introduce additional nodes to the network during runtime.

5. Sending commands:
To send commands to individual nodes select a node from the list by left clicking. Activate the context menu by right clicking. From there you can choose different commands to send to the selected nodes.
You can select several nodes as a group by holding down the Shift key. Individual nodes can be added to a selection group by holding down the Ctrl key while left clicking.

6. Configuration of time synchronization service:
To synchronize the time between the nodes in the mesh network you can individually assign a node the role of the master node and configure the remaining nodes to synchronize relative to this master node.
A shortcut for this configuration task has been added to the interface.
By selecting ``Autoconfigure Time Sync`` in the context menu, the program tries to set the portal node as a master node and configure the the remaining nodes to use this server for synchronization.

   .. image:: images/cashmere_synchronization.png

The logging widget provides additional information about the sent commands.

Note: Please allow ~2 minutes for the network to synchronize completely. You can visually inspect the synchronization by sending the command ``Locate/Start blinking``. The selected nodes should blink synchronously after some time.

7. Configuration of attached sensor hardware:
The configuration of installed sensor hardware is performed via the context menu as well. Select the nodes you wish to configure and select ``Measurement Control/Add sensor`` from the context menu.
A dialog window will appear. Please refer to the individual module documentations for the details of configuration.

   .. image:: images/cashmere_sensor.png

The dialog is pre-filled with a default configuration for the MPU6050 sensor.

* The name field can be freely chosen for later easier identification of the generated time series records.
* The sensor type selects the installed driver module to use for the specific sensor hardware.
* The configuration field is a serialized JSON string holding the individual sensor parameters. Please refer to the documentation of the sensor module. For the MPU6050 sensor, the only configurable parameter is the address of the I2C cable. You can either select address 0x68 or 0x69 according to the connected cable.
* The frequency field defines the polling frequency for the specified sensor task.
* The channels field consists of a list of channel identifiers which are to be polled during the measurement. Please refer to the documentation of the sensor module for a list of valid channels. For the MPU6050 sensor, the acceleration axes are already selected, denoted by “accx”, “accy”, “accz”.

8. Measurement control
To start a measurement select nodes which are properly configured for their sensor hardware and select in the context menu 
``Measurement control/Start measurement``. You will be prompted to provide a name for the measurement. The nodes will start the measurement task and record time series on their local storage. Additionally the sensor signal is published on a network socket.

To stop a measurement select ``Measurement control/Stop measurement`` from the context menu of your selected nodes.

9. Transfer recorded time series data
To download recorded time series from individual nodes select ``File Manager`` from the context menu. The node will be queried for its recorded measurement files and they will be displayed in the list of the dialog.

   .. image:: images/cashmere_transfer.png

Select the file you wish to transfer and click the Download button.
Select the destination where you wish to save the downloaded time series file. If the checkbox “Convert to CSV” is ticked, the transferred binary file will automatically converted to a CSV file. The original binary will be deleted after successful conversion.

Each time series file is named after the following scheme:
*hostname__measurementname_sensorname_timestamp.bin*

10. Plot signal data during a measurement
During a running measurement the acquired signal data can by visualized live by utilizing the plot widgets.

Click the button labeled ``Create plot widget``. A dialog will appear to configure to which signal to subscribe.

The fields a pre-filled with default information for the case you wish to subscribe to a signal from a MPU6050 sensor.

   .. image:: images/cashmere_plot1.png

* The Address field denotes the ZMQ-network address to which you wish to subscribe.
  Each measurement publishes its signal on the port 5556.
  Enter the information in the following form:
  ``tcp://IP_ADDRESS:5556``
* The channels field consists of a list of the channels in the acquired network packets. Please refer to the documentation of the individual sensor module for specifics.
* The datatypes field string denotes the datatypes of the channels. In the given example, the individual channels are decoded as double datatype.
* The units field consists of a list of the units for each individual channel. In the example, the time channel is interpreted as a 64bit datetime timestamp. 

After successful time synchronization and configuration a new plot widget will appear in the right area of the interface.

   .. image:: images/cashmere_plot2.png

By grabbing the right edge of the plot window with the left mouse button, you can drag the FFT plotting area into the plot.
Tick the checkbox ``Calculate FFT`` to calculate a Fast Fourier Transform for the selected signal and visualize it.

You can utilize the left mouse button in the plot window to drag the signal along the axes and the right mouse button to adjust the scaling of the plot area. If you wish to stop plotting the signal just close the sub window inside the right area of the interface.

   .. image:: images/cashmere_plot3.png
