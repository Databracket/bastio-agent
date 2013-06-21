Building debian package (fabfile)
================================

* fab builddeb
This function will create a tar.gz of the code then create a debian package and move it to the repo's root.

* fab release
This function can be used on releases where you will create a new version.
The function accepts two parameters (name,email) and EDITOR will be opened and those parameters will be added to the changelog file along with the version you will only need to write the changelog message.

* fab clear

This function will remove the debian package and run setup.py clear.
