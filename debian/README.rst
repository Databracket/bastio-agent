Building deb package
====================

* create a top level directoy.
* cd to it and clone the codebase into opt.
* cd opt;python setup.py sdist.
* add etc directory on the same level as opt as you can see.
* add the init.d files inside the etc directory.
* add usr directory.
* add link to /opt/bastio-agent/bin/bastio-agent inside the usr/bin directory
* cd to the top level directory.
* dpkg -b bastio bastio-agent_0.1.0_all.deb
