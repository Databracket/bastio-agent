PYTHON=`which python`
PROJECT=bastio-agent

all:
	@echo "make builddeb - Create debian package"
	@echo "make release - Create a release package (i.e a new version)"


builddeb:
	$(PYTHON) setup.py sdist
	dpkg-buildpackage -A -tc 
release:
	dch -i
	$(PYTHON) setup.py sdist
	dpkg-buildpackage -A -tc

clean:
	$(PYTHON) setup.py clean
