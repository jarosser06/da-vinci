Stacks
======

Overview
--------

The Stack class is the foundation for all infrastructure stacks in Da Vinci CDK. It extends AWS CDK's Stack class, adding framework-specific functionality and standardization.

Core Functionality
------------------

- Standardized stack naming (``app_name-deployment_id-stack_name``)
- Stack dependency management
- Docker image configuration
- Framework feature requirements (Event Bus, Exception Trap)

Stack Dependencies
------------------

Stacks can declare dependencies on other stacks, which the framework automatically resolves during deployment:

.. code-block:: python

   from da_vinci_cdk.stack import Stack

   class CustomStack(Stack):
       def __init__(self, scope, construct_id, **kwargs):
           super().__init__(
               scope,
               construct_id,
               required_stacks=[DatabaseStack, StorageStack],
               **kwargs
           )

Framework Integration
---------------------

In addition to the normal dependency declaration, framework stacks can be toggled as dependencies using feature flags. It is always a best practice to specify dependence on the Da Vinci feature stacks when being utilized.

- ``requires_event_bus``: Stack utilizes event loop functionality, either publishing or receiving
- ``requires_exception_trap``: Stack manages code that is expecting exceptions to be trapped

Example
-------

.. code-block:: python

   from da_vinci_cdk.stack import Stack
   from aws_cdk import aws_lambda as lambda_

   class ApiStack(Stack):
       def __init__(self, scope, construct_id, **kwargs):
           super().__init__(
               scope,
               construct_id,
               requires_event_bus=True,
               requires_exception_trap=True,
               **kwargs
           )

           # Create Lambda function
           api_function = lambda_.Function(
               self, "ApiFunction",
               runtime=lambda_.Runtime.PYTHON_3_11,
               handler="index.handler",
               code=lambda_.Code.from_asset("./lambda"),
           )

Creating Custom Stacks
----------------------

When creating custom stacks:

1. **Extend the Stack class** from ``da_vinci_cdk.stack``
2. **Declare dependencies** using ``required_stacks`` parameter
3. **Specify framework requirements** (``requires_event_bus``, ``requires_exception_trap``)
4. **Add your resources** using standard CDK constructs

Best Practices
--------------

**Single Responsibility**
   Each stack should have a clear, single purpose (e.g., DatabaseStack, ApiStack, StorageStack).

**Declare Dependencies**
   Always declare stack dependencies explicitly rather than relying on implicit ordering.

**Feature Requirements**
   Set ``requires_event_bus`` and ``requires_exception_trap`` based on actual usage, not speculatively.

**Naming Convention**
   Use descriptive stack names that clearly indicate the stack's purpose.

**Resource Limits**
   Keep stacks reasonably sized. CloudFormation has limits on the number of resources per stack.
