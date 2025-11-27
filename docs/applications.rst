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

All events and their processing results are stored in DynamoDB tables, creating a complete audit trail. This includes the original event, when it was published, which subscribers received it, processing status, and any responses. Event data is stored in a structured format that can be queried programmatically.

**Key Benefits**

- Complete audit trail of all events and processing results
- Query event history programmatically via DynamoDB
- Track which functions processed which events
- Identify processing failures and successes
- Add new functions without changing existing code
- Multiple functions can handle the same event
- Function failures stay isolated
- No direct dependencies between functions

**Use When**

- Functions need to trigger other functions
- Multiple actions needed for one event
- Adding features to existing processes
- Building independent processing steps
- Decoupling application components
- Audit trail of event processing required
- Need to query event history programmatically

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

.. _docker-custom-indexes:

Application Dockerfile Requirements
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

When using a custom Dockerfile in your application's ``app_entry`` directory, you must install uv to respect custom package index configurations in your ``pyproject.toml``.

**Why uv is Required**

If your ``pyproject.toml`` specifies a custom package index:

.. code-block:: toml

   [[tool.uv.index]]
   url = "https://packages.example.com/simple/"

Then pip will not respect this configuration. The Dockerfile must use ``uv pip install`` to properly read the index configuration from ``pyproject.toml``.

**Required Dockerfile Pattern**

.. code-block:: dockerfile

   # Image is passed as a build arg by the framework
   ARG IMAGE
   FROM $IMAGE

   # Install uv to respect pyproject.toml index configuration
   RUN pip install uv

   ADD . ${LAMBDA_TASK_ROOT}/myapp
   RUN rm -rf /var/task/myapp/.venv

   # Use uv pip install to respect custom package indexes
   RUN cd ${LAMBDA_TASK_ROOT}/myapp && uv pip install --system .

**Key Points**

- ``pip install uv`` installs uv in the Lambda base image
- ``uv pip install --system`` reads ``[[tool.uv.index]]`` from ``pyproject.toml``
- ``--system`` flag installs packages globally (no virtual environment)
- This pattern works with both PyPI and custom package repositories

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

Sidecar Applications
--------------------

Overview
~~~~~~~~

A sidecar application is a separate CDK application that deploys alongside and connects to an existing da_vinci Application. Sidecars share the parent's operational infrastructure (global settings, event bus, exception trap) but maintain their own stack deployments.

When to Use
~~~~~~~~~~~

Use a sidecar application when you need:

- Auxiliary services that support the main application
- Services with different deployment lifecycles
- Additional infrastructure that shouldn't be in the main app
- Services managed by different teams using the same resources

**Example use cases:**

- Monitoring dashboards that read from main app's exception trap
- Admin tools that modify global settings
- Background processing services triggered by main app events
- Integration services connecting to external systems

How It Works
~~~~~~~~~~~~

**Resource Organization:**

- Sidecar has its own CDK app and CloudFormation stacks
- Shares parent's ``deployment_id`` for consistent resource naming
- Gets unique resource names via ``sidecar_app_name`` prefix
- Connects to parent's infrastructure via resource discovery

**Deployment Requirements:**

1. Parent application must be deployed first
2. Sidecar reads parent's configuration from global settings table
3. Sidecar automatically discovers shared resources
4. Sidecar can add its own stacks and Lambda functions

**Request Flow Differences:**

.. code-block:: none

   Regular Application Service:
   Request → API Gateway → Lambda (in Application stack)
                           ↓
                      Shared Resources

   Sidecar Service:
   Request → API Gateway → Lambda (in SidecarApplication stack)
                           ↓
                      Shared Resources ← Discovered via resource registry

Example
~~~~~~~

.. code-block:: python

   from da_vinci_cdk import Application, SideCarApplication, Stack

   # Main application (deploy first)
   app = Application(
       app_name='customer-portal',
       deployment_id='prod',
       enable_event_bus=True,
       enable_exception_trap=True
   )

   # Sidecar application for admin tools (deploy separately)
   admin_app = SideCarApplication(
       app_name='customer-portal',        # Same as parent
       deployment_id='prod',               # Same as parent
       sidecar_app_name='admin-tools',    # Unique identifier
       app_entry='./admin_src'
   )

   # Add stacks to sidecar
   admin_app.add_uninitialized_stack(AdminDashboardStack)

   # Sidecar functions can access parent's:
   # - Global settings table
   # - Event bus (if enabled)
   # - Exception trap (if enabled)
   # - Resource registry

Limitations
~~~~~~~~~~~

- Parent application must exist and be deployed
- Cannot modify parent application's stacks
- Shares parent's global settings (read/write access)
- Must use same AWS account and region as parent

Best Practices
--------------

Resource Organization
~~~~~~~~~~~~~~~~~~~~~

- Group related resources in purpose-specific stacks
- Store shared configuration in global settings
- Use event bus for component communication
- Use exception trap for error tracking
- Use sidecars for auxiliary services with separate lifecycles

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
