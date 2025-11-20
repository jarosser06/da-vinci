DynamoDB Tables
===============

Table definitions are the heart of Da Vinci. They serve as the single source of truth for both your application code and infrastructure.

Table Objects
-------------

Table objects define your DynamoDB tables using Python classes that inherit from ``TableObject``.

Basic Table Definition
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from da_vinci.core.orm.table_object import (
       TableObject,
       TableObjectAttribute,
       TableObjectAttributeType,
   )

   class UserTable(TableObject):
       """User table for storing user profiles"""

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
               description="User full name",
           ),
       ]

Attribute Types
---------------

Da Vinci supports various attribute types:

**STRING**
   Plain text strings

**NUMBER**
   Numeric values (integers or floats)

**BOOLEAN**
   True/False values

**DATETIME**
   Python datetime objects (stored as ISO strings)

**JSON**
   Native DynamoDB JSON (not safe for empty attributes)

**JSON_STRING**
   JSON serialized as string (safe for empty attributes)

**STRING_LIST**
   List of strings

**NUMBER_LIST**
   List of numbers

**JSON_LIST**
   List of JSON objects (native)

**JSON_STRING_LIST**
   List of JSON objects (as strings)

**COMPOSITE_STRING**
   Multiple values combined into a single string (useful for composite keys)

**STRING_SET**
   DynamoDB string set

**NUMBER_SET**
   DynamoDB number set

Example with Various Types
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   class ProductTable(TableObject):
       table_name = "products"
       partition_key_attribute = "product_id"

       attributes = [
           TableObjectAttribute(
               name="product_id",
               attribute_type=TableObjectAttributeType.STRING,
           ),
           TableObjectAttribute(
               name="price",
               attribute_type=TableObjectAttributeType.NUMBER,
           ),
           TableObjectAttribute(
               name="in_stock",
               attribute_type=TableObjectAttributeType.BOOLEAN,
           ),
           TableObjectAttribute(
               name="tags",
               attribute_type=TableObjectAttributeType.STRING_LIST,
           ),
           TableObjectAttribute(
               name="metadata",
               attribute_type=TableObjectAttributeType.JSON_STRING,
           ),
           TableObjectAttribute(
               name="created_at",
               attribute_type=TableObjectAttributeType.DATETIME,
           ),
       ]

Composite Keys
--------------

Use composite strings for multi-part partition or sort keys:

.. code-block:: python

   class OrderItemTable(TableObject):
       table_name = "order_items"
       partition_key_attribute = "composite_key"
       sort_key_attribute = "item_id"

       attributes = [
           TableObjectAttribute(
               name="composite_key",
               attribute_type=TableObjectAttributeType.COMPOSITE_STRING,
               argument_names=["order_id", "user_id"],
           ),
           TableObjectAttribute(
               name="item_id",
               attribute_type=TableObjectAttributeType.STRING,
           ),
           TableObjectAttribute(
               name="quantity",
               attribute_type=TableObjectAttributeType.NUMBER,
           ),
       ]

   # Usage
   item = OrderItemTable(
       order_id="order-123",
       user_id="user-456",
       item_id="item-789",
       quantity=2
   )

Global Secondary Indexes
-------------------------

Add GSIs for alternative query patterns:

.. code-block:: python

   class UserTable(TableObject):
       table_name = "users"
       partition_key_attribute = "user_id"

       global_secondary_indexes = [
           {
               "index_name": "email_index",
               "partition_key": "email",
           },
           {
               "index_name": "status_created_index",
               "partition_key": "status",
               "sort_key": "created_at",
           },
       ]

       attributes = [
           TableObjectAttribute(
               name="user_id",
               attribute_type=TableObjectAttributeType.STRING,
           ),
           TableObjectAttribute(
               name="email",
               attribute_type=TableObjectAttributeType.STRING,
           ),
           TableObjectAttribute(
               name="status",
               attribute_type=TableObjectAttributeType.STRING,
           ),
           TableObjectAttribute(
               name="created_at",
               attribute_type=TableObjectAttributeType.DATETIME,
           ),
       ]

Local Secondary Indexes
-----------------------

