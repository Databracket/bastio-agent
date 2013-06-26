.. include:: global.rst.inc

.. _installation:

Installation
============

|project_name| can be installed in a few ways. You could either install it directly
from the `code repository`_, from the `PyPI repository`_, or from our `PPA repository`_.

Installation from the PPA repository
------------------------------------

Before installing |project_name| from our `PPA repository`_ you will need to set it
up so that the APT packaging system will understand how to deal with it. Execute the
following commands as ``root`` to add the `PPA repository`_ through APT::

    # apt-add-repository ppa:databracket/bastio-agent

If `Ubuntu Synchronizing Key Server`_ (SKS) is down for any reason you can still try
hkp://pool.sks-keyservers.net by running the following command::

    # apt-add-repository ppa:databracket/bastio-agent --keyserver hkp://pool.sks-keyservers.net

Then run the following commands to install |project_name| latest version::

    # apt-get update
    # apt-get install bastio-agent

After successful installation of the package you can refer to :ref:`configuration` to finish
configuring your fresh installation and start using |project_name|.

.. note::
    You do not have to configure |project_name| as an OS daemon or service as
    this installation method takes care of that.

Installation from the PyPI repository
-------------------------------------

You do not need to have git_ installed for this method but you will instead need
to install pip_ to be able to install |project_name| from the `PyPI repository`_.
Please execute the following commands as ``root``::

    # mkdir -p /opt/bastio-agent
    # virtualenv /opt/bastio-agent
    # source /opt/bastio-agent/bin/activate
    # pip install bastio-agent
    # deactivate

.. note::
    This installation method requires configuring |project_name| as a service 
    (see below).

Installation from the code repository
-------------------------------------

You will need to install git_ and virtualenv_, and of course you will have to
have Python_ v2.7 installed. After cloning the `code repository`_ you will need
to setup a proper environment to run |project_name| from inside a virtual
environment. To do so please execute the following commands in the same order
as ``root``::

    # mkdir -p /opt/bastio-agent
    # virtualenv /opt/bastio-agent
    # source /opt/bastio-agent/bin/activate
    # cd ~/bastio-agent-clone
    # python install setup.py
    # deactivate

.. note::
    This installation method requires configuring |project_name| as a service 
    (see below).

Configure |project_name| as an OS service
-----------------------------------------

After successful installation of the package you will then need to prepare your
operating system to run |project_name| as a service or a daemon. You will find
in the package under the ``debian`` directory a LSB_ compliant SYSV-init script
for your convenience. If you are on a Debian based distribution please carry out
the following commands::

    # mkdir -p /etc/bastio
    # cp ~/bastio-agent-clone/data/agent.conf /etc/bastio/agent.conf
    # cp ~/bastio-agent-clone/debian/bastio-agent.init /etc/init.d/bastio-agent
    # chmod 0600 /etc/bastio/agent.conf
    # chmod 0755 /etc/init.d/bastio-agent
    # update-rc.d bastio-agent defaults

.. note::
    You won't need to carry out these steps if you installed |project_name| from
    our `PPA repository`_.
