.. Bastio Agent documentation master file, created by
   sphinx-quickstart on Mon Jun 17 04:33:51 2013.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

.. include:: global.rst.inc

Bastio Agent
============

Bastio is an easy to use operating system user account provisioning tool to help
people with a lot of servers and users create and delete system user accounts.
With Bastio you will no longer need to keep track of your team's access to
servers, once a team member leaves you can disable her access to all your server
assets in one click.

Bastio saves you time by not making you wait for your team members to generate
and send you their public keys while allowing crypto-savvy members of your team
the freedom to generate their own.

Install |project_name| on your servers to enable OS account provisioning and SSH
access management. No daunting configurations needed; all you have to do is specify
your API key and run the agent.

Easy Installation
-----------------

You can install |project_name| from our `PPA repository`_ quickly and easily::

    # apt-get install bastio-agent

You could also use pip_ to install |project_name|::

    # pip install bastio-agent

Need more help with installation? See :ref:`installation`.

User's Guide
============

.. toctree::
    :maxdepth: 2

    installation
    configuration
    hacking
    api

Indices and Tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