Add LSIs for alternative sort key patterns on the same partition key:

.. code-block:: python

   class EventTable(TableObject):
       table_name = "events"
       partition_key_attribute = "user_id"
       sort_key_attribute = "event_id"

       local_secondary_indexes = [
           {
               "index_name": "user_timestamp_index",
               "sort_key": "timestamp",
           },
       ]

       attributes = [
           TableObjectAttribute(
               name="user_id",
               attribute_type=TableObjectAttributeType.STRING,
           ),
           TableObjectAttribute(
               name="event_id",
               attribute_type=TableObjectAttributeType.STRING,
           ),
           TableObjectAttribute(
               name="timestamp",
               attribute_type=TableObjectAttributeType.DATETIME,
           ),
       ]

Optional Attributes and Defaults
---------------------------------

Make attributes optional or provide default values:

.. code-block:: python

   class ConfigTable(TableObject):
       table_name = "config"
       partition_key_attribute = "key"

       attributes = [
           TableObjectAttribute(
               name="key",
               attribute_type=TableObjectAttributeType.STRING,
           ),
           TableObjectAttribute(
               name="value",
               attribute_type=TableObjectAttributeType.STRING,
           ),
           TableObjectAttribute(
               name="enabled",
               attribute_type=TableObjectAttributeType.BOOLEAN,
               default=True,  # Default value
           ),
           TableObjectAttribute(
               name="description",
               attribute_type=TableObjectAttributeType.STRING,
               optional=True,  # Explicitly optional
           ),
       ]

Custom Import/Export
--------------------

Use custom functions to transform data during import/export:

.. code-block:: python

   def encrypt_data(value):
       # Custom encryption logic
       return encrypted_value

   def decrypt_data(value):
       # Custom decryption logic
       return decrypted_value

   class SecureTable(TableObject):
       table_name = "secure_data"
       partition_key_attribute = "id"

       attributes = [
           TableObjectAttribute(
               name="id",
               attribute_type=TableObjectAttributeType.STRING,
           ),
           TableObjectAttribute(
               name="sensitive_data",
               attribute_type=TableObjectAttributeType.STRING,
               custom_exporter=encrypt_data,
               custom_importer=decrypt_data,
           ),
       ]

Table Client Operations
------------------------

Use the TableClient for CRUD operations:

**Get Item**

.. code-block:: python

   from da_vinci.core.orm.client import TableClient

   client = TableClient(UserTable)
   user = client.get("user-123")

**Put Item**

.. code-block:: python

   user = UserTable(
       user_id="user-123",
       email="alice@example.com",
       name="Alice"
   )
   client.put(user)

**Delete Item**

.. code-block:: python

   client.delete("user-123")

**Scan Table**

.. code-block:: python

   # Scan all items
   for user in client.scan():
       print(user.name)

   # Scan with filter
   from da_vinci.core.orm.client import TableScanDefinition

   scan_def = TableScanDefinition(UserTable)
   scan_def.add("email", "contains", "@example.com")

   for user in client.scan(scan_definition=scan_def):
       print(user.email)

**Query Index**

.. code-block:: python

   # Query GSI
   users = client.query(
       index_name="email_index",
       partition_key_value="alice@example.com"
   )

   # Query with sort key condition
   users = client.query(
       index_name="status_created_index",
       partition_key_value="active",
       sort_key_condition="created_at > :date",
       expression_values={":date": some_date}
   )

Best Practices
--------------

**Centralize Definitions**
   Keep all table definitions in a single module (e.g., ``tables.py``) that both runtime and CDK code can import.

**Use Descriptive Names**
   Give tables and attributes clear, descriptive names that indicate their purpose.

**Add Descriptions**
   Use the ``description`` parameter for documentation and LLM context.

**Choose Appropriate Types**
   Use ``JSON_STRING`` instead of ``JSON`` if you need to store empty values.

**Index Wisely**
   Only create indexes you actually need. Each GSI has a cost.

**Consider Access Patterns**
   Design your partition and sort keys based on how you'll query the data.

**Use Composite Keys When Needed**
   Composite keys allow multiple attributes to form a single key, enabling more flexible access patterns.
