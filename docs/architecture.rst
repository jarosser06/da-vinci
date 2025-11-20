Architecture
============

Understanding how Da Vinci components work together will help you build better applications.

Package Structure
-----------------

Da Vinci consists of two Python packages:

**da_vinci (Core Runtime)**
   Runtime library for application business logic. This is what your application imports and uses at runtime.

**da_vinci_cdk (Infrastructure)**
   CDK constructs for infrastructure deployment. This generates your CloudFormation templates.

These packages work together but have different purposes and can be versioned independently.

How They Work Together
----------------------

The key insight is that **table definitions are shared** between both packages:

1. You define table objects in your application code
2. Your application uses these definitions at runtime (via da_vinci)
3. Your CDK app uses the same definitions to generate infrastructure (via da_vinci_cdk)

This ensures your infrastructure always matches your code.

Runtime Architecture (da_vinci)
--------------------------------

The core package provides several key components:

**ORM Layer**
   - ``TableObject`` - Base class for table definitions
   - ``TableObjectAttribute`` - Define table attributes
   - ``TableClient`` - CRUD operations for tables

**Resource Discovery**
   - ``ResourceDiscovery`` - Find AWS resources by name
   - Eliminates hardcoded ARNs
   - Environment-aware lookups

**Event System**
   - ``EventPublisher`` - Publish events to EventBridge
   - Event-driven architecture support
   - Type-safe event handling

**Configuration**
   - ``GlobalSettings`` - Centralized configuration
   - Environment-specific settings
   - Runtime configuration lookup

**Utilities**
   - Logging helpers
   - JSON serialization
   - Exception types

Infrastructure Architecture (da_vinci_cdk)
-------------------------------------------

The CDK package provides constructs for deployment:

**Application Construct**
   Top-level construct that manages your entire application:

   - Coordinates multiple stacks
   - Manages dependencies
   - Handles cross-stack references

**Table Integration**
   Automatically creates DynamoDB tables from table object definitions:

   - Generates table schema
   - Creates indexes
   - Sets up permissions

**Stack Management**
   Handles CloudFormation stack organization and dependencies.

Data Flow
---------

Here's how data flows through a typical Da Vinci application:

1. **Definition Time**

   You define table objects:

   .. code-block:: python

      class UserTable(TableObject):
          table_name = "users"
          partition_key_attribute = "user_id"
          # ...

2. **Deployment Time**

   CDK generates infrastructure from definitions:

   .. code-block:: python

      app = Application(app_name="my_app", deployment_id="dev")
      app.add_table(UserTable)
      app.synth()  # Generates CloudFormation

3. **Runtime**

   Application uses table client:

   .. code-block:: python

      client = TableClient(UserTable)
      user = client.get("user-123")

Component Interaction
---------------------

**Table Object → Infrastructure**

   Table definitions drive DynamoDB table creation with all attributes, indexes, and settings.

**Table Object → Runtime**

   Same definitions provide type-safe CRUD operations and query building.

**Resource Discovery → Services**

   Services discover each other without hardcoded references:

   .. code-block:: python

      discovery = ResourceDiscovery()
      table_name = discovery.get_table_name("users")

**Events → Communication**

   Services communicate via events:

   .. code-block:: python

      # Service A publishes
      publisher.publish(event_type="user.created", detail={...})

      # Service B consumes (via Lambda trigger)
      def handler(event, context):
          # Process event
          pass

Deployment Model
----------------

Da Vinci applications deploy as CloudFormation stacks:

**Single Stack**
   Simple applications can use a single stack containing all resources.

**Multiple Stacks**
   Complex applications split into multiple stacks with managed dependencies.

**Cross-Stack References**
   Da Vinci handles cross-stack references automatically through resource discovery.

Example Architecture
--------------------

Here's a typical Da Vinci application architecture:

.. code-block:: text

   ┌─────────────────────────────────────────────────┐
   │              CDK Application                     │
   │  (da_vinci_cdk.Application)                     │
   └─────────────────┬───────────────────────────────┘
                     │
        ┌────────────┼────────────┐
        │            │            │
        ▼            ▼            ▼
   ┌────────┐  ┌────────┐  ┌────────┐
   │Stack 1 │  │Stack 2 │  │Stack 3 │
   │        │  │        │  │        │
   │DynamoDB│  │Lambda  │  │API GW  │
   │Tables  │  │Functions│  │        │
   └────────┘  └────────┘  └────────┘
        │            │            │
        └────────────┴────────────┘
                     │
                     ▼
        ┌─────────────────────────┐
        │   Runtime Application    │
        │   (Uses da_vinci)       │
        │                         │
        │  TableClient            │
        │  ResourceDiscovery      │
        │  EventPublisher         │
        └─────────────────────────┘

Best Practices
--------------

**Organize by Domain**
   Group related tables, functions, and resources together.

**Use Resource Discovery**
   Never hardcode ARNs or resource names. Use ResourceDiscovery to look them up at runtime.

**Centralize Table Definitions**
   Keep all table definitions in one module that both runtime and CDK code can import.

**Environment Isolation**
   Use different deployment_id values for different environments (dev, staging, prod).

**Event-Driven Communication**
   Use events for service-to-service communication rather than direct calls.

**Single Responsibility Stacks**
   Each stack should have a clear purpose and minimal dependencies.

Extensibility
-------------

Da Vinci is designed to be extended:

**Custom Table Clients**
   Extend TableClient for domain-specific operations.

**Custom CDK Constructs**
   Mix Da Vinci constructs with your own CDK constructs.

**Custom Events**
   Define your own event types and handlers.

**Direct AWS Access**
   Drop down to boto3 when needed for operations not covered by the framework.
