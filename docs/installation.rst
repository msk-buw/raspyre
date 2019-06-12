===================
Manual Installation
===================

If you decide to configure your RasPyre nodes manually you need to perform several steps.

.. note::
   Please ensure that you are running a Linux distribution with a configured real time kernel.

Software Installation
---------------------

Install a suitable Python interpreter (3.5+).

On a Debian based system::

  # apt-get install python3 python3-dev python3-pip

Install the OLSRd routing daemon::

  # apt-get install olsrd

Install the RasPyre python package::

  # python3 -m pip install raspyre

Install one or more sensor drivers (e.g. the ``raspyre-mpu6050`` package)::

  # python3 -m pip install raspyre-mpu6050

Network configuration
---------------------

Configure your network adapters, so that your meshing interface is identified by ``mesh0``.
Configure the ``udev`` subsystem, that the WiFi adapter that should provide the portal access point is renamed to ``ap0``.

Start up the OLSR daemon. A sample configuration file can be found the in the ``conf`` directory of the RasPyre distribution.

RPC daemon configuration
------------------------

Configure the RasPyre RPC service to start up as a daemon. A systemd unit file is provided in the ``conf`` directory::

  [Unit]
  Description=Raspyre RPC Server Backend
  After=network.target

  [Service]
  WorkingDirectory=/home/pi
  ExecStart=/usr/local/bin/raspyre-rpcserver --logfile /home/pi/raspyre-rpc.log /home/pi/data/ --verbose
  User=root
  LimitRTPRIO=90
  LimitRTTIME=infinity

  [Install]
  WantedBy=multi-user.target

.. note:: Ensure that the process is run with proper rights to request real time priority CPU scheduling up to priority 90.

