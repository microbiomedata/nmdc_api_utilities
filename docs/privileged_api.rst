Privileged API Reference
========================

.. warning::
   Classes on this page target privileged endpoints and require valid ``NMDCAuth`` credentials.
   They are intended for authorized users who need metadata submission, identifier minting, or staging workflows.

Authentication Support
----------------------

``NMDCAuth`` is required for all privileged classes on this page.

.. autoclass:: nmdc_client.auth.NMDCAuth
   :members:
   :undoc-members:
   :show-inheritance:

Authentication Requirement
--------------------------

Instantiate ``NMDCAuth`` and pass it to privileged classes:

.. code-block:: python

   from nmdc_client.auth import NMDCAuth
   from nmdc_client.metadata import Metadata

   auth = NMDCAuth(client_id="YOUR_CLIENT_ID", client_secret="YOUR_CLIENT_SECRET")
   metadata_client = Metadata(auth=auth)

Metadata Submission
-------------------

.. autoclass:: nmdc_client.metadata.Metadata
   :members:
   :undoc-members:
   :show-inheritance:

Identifier Minting
------------------

.. autoclass:: nmdc_client.minter.Minter
   :members:
   :undoc-members:
   :show-inheritance:

Data Staging and Workflow Management
------------------------------------

.. autoclass:: nmdc_client.data_staging.JGISequencingProjectAPI
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: nmdc_client.data_staging.JGISampleSearchAPI
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: nmdc_client.data_staging.GlobusTaskAPI
   :members:
   :undoc-members:
   :show-inheritance:

Related Pages
-------------

- :doc:`functions` for public core APIs
- :doc:`public_subclasses` for public collection subclasses
