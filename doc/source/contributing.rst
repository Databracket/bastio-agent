.. include:: global.rst.inc

.. _contributing:

Contributing
=======

Thought of something you would like to see in |project_name|?
This document will help you get started.

Important URLs
--------------

|project_name| uses git_ to track code history and hosts its `code repository`_
at github_. The `issue tracker`_ is where you can file bug reports and request
features or enhancements to |project_name|. We also have a `PyPI repository`_
hosted at PyPI_, and a `PPA repository`_. |project_name| uses and is centered
around Paramiko_.

Before You Start
----------------

Ensure your system has the following programs and libraries installed:

- Python_
- git_
- ssh_
- virtualenv_

Setting up the Work Environment
-------------------------------

- Fork the `code repository`_ into your github_ account. Let us call you ``hackeratti``
  for the sake of this example. Replace ``hackeratti`` with your own username below.

- Clone your fork and setup your environment::

  $ git clone git@github.com:hackeratti/bastio-agent.git
  $ cd bastio-agent/
  $ virtualenv venv/
  $ source venv/bin/activate
  $ python setup.py develop

.. note::
    Run ``python setup.py develop`` only once at first, any changes won't affect the
    script generated in the ``bin`` directory under the ``venv`` directory.


