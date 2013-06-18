from fabric.api import *
from bastio import __version__
def builddeb():
	local('python setup.py sdist')
	with settings(warn_only=True):   
		local('dpkg-buildpackage -tc',capture=False)
	local('mv ../*.deb .')
	#local('mv ../*.changes	.')
	
def clean():
	local('rm -f *.deb')
	local('python setup.py clean')

def release(name="Ahmad Aabed",email="ahmad.aabed.m@gmail.com",):
	print __version__
	with shell_env(DEBFULLNAME=name, DEBEMAIL=email):
            local('dch -v %s' %__version__)
