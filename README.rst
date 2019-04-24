===============================
RasPyre
===============================

.. image:: https://raw.githubusercontent.com/msk-buw/raspyre/master/raspyre-logo.png

RasPyre is a Raspberry Pi based Software Framework for the application in Structural Health Monitoring.
A variety of sensor hardware can be rapidly incorporated and controlled. The integrated WiFi mesh configuration
enables users to set up an ad-hoc wireless sensor network.

Please cite our work when using our software in your own research or publication.

https://www.uni-weimar.de/en/civil-engineering/chairs/modelling-and-simulation-of-structures/research/software/

Installation
------------

* Linux

On the command line, install the dependencies::

  $ pip install -r requirements.txt

Then install the package itself::

  $ python setup.py install

After the successfull installation the RPC server is available as a command line tool (``raspyre-rpcserver``). If you wish to start the service automatically copy the file ``raspyre-rpcserver.service`` to ``/etc/systemd/system/`` and enable the systemd service::

  # systemctl enable raspyre-rpcserver
