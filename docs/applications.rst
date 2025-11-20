Applications
============

Overview
--------

The Application class provides the foundation for building AWS cloud-native applications with minimal boilerplate. It manages infrastructure deployment using AWS CDK with built-in best practices, while providing core operational features like configuration management, error tracking, and service communication.

Key capabilities:

- Infrastructure deployment and management through AWS CDK
- Multi-environment deployments (dev, staging, prod) in a single account
- Built-in operational features (configuration, error handling, pub/sub)
- Docker-based Lambda deployments with automatic dependency management

Core Features
-------------

Global Settings
~~~~~~~~~~~~~~~

Global Settings is a shared configuration table that provides plain-text values accessible by any part of the application. It acts as a central source for application-wide variables.

.. code-block:: python

   enable_global_settings=True  # Default

**How it Works**

All settings are stored in a single DynamoDB table with unrestricted access across the application. Any Lambda function or component can read any setting. **Note**: Values are currently stored as plain text.

**Key Benefits**

- Single source for application-wide variables
- Changes take effect without redeployment
- Accessible from any application component
- Simple key-value storage pattern
- Framework-managed infrastructure

**Use When**

- Defining shared variables across components
- Managing feature flags or toggles
- Configuring framework behavior

Exception Trap
~~~~~~~~~~~~~~

The Exception Trap is a centralized error capturing system for Lambda functions. It automatically stores errors with their full context for later analysis.

**How it Works**

When a Lambda function throws an error, the Exception Trap:

- Captures the full error context (stack trace, event data, metadata)
- Stores it in a central database
- Retains errors for 48 hours by default

**Key Benefits**

- Complete error context in one place
- Automatic cleanup of old errors
- No impact on application behavior
- Simple debugging of production issues
- Error tracking across distributed functions

**Use When**

- Debugging errors
- Analyzing patterns in application failures
- Tracing issues across multiple functions
- Error monitoring needs structure

Event Bus
~~~~~~~~~

The Event Bus enables Lambda functions to communicate using events. Any function can publish an event, and any function can subscribe to receive specific event types.

.. code-block:: python

   enable_event_bus=False  # Default

**How it Works**

Functions publish events with a type and payload. The Event Bus handles delivery to all functions that subscribe to that event type. Subscribers process events independently - if one fails, others continue normally.

**Key Benefits**

- Add new functions without changing existing code
- Multiple functions can handle the same event
- Automatic event delivery and tracking
- Function failures stay isolated
- No direct dependencies between functions
- Managed queuing and routing

**Use When**

- Functions need to trigger other functions
- Multiple actions needed for one event
- Adding features to existing processes
- Building independent processing steps
- Decoupling application components

Deployment Configuration
~~~~~~~~~~~~~~~~~~~~~~~~

The Application combines app_name and deployment_id to create unique resource identifiers, enabling:

- Multiple application deployments in one AWS account
- Clear resource ownership
- Simple development environments

.. code-block:: python

   app = Application(
       app_name='customer-portal',
       deployment_id='dev-team1'
   )  # Resources will be prefixed with 'customer-portal-dev-team1'

Infrastructure Components
~~~~~~~~~~~~~~~~~~~~~~~~~

The Application automatically configures required infrastructure based on enabled features. This includes:

- Core stacks and dependencies
- Docker image management
- Resource permissions
- Cross-stack references

Docker Management
~~~~~~~~~~~~~~~~~

The Application handles container image builds for Lambda functions:

- **Library Base Image**: Contains framework code and dependencies
- **Application Image**: Contains application code

.. code-block:: python

   # Use library base image (recommended)
   app = Application(
       app_name='myapp',
       deployment_id='dev',
       app_entry='./src',
       app_image_use_lib_base=True  # Builds on top of Da Vinci base image
   )

   # Custom application image
   app = Application(
       app_name='myapp',
       deployment_id='dev',
       app_entry='./src',
       app_image_use_lib_base=False  # Uses your Dockerfile from app_entry
   )

Stack Management
~~~~~~~~~~~~~~~~

The Application manages AWS CloudFormation stacks and their dependencies:

.. code-block:: python

   # Framework handles dependencies
   app.add_uninitialized_stack(MyCustomStack)

   # Enable core features
   app = Application(
       app_name='myapp',
       deployment_id='dev',
       enable_event_bus=True,
       enable_exception_trap=True
   )

Best Practices
--------------

Resource Organization
~~~~~~~~~~~~~~~~~~~~~

- Group related resources in purpose-specific stacks
- Store shared configuration in global settings
- Use event bus for component communication
- Use exception trap for error tracking

Environment Isolation
~~~~~~~~~~~~~~~~~~~~~

Use different ``deployment_id`` values for different environments:

.. code-block:: python

   # Development
   app_dev = Application(app_name='myapp', deployment_id='dev')

   # Staging
   app_staging = Application(app_name='myapp', deployment_id='staging')

   # Production
   app_prod = Application(app_name='myapp', deployment_id='prod')

Feature Flags
~~~~~~~~~~~~~

Enable only the features you need:

.. code-block:: python

   app = Application(
       app_name='myapp',
       deployment_id='dev',
       enable_global_settings=True,   # Almost always needed
       enable_exception_trap=True,     # Recommended for production
       enable_event_bus=False,         # Only if using events
   )
