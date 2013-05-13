# Copyright 2013 Databracket LLC.
# See LICENSE file for details.

"""A module to contain version details for the package.
    Update version information here only. There's no need to update any other
    file in the package.

    Release of a hotfix/bugfix:
    - Increment version's BUILD field.

    Release of an update that modifies the API but maintains
    backward compatibility:
    - Increment version's MINOR field and reset the BUILD field.

    Release of an update that that modifies the API and breaks
    backward compatibility:
    - Increment version's MAJOR field and reset both the MINOR and BUILD fields.
"""

__author__ = "Amr Ali"
__copyright__ = "Copyright 2013 Databracket LLC"
__license__ = "GPL3v+"

VERSION_MAJOR = 0
VERSION_MINOR = 1
VERSION_BUILD = 0
VERSION_INFO = (VERSION_MAJOR, VERSION_MINOR, VERSION_BUILD)
VERSION_STRING = '%d.%d.%d' % VERSION_INFO

__version__ = VERSION_STRING
