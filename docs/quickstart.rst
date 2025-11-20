Quick Start Guide
=================

This guide walks you through creating your first Da Vinci application.

Prerequisites
-------------

Before starting, ensure you have:

- Python 3.11+ installed (Python 3.12+ required for CDK)
- AWS account with appropriate permissions (DynamoDB, Lambda, CloudFormation)
- AWS credentials configured (``aws configure``)
- AWS CDK CLI installed (``npm install -g aws-cdk``)
- Da Vinci packages installed (see :doc:`installation`)

Creating Your First Application
--------------------------------

Step 1: Define a DynamoDB Table
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Create a file called ``tables.py`` to define your DynamoDB tables:

.. code-block:: python

   from da_vinci.core.orm.table_object import (
       TableObject,
       TableObjectAttribute,
       TableObjectAttributeType,
   )

   class UserTable(TableObject):
       """User table for storing user information"""

       table_name = "users"
       partition_key_attribute = "user_id"

       attributes = [
           TableObjectAttribute(
               name="user_id",
               attribute_type=TableObjectAttributeType.STRING,
               description="Unique user identifier",
           ),
           TableObjectAttribute(
               name="email",
               attribute_type=TableObjectAttributeType.STRING,
               description="User email address",
           ),
           TableObjectAttribute(
               name="name",
               attribute_type=TableObjectAttributeType.STRING,
               description="User display name",
           ),
           TableObjectAttribute(
               name="created_at",
               attribute_type=TableObjectAttributeType.DATETIME,
               description="When the user was created",
           ),
       ]

Step 2: Create Application Logic
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Create a file called ``user_service.py`` for your business logic:

.. code-block:: python

   from datetime import UTC, datetime
   from da_vinci.core.orm.client import TableClient
   from tables import UserTable

   class UserService:
       def __init__(self):
           self.table_client = TableClient(UserTable)

       def create_user(self, user_id: str, email: str, name: str):
           """Create a new user"""
           user = UserTable(
               user_id=user_id,
               email=email,
               name=name,
               created_at=datetime.now(UTC),
           )
           self.table_client.put(user)
           return user

       def get_user(self, user_id: str):
           """Retrieve a user by ID"""
           return self.table_client.get(user_id)

       def list_users(self):
           """List all users"""
           return list(self.table_client.scan())

Step 3: Deploy Infrastructure with CDK
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Create a file called ``app.py`` for your CDK infrastructure:

.. code-block:: python

   from da_vinci_cdk.application import Application
   from tables import UserTable

   # Create application
   app = Application(
       app_name="my_app",
       deployment_id="dev",
   )

   # Add tables to application
   # This automatically creates the DynamoDB infrastructure
   app.add_table(UserTable)

   # Synthesize CDK stacks
   app.synth()

Step 4: Deploy to AWS
~~~~~~~~~~~~~~~~~~~~~~

Deploy your application to AWS using the CDK CLI:

.. code-block:: bash

   # Bootstrap CDK (first time only)
   cdk bootstrap

   # Deploy the application
   cdk deploy --all

Step 5: Use Your Application
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Now you can use your application:

.. code-block:: python

   from user_service import UserService

   # Create service instance
   service = UserService()

   # Create a user
   user = service.create_user(
       user_id="user-123",
       email="alice@example.com",
       name="Alice Smith"
   )

   # Retrieve the user
   retrieved_user = service.get_user("user-123")
   print(f"User: {retrieved_user.name} ({retrieved_user.email})")

   # List all users
   users = service.list_users()
   for user in users:
       print(f"- {user.name}")

Summary
-------

In these steps, you:

1. **Defined a DynamoDB table** using Da Vinci's table object system
2. **Created business logic** using the table client for CRUD operations
3. **Deployed infrastructure** automatically from your table definitions
4. **Used your application** with type-safe table objects

Key Concepts
------------

**Table Objects**
   Table objects define both your data model and drive infrastructure generation. They provide type safety and eliminate boilerplate for DynamoDB operations.

**Table Client**
   The table client provides methods for interacting with DynamoDB tables: ``put()``, ``get()``, ``scan()``, ``query()``, and more.

**Application**
   The CDK Application construct manages your infrastructure deployment, automatically creating resources from your table definitions.

Next Steps
----------

Now that you've built your first application, explore:

- :doc:`architecture` - Understand how Da Vinci components work together
- :doc:`examples/index` - See more complex examples
- :doc:`api/core` - Dive into the core API reference
- :doc:`api/cdk` - Learn about CDK constructs and patterns

Common Patterns
---------------

**Adding Indexes**

.. code-block:: python

   class UserTable(TableObject):
       table_name = "users"
       partition_key_attribute = "user_id"

       # Add a GSI for querying by email
       global_secondary_indexes = [
           {
               "index_name": "email_index",
               "partition_key": "email",
           }
       ]

**Querying with Indexes**

.. code-block:: python

   # Query by email using GSI
   users = table_client.query(
       index_name="email_index",
       partition_key_value="alice@example.com"
   )

**Using Scan Filters**

.. code-block:: python

   from da_vinci.core.orm.client import TableScanDefinition

   # Scan with filter
   scan_def = TableScanDefinition(UserTable)
   scan_def.add("email", "contains", "@example.com")

   users = table_client.scan(scan_definition=scan_def)

Troubleshooting
---------------

**Table Not Found**
   Ensure you've deployed your infrastructure with ``cdk deploy --all`` and that your AWS credentials are configured correctly.

**Import Errors**
   Make sure both ``da-vinci`` and ``da-vinci-cdk`` are installed in your environment.

**Permission Errors**
   Ensure your AWS credentials have permissions to create DynamoDB tables and other required resources.
