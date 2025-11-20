Core Principles
===============

Da Vinci is built on four foundational principles that guide its design and implementation. Understanding these principles will help you make the most of the framework.

1. Additive Convenience
-----------------------

**Framework provides convenience without blocking direct AWS access**

Da Vinci is designed to make common tasks easier while never preventing you from accessing AWS services directly. This means:

**You Can Always Drop Down**
   If Da Vinci doesn't provide a specific feature, you can always use boto3 or the AWS SDK directly. The framework doesn't lock you in.

.. code-block:: python

   from da_vinci.core.orm.client import TableClient
   import boto3

   # Use Da Vinci for convenience
   client = TableClient(MyTable)
   item = client.get("key-123")

   # Or use boto3 directly when needed
   dynamodb = boto3.resource('dynamodb')
   table = dynamodb.Table('my-table-name')
   response = table.get_item(Key={'id': 'key-123'})

**Mix and Match**
   You can combine framework features with direct AWS calls in the same application. Use what makes sense for each use case.

**No Abstraction Lock-In**
   The framework eliminates boilerplate but doesn't hide AWS services behind heavy abstractions. You still work with familiar AWS concepts.

2. Single Source of Truth
--------------------------

**Centralized definitions drive infrastructure and code**

Da Vinci centralizes configuration and definitions to avoid duplication and ensure consistency.

**Table Definitions**
   Define your DynamoDB tables once, use them everywhere:

.. code-block:: python

   # Define once
   class UserTable(TableObject):
       table_name = "users"
       partition_key_attribute = "user_id"
       # ... attributes ...

   # Use in application code
   client = TableClient(UserTable)

   # Use in infrastructure
   app.add_table(UserTable)

**Configuration Management**
   Centralized configuration accessible across your application.

**Resource Discovery**
   Services discover each other through centralized resource registry.

**Benefits**
   - No duplicate definitions
   - Infrastructure always matches code
   - Single place to update
   - Type safety across stack

3. AWS-Native Development
--------------------------

**Stay close to AWS services, don't hide them**

Da Vinci embraces AWS services rather than abstracting them away.

**Leverage AWS Managed Services**
   Use DynamoDB, SQS, etc. as they were designed, with Da Vinci providing helpers rather than replacements.

**CDK Under the Hood**
   Infrastructure is pure CDK - you can mix Da Vinci constructs with standard CDK constructs.

**AWS Patterns**
   Follow AWS best practices and patterns:

- Event-driven with SQS-based event bus
- Serverless with Lambda
- NoSQL with DynamoDB
- Infrastructure as Code with CDK

4. Operational First
--------------------

**Built-in production-ready patterns**

Da Vinci includes operational concerns from the start, not as an afterthought.

**Error Handling**
   Built-in error handling and exception patterns.

**Service Discovery**
   Automatic service discovery eliminates hardcoded ARNs and names.

**Event Communication**
   First-class support for event-driven architectures.

**Logging and Observability**
   Structured logging built in.

**Configuration Management**
   Environment-aware configuration.

Applying the Principles
------------------------

When building with Da Vinci:

1. **Start with table definitions** - They drive your infrastructure
2. **Use framework features for common patterns** - Table clients, event publishing, service discovery
3. **Drop to boto3 when needed** - Don't fight the framework for edge cases
4. **Think AWS-native** - Embrace managed services and AWS patterns
5. **Build for production** - Use built-in error handling, logging, and configuration

These principles work together to create a framework that accelerates development without sacrificing control or operational excellence.
