Event-Driven Architecture
==========================

This example demonstrates building an event-driven application using Da Vinci's event bus capabilities.

Overview
--------

We'll build a user registration system that:

- Creates user records
- Publishes events when users are created
- Sends welcome emails in response to events
- Updates user statistics when events occur

This demonstrates decoupled, event-driven architecture where components communicate through events rather than direct calls.

Step 1: Define Tables
----------------------

Create ``tables.py``:

.. code-block:: python

   from datetime import UTC, datetime
   from da_vinci.core.orm.table_object import (
       TableObject,
       TableObjectAttribute,
       TableObjectAttributeType,
   )

   class UserTable(TableObject):
       """Table for storing user records"""

       table_name = "users"
       partition_key_attribute = "user_id"

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
               name="name",
               attribute_type=TableObjectAttributeType.STRING,
           ),
           TableObjectAttribute(
               name="status",
               attribute_type=TableObjectAttributeType.STRING,
               default="pending",
           ),
           TableObjectAttribute(
               name="created_at",
               attribute_type=TableObjectAttributeType.DATETIME,
           ),
       ]

   class UserStatsTable(TableObject):
       """Table for tracking user statistics"""

       table_name = "user_stats"
       partition_key_attribute = "stat_key"

       attributes = [
           TableObjectAttribute(
               name="stat_key",
               attribute_type=TableObjectAttributeType.STRING,
           ),
           TableObjectAttribute(
               name="total_users",
               attribute_type=TableObjectAttributeType.NUMBER,
               default=0,
           ),
           TableObjectAttribute(
               name="active_users",
               attribute_type=TableObjectAttributeType.NUMBER,
               default=0,
           ),
           TableObjectAttribute(
               name="updated_at",
               attribute_type=TableObjectAttributeType.DATETIME,
           ),
       ]

Step 2: Create User Service with Events
----------------------------------------

Create ``user_service.py``:

.. code-block:: python

   import uuid
   from datetime import UTC, datetime

   from da_vinci.core.orm.client import TableClient
   from da_vinci.event_bus.client import EventPublisher
   from da_vinci.event_bus.event import Event
   from tables import UserTable


   class UserService:
       """Service for managing users with event publishing"""

       def __init__(self):
           self.client = TableClient(UserTable)
           self.event_publisher = EventPublisher()

       def create_user(self, email: str, name: str) -> UserTable:
           """Create a new user and publish event"""
           user_id = str(uuid.uuid4())
           now = datetime.now(UTC)

           user = UserTable(
               user_id=user_id,
               email=email,
               name=name,
               status="pending",
               created_at=now,
           )

           # Save user
           self.client.put(user)

           # Publish event
           event = Event(
               event_type="user.created",
               body={
                   "user_id": user.user_id,
                   "email": user.email,
                   "name": user.name,
               }
           )
           self.event_publisher.submit(event)

           return user

       def activate_user(self, user_id: str) -> UserTable:
           """Activate a user and publish event"""
           user = self.client.get(user_id)
           user.status = "active"
           self.client.put(user)

           # Publish activation event
           event = Event(
               event_type="user.activated",
               body={
                   "user_id": user.user_id,
                   "email": user.email,
               }
           )
           self.event_publisher.submit(event)

           return user

Step 3: Create Event Handlers
------------------------------

Create ``event_handlers.py``:

