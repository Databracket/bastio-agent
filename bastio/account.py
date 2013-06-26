# Copyright 2013 Databracket LLC
# See LICENSE file for details.

"""
:module: bastio.account
:synopsis: A module responsible for communicating account details.
:author: Amr Ali <amr@databracket.com>

.. autofunction:: download_backend_hostkey

.. autofunction:: upload_public_key
"""

__author__ = "Amr Ali"
__copyright__ = "Copyright 2013 Databracket LLC"
__license__ = "GPLv3+"

import requests

from bastio import __version__
from bastio.mixin import public, Json
from bastio.ssh.crypto import RSAKey
from bastio.excepts import BastioAccountError, reraise

# Endpoints
__base_url = 'https://bastio.com/api/external/'
__download_hostkey_endpoint = __base_url + 'backend/host_key'
__upload_key_endpoint = __base_url + 'server/upload_key'

def __send_request(method, **kwargs):
    try:
        method = getattr(requests, method)
        client_version = "Bastio Agent v{}".format(__version__)
        if 'headers' not in kwargs:
            kwargs['headers'] = {}
        kwargs['headers'].update({'User-Agent': client_version})
        return method(**kwargs)
    except requests.exceptions.SSLError:
        reraise(BastioAccountError, "SSL verification failed")
    except requests.exceptions.RequestException:
        reraise(BastioAccountError)
    except Exception as ex:
        reraise(BastioAccountError,
                "request unhandled exception occurred: " + ex.message)

@public
def download_backend_hostkey():
    """Get Bastio's backend SSH host key.

    :returns:
        :class:`bastio.ssh.crypto.RSAKey`
    :raises:
        :class:`bastio.excepts.BastioAccountError`
    """
    errmsg = "get backend host key failed: "

    response = __send_request('get', url=__download_hostkey_endpoint, verify=True)
    if response.status_code != requests.codes.okay: # 200
        raise BastioAccountError(errmsg + "unable to retrieve backend's host key")

    public_key = response.json()['payload']
    if not RSAKey.validate_public_key(public_key):
        raise BastioAccountError(errmsg + "invalid host key")
    return RSAKey.from_public_key(public_key)

@public
def upload_public_key(api_key, public_key, old_public_key=None):
    """Upload agent's public key to Bastio on the account specified by ``api_key``.

    This action will create a new server when ``old_public_key`` is not specified
    and it is the first time we see this ``public_key``. However the public key
    we store that identifies this server will be replaced IFF we already have
    ``old_public_key`` in our records and ``public_key`` does not exist in our
    database.

    :param api_key:
        The API key for the Bastio account.
    :type api_key:
        str
    :param public_key:
        The agent's public key to be uploaded to Bastio's servers.
    :type public_key:
        The string output of :func:`bastio.ssh.crypto.RSAKey.get_public_key`.
    :param old_public_key:
        The agent's old public key to be replaced by a new one.
    :type old_public_key:
        The string output of :func:`bastio.ssh.crypto.RSAKey.get_public_key`.
    :raises:
        :class:`bastio.excepts.BastioAccountError`
    """
    errmsg = "upload public key failed: "

    if not old_public_key:
        old_public_key = ''

    if old_public_key and not RSAKey.validate_public_key(old_public_key):
        raise BastioAccountError(errmsg + "invalid old public key")

    if not RSAKey.validate_public_key(public_key):
        raise BastioAccountError(errmsg + "invalid new public key")

    payload = Json()
    payload.api_key = api_key
    payload.public_key = public_key
    payload.old_public_key = old_public_key

    headers = {'Content-type': 'application/json'}
    response = __send_request('post', url=__upload_key_endpoint, verify=True,
            data=payload.to_json(), headers=headers)
    if response.status_code == requests.codes.bad: # 400
        raise BastioAccountError(errmsg + "missing or invalid field")
    elif response.status_code == requests.codes.forbidden: # 403
        raise BastioAccountError(errmsg + "not authorized or invalid API key")
    elif response.status_code == requests.codes.okay: # 200
        return

    # An unexpected response status code
    raise BastioAccountError(
            errmsg + "unexpected response status code ({})".format(
                response.status_code))

