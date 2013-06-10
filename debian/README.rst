Building deb package
====================

*create a top level directoy.
*cd to it and clone the codebase into opt.
*cd opt;python setup.py sdist.
*add etc directory on the same level as opt as you can see.
*add the init.d files inside the etc directory.
*add usr directory.
*add link to /opt/bastio-agent/bin/bastio-agent inside the usr/bin directory
*cd to the top level directory.
*dpkg -b bastio bastio-agent_0.1.0_all.deb

This how the package is organized before packing it up.

bastio
├── DEBIAN
│   ├── control
│   ├── md5sums
│   └── postinst
├── etc
│   ├── bastio
│   │   └── agent.conf
│   ├── init.d
│   │   └── bastio-agent
│   ├── rc0.d
│   │   └── K20bastio-agent
│   ├── rc1.d
│   │   └── K20bastio-agent
│   ├── rc2.d
│   │   └── S20bastio-agent
│   ├── rc3.d
│   │   └── S20bastio-agent
│   ├── rc4.d
│   │   └── S20bastio-agent
│   ├── rc5.d
│   │   └── S20bastio-agent
│   └── rc6.d
│       └── K20bastio-agent
├── opt
│   └── bastio
│       ├── bastio
│       │   ├── account.py
│       │   ├── cli.py
│       │   ├── concurrency.py
│       │   ├── concurrency.pyc
│       │   ├── configs.py
│       │   ├── configs.pyc
│       │   ├── excepts.py
│       │   ├── excepts.pyc
│       │   ├── __init__.py
│       │   ├── __init__.pyc
│       │   ├── log.py
│       │   ├── log.pyc
│       │   ├── mixin.py
│       │   ├── mixin.pyc
│       │   ├── ssh
│       │   │   ├── api.py
│       │   │   ├── api.pyc
│       │   │   ├── client.py
│       │   │   ├── client.pyc
│       │   │   ├── crypto.py
│       │   │   ├── crypto.pyc
│       │   │   ├── __init__.py
│       │   │   ├── __init__.pyc
│       │   │   ├── protocol.py
│       │   │   └── protocol.pyc
│       │   ├── test
│       │   │   ├── __init__.py
│       │   │   ├── __init__.pyc
│       │   │   ├── test_concurrency.py
│       │   │   ├── test_concurrency.pyc
│       │   │   ├── test_configs.py
│       │   │   ├── test_configs.pyc
│       │   │   ├── test_mixin.py
│       │   │   ├── test_mixin.pyc
│       │   │   ├── test_ssh_api.py
│       │   │   ├── test_ssh_api.pyc
│       │   │   ├── test_ssh_client.py
│       │   │   ├── test_ssh_client.pyc
│       │   │   ├── test_ssh_crypto.py
│       │   │   ├── test_ssh_crypto.pyc
│       │   │   ├── test_ssh_protocol.py
│       │   │   └── test_ssh_protocol.pyc
│       │   ├── version.py
│       │   └── version.pyc
│       ├── Bastio_Agent.egg-info
│       │   ├── dependency_links.txt
│       │   ├── entry_points.txt
│       │   ├── PKG-INFO
│       │   ├── requires.txt
│       │   ├── SOURCES.txt
│       │   └── top_level.txt
│       ├── debian
│       │   └── README.rst
│       ├── dist
│       │   └── Bastio-Agent-0.1.0.tar.gz
│       ├── distribute_setup.py
│       ├── distribute_setup.pyc
│       ├── LICENSE
│       ├── MANIFEST.in
│       ├── README.rst
│       ├── requirements.txt
│       └── setup.py
└── usr
    └── bin
        └── bastio-agent -> /opt/bastio-agent/bin/bastio-agent
