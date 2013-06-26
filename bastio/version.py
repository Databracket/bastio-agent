# Copyright 2013 Databracket LLC.
# See LICENSE file for details.

"""
:module: bastio.version
:synopsis: A module that contain version details for the package.
:author: Amr Ali <amr@databracket.com>

Update version information here only. There's no need to update any other
file in the package.

Release of a hotfix/bugfix:
- Increment version's ``BUILD`` field.

Release of an update that modifies the API but maintains
backward compatibility:
- Increment version's ``MINOR`` field and reset the ``BUILD`` field.

Release of an update that that modifies the API and breaks
backward compatibility:
- Increment version's ``MAJOR`` field and reset both the ``MINOR`` and ``BUILD`` fields.
"""

__author__ = "Amr Ali"
__copyright__ = "Copyright 2013 Databracket LLC"
__license__ = "GPLv3+"

VERSION_MAJOR = 0
VERSION_MINOR = 1
VERSION_BUILD = 2

# NOTE: DO NOT MODIFY ANYTHING BELOW THIS LINE UNLESS YOU DO KNOW WHAT YOU ARE DOING.

VERSION_INFO = (VERSION_MAJOR, VERSION_MINOR, VERSION_BUILD)
VERSION_STRING = '%d.%d.%d' % VERSION_INFO

__version__ = VERSION_STRING

