#!/bin/bash
if [  -d opt ]; then
    rm -fr opt;mkdir opt
fi

cd ..
python setup.py sdist 
cd -
tar xzf ../dist/Bastio-Agent-0.1.0.tar.gz -C opt
mv opt/Bastio-Agent-0.1.0/ opt/bastio
cp -r ../dist/ opt/bastio

if [  -f bastio-agent_0.1.0_all.deb ]; then
    rm -f bastio-agent_0.1.0_all.deb
fi

fpm -s dir -t deb -a all -v 0.1.0 -n  bastio-agent  --vendor Databracket --deb-pre-depends 'python-dev' --deb-pre-depends 'python-virtualenv' --deb-pre-depends 'python2.7'  --description 'An agent for Bastio service to provision system accounts and SSH access.' --url 'http://www.bastio.com/' -m 'support@bastio.com'  --license 'GPLv3+'    --deb-user root  --deb-group root  -x builddeb.sh .