.. code-block:: python

   from datetime import UTC, datetime
   from da_vinci.core.orm.client import TableClient
   from tables import UserStatsTable


   def handle_user_created(event: dict) -> None:
       """
       Handler for user.created events
       Sends welcome email
       """
       detail = event.get("detail", {})
       user_email = detail.get("email")
       user_name = detail.get("name")

       # Send welcome email (pseudo-code)
       send_email(
           to=user_email,
           subject="Welcome!",
           body=f"Hello {user_name}, welcome to our platform!"
       )

       print(f"Welcome email sent to {user_email}")


   def handle_user_activated(event: dict) -> None:
       """
       Handler for user.activated events
       Updates user statistics
       """
       stats_client = TableClient(UserStatsTable)

       # Get or create stats record
       stats = stats_client.get("global") or UserStatsTable(
           stat_key="global",
           total_users=0,
           active_users=0,
           updated_at=datetime.now(UTC)
       )

       # Increment counters
       stats.active_users += 1
       stats.updated_at = datetime.now(UTC)

       stats_client.put(stats)
       print(f"Stats updated: {stats.active_users} active users")


   def handle_any_user_event(event: dict) -> None:
       """
       Handler for all user.* events
       Updates total user count
       """
       event_type = event.get("detail-type")

       if event_type == "user.created":
           stats_client = TableClient(UserStatsTable)

           stats = stats_client.get("global") or UserStatsTable(
               stat_key="global",
               total_users=0,
               active_users=0,
               updated_at=datetime.now(UTC)
           )

           stats.total_users += 1
           stats.updated_at = datetime.now(UTC)

           stats_client.put(stats)
           print(f"Stats updated: {stats.total_users} total users")


   def send_email(to: str, subject: str, body: str) -> None:
       """Placeholder for email sending"""
       # In real implementation, use SES or similar
       print(f"Email to {to}: {subject}")

Step 4: Deploy with Event Bus
------------------------------

Create ``app.py``:

.. code-block:: python

   from da_vinci_cdk.application import Application
   from tables import UserTable, UserStatsTable

   # Create application with event bus enabled
   app = Application(
       app_name="user_system",
       deployment_id="dev",
       enable_event_bus=True,  # Enable event bus
   )

   # Add tables
   app.add_table(UserTable)
   app.add_table(UserStatsTable)

   # Note: Event handlers are Lambda functions that are triggered by
   # SQS queues. You would create Lambda functions for your handlers
   # and configure them to consume from the event queues.
   # See the CDK documentation for details on wiring Lambda functions to SQS.

   app.synth()

Step 5: Use the Event-Driven System
------------------------------------

.. code-block:: python

   from user_service import UserService

   # Create service
   service = UserService()

   # Create a user (triggers events)
   user = service.create_user(
       email="alice@example.com",
       name="Alice Smith"
   )
   print(f"Created user: {user.user_id}")

   # This will trigger:
   # 1. user.created event
   # 2. handle_user_created() - sends welcome email
   # 3. handle_any_user_event() - updates total user count

   # Activate the user (triggers more events)
   activated = service.activate_user(user.user_id)
   print(f"Activated user: {activated.user_id}")

   # This will trigger:
   # 1. user.activated event
   # 2. handle_user_activated() - updates active user count

Expected Output:

.. code-block:: text

   Created user: abc-123-def
   Welcome email sent to alice@example.com
   Stats updated: 1 total users

   Activated user: abc-123-def
   Stats updated: 1 active users

Key Concepts
------------

**Event Publisher**
   Publishes events to the event bus when actions occur.

**Event Handlers**
   Lambda functions that respond to specific event types.

**Decoupling**
   Services don't directly call each other - they communicate through events.

**Event Types**
   Use dot notation (``user.created``, ``user.activated``) for event organization.

**Wildcard Subscriptions**
   Use ``*`` to subscribe to multiple related event types.

Benefits
--------

**Extensibility**
   Add new handlers without modifying existing code.

**Reliability**
   If one handler fails, others continue processing.

**Scalability**
   Each handler scales independently.

**Flexibility**
   Multiple handlers can respond to the same event.

Variations
----------

**Add Event Validation**

.. code-block:: python

   from pydantic import BaseModel

   class UserCreatedEvent(BaseModel):
       user_id: str
       email: str
       name: str

   def handle_user_created(event: dict) -> None:
       detail = event.get("detail", {})
       validated = UserCreatedEvent(**detail)
       # Use validated.email, validated.name, etc.

**Add Dead Letter Queue**

Configure DLQ for failed event processing in your CDK:

.. code-block:: python

   app.add_event_handler(
       event_type="user.created",
       handler_function=handle_user_created,
       dead_letter_queue=True,  # Enable DLQ
   )

**Batch Event Processing**

Process events in batches for efficiency:

.. code-block:: python

   def handle_user_events_batch(events: list[dict]) -> None:
       """Process multiple user events at once"""
       for event in events:
           # Process each event
           pass

Next Steps
----------

- Add :doc:`api_backend` to trigger events from HTTP requests
- Implement :doc:`batch_processing` for event replay
- Add event sourcing patterns for audit trails
