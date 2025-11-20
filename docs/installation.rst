Installation
============

Requirements
------------

**Python Version**
   - Python 3.11 or higher for ``da_vinci`` (core runtime)
   - Python 3.12 or higher for ``da_vinci_cdk`` (infrastructure)

**AWS Requirements**
   - AWS account with appropriate permissions
   - AWS credentials configured locally
   - AWS CDK CLI installed (for infrastructure deployment)

Installing Da Vinci
--------------------

Using pip
~~~~~~~~~

Da Vinci packages are hosted on a custom PyPI server. You need to specify the extra index URL:

.. code-block:: bash

   pip install --extra-index-url https://packages.davinciproject.dev/simple/ da-vinci da-vinci-cdk

Or install packages individually:

.. code-block:: bash

   pip install --extra-index-url https://packages.davinciproject.dev/simple/ da-vinci
   pip install --extra-index-url https://packages.davinciproject.dev/simple/ da-vinci-cdk

Using Poetry
~~~~~~~~~~~~

If you're using Poetry, add the custom PyPI source:

.. code-block:: bash

   poetry source add --priority=explicit davinciproject https://packages.davinciproject.dev/simple/
   poetry add da-vinci --source davinciproject
   poetry add da-vinci-cdk --source davinciproject

Using uv
~~~~~~~~

If you're using the `uv <https://github.com/astral-sh/uv>`_ package manager:

.. code-block:: bash

   uv add da-vinci da-vinci-cdk --extra-index-url https://packages.davinciproject.dev/simple/

Development Installation
-------------------------

To install Da Vinci for development with all dev dependencies:

.. code-block:: bash

   # Clone the repository
   git clone https://github.com/jarosser06/da-vinci.git
   cd da-vinci

   # Install with uv (recommended)
   uv sync

   # Or with pip
   pip install -e packages/core -e packages/cdk

This installs both packages in editable mode with all development dependencies including testing, linting, and documentation tools.

AWS CDK Installation
--------------------

The CDK package requires the AWS CDK CLI to be installed:

.. code-block:: bash

   npm install -g aws-cdk

Verify the installation:

.. code-block:: bash

   cdk --version

AWS Credentials Setup
---------------------

Da Vinci uses standard AWS credentials. You can configure them using:

**AWS CLI Configuration**

.. code-block:: bash

   aws configure

**Environment Variables**

.. code-block:: bash

   export AWS_ACCESS_KEY_ID=your_access_key
   export AWS_SECRET_ACCESS_KEY=your_secret_key
   export AWS_DEFAULT_REGION=us-east-1

**Credentials File**

Create ``~/.aws/credentials``:

.. code-block:: ini

   [default]
   aws_access_key_id = your_access_key
   aws_secret_access_key = your_secret_key

And ``~/.aws/config``:

.. code-block:: ini

   [default]
   region = us-east-1

Verifying Installation
-----------------------

Verify that Da Vinci core is installed correctly:

.. code-block:: python

   # Verify core package imports
   from da_vinci.core.orm.client import TableClient
   from da_vinci.core.orm.table_object import TableObject
   from da_vinci.event_bus.client import EventPublisher
   print("✓ da_vinci core installed successfully")

To verify CDK installation (requires Node.js):

.. code-block:: python

   # Verify CDK package imports (requires Node.js)
   from da_vinci_cdk.application import Application
   print("✓ da_vinci_cdk installed successfully")

**Note**: The CDK package requires Node.js to be installed because it uses the AWS CDK CLI under the hood. If you see errors about missing 'node', install Node.js first.

Next Steps
----------

Now that you have Da Vinci installed, proceed to the :doc:`quickstart` guide to build your first application.
