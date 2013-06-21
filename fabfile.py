from fabric.api import *
from bastio import __version__
def builddeb():
	"""Creates a new debian package"""
	local('python setup.py sdist')
	with settings(warn_only=True):   
		local('dpkg-buildpackage -tc',capture=False)
	local('mv ../bastio-agent_%s_all.deb .' %__version__)
	#local('mv ../*.changes	.')
	
def clean():
	"""Cleans debian package and runs setup.py clean"""
	local('rm -f bastio-agent_%s_all.deb' %__version__)
	local('python setup.py clean')

def release(name="Ahmad Aabed",email="ahmad.aabed.m@gmail.com",):
	"""Creates a release package i.e (opens the changelog file to write changes)"""
	print __version__
	with shell_env(DEBFULLNAME=name, DEBEMAIL=email):
            local('dch -v %s' %__version__)
