.. include:: global.rst.inc

.. _configuration:

Configuration
=============

We've made |project_name| to be very easy to configure. Ideally you shouldn't be
required to do anything beyond configuring your ``API`` key but that depends on
how you've installed |project_name|. We will mainly talk about Debian based
distributions here unless specified otherwise. See :ref:`installation` for the
different ways you could install |project_name|.

Fresh install configurations
----------------------------

After you have installed |project_name| successfully you will need configure your
API key. Edit the configuration file ``/etc/bastio/agent.conf`` and set your API
key to the ``api_key`` variable. Now you will need to generate an agent's key that
will be unique to the particular server you've installed it on. Run the following
command as ``root`` to generate a new agent-key::

    # bastio-agent --config /etc/bastio/agent.conf generate-key --bits 2048

Or::

    # bastio-agent --agent-key /etc/bastio/agent.key generate-key --bits 2048

After generating the new agent-key you will need to upload it to signal the
enrollment of a new server under your account. Run the following command::

    # bastio-agent --config /etc/bastio/agent.conf upload-key

Or::

    # bastio-agent --agent-key /etc/bastio/agent.key upload-key --api-key <API KEY>

Now your new |project_name| installation is ready. Make sure to start or restart
the daemon after any modification to the configuration file or key(s).

.. warning::
    The order of command line arguments is important.

Replace the old agent key with a new one
----------------------------------------

In case of agent key compromise or that you simply wish to replace it, all you have
to do is generate a new agent-key. Run the following commands as ``root`` to replace
the old agent-key with a new one::

    # mv /etc/bastio/agent.key /etc/bastio/agent.key.old
    # bastio-agent --config /etc/bastio/agent.conf generate-key --bits 2048
    # bastio-agent --config /etc/bastio/agent.conf -k /etc/bastio/agent.key.old upload-key \
    #   --new-agent-key /etc/bastio/agent.key

.. warning::
    Uploading a new agent-key without specifying the old agent-key will
    create a new adjacent server-entry in our database for the same server.

