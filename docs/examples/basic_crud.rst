Basic CRUD Application
======================

This example demonstrates a simple CRUD (Create, Read, Update, Delete) application using Da Vinci and DynamoDB.

Overview
--------

We'll build a task management application where users can:

- Create tasks
- Read task details
- Update task status
- Delete tasks
- List all tasks

Step 1: Define the Table
-------------------------

Create ``tables.py``:

.. code-block:: python

   from datetime import UTC, datetime
   from da_vinci.core.orm.table_object import (
       TableObject,
       TableObjectAttribute,
       TableObjectAttributeType,
   )

   class TaskTable(TableObject):
       """Table for storing tasks"""

       table_name = "tasks"
       partition_key_attribute = "task_id"

       attributes = [
           TableObjectAttribute(
               name="task_id",
               attribute_type=TableObjectAttributeType.STRING,
               description="Unique task identifier",
           ),
           TableObjectAttribute(
               name="title",
               attribute_type=TableObjectAttributeType.STRING,
               description="Task title",
           ),
           TableObjectAttribute(
               name="description",
               attribute_type=TableObjectAttributeType.STRING,
               description="Task description",
               optional=True,
           ),
           TableObjectAttribute(
               name="status",
               attribute_type=TableObjectAttributeType.STRING,
               description="Task status (pending, in_progress, completed)",
               default="pending",
           ),
           TableObjectAttribute(
               name="priority",
               attribute_type=TableObjectAttributeType.NUMBER,
               description="Priority level (1-5)",
               default=3,
           ),
           TableObjectAttribute(
               name="created_at",
               attribute_type=TableObjectAttributeType.DATETIME,
               description="When the task was created",
           ),
           TableObjectAttribute(
               name="updated_at",
               attribute_type=TableObjectAttributeType.DATETIME,
               description="When the task was last updated",
           ),
       ]

Step 2: Create Service Layer
-----------------------------

Create ``task_service.py``:

.. code-block:: python

   import uuid
   from datetime import UTC, datetime
   from typing import Optional

   from da_vinci.core.orm.client import TableClient, TableScanDefinition
   from da_vinci.core.exceptions import ResourceNotFoundError
   from tables import TaskTable


   class TaskService:
       """Service for managing tasks"""

       def __init__(self):
           self.client = TableClient(TaskTable)

       def create_task(
           self,
           title: str,
           description: Optional[str] = None,
           priority: int = 3,
       ) -> TaskTable:
           """Create a new task"""
           now = datetime.now(UTC)
           task_id = str(uuid.uuid4())

           task = TaskTable(
               task_id=task_id,
               title=title,
               description=description,
               status="pending",
               priority=priority,
               created_at=now,
               updated_at=now,
           )

           self.client.put(task)
           return task

       def get_task(self, task_id: str) -> TaskTable:
           """Get a task by ID"""
           task = self.client.get(task_id)
           if not task:
               raise ResourceNotFoundError(f"Task {task_id} not found")
           return task

       def update_task_status(self, task_id: str, status: str) -> TaskTable:
           """Update task status"""
           task = self.get_task(task_id)
           task.status = status
           task.updated_at = datetime.now(UTC)
           self.client.put(task)
           return task

       def update_task(
           self,
           task_id: str,
           title: Optional[str] = None,
           description: Optional[str] = None,
           priority: Optional[int] = None,
       ) -> TaskTable:
           """Update task details"""
           task = self.get_task(task_id)

           if title is not None:
               task.title = title
           if description is not None:
               task.description = description
           if priority is not None:
               task.priority = priority

           task.updated_at = datetime.now(UTC)
           self.client.put(task)
           return task

       def delete_task(self, task_id: str) -> None:
           """Delete a task"""
           self.client.delete(task_id)

       def list_tasks(self, status: Optional[str] = None) -> list[TaskTable]:
           """List all tasks, optionally filtered by status"""
           if status:
               scan_def = TableScanDefinition(TaskTable)
               scan_def.add("status", "equal", status)
               return list(self.client.scan(scan_definition=scan_def))
           else:
               return list(self.client.scan())

       def list_tasks_by_priority(self, min_priority: int) -> list[TaskTable]:
           """List tasks with priority >= min_priority"""
           scan_def = TableScanDefinition(TaskTable)
           scan_def.add("priority", "greater_than_or_equal", min_priority)
           return list(self.client.scan(scan_definition=scan_def))

Step 3: Deploy Infrastructure
------------------------------

Create ``app.py``:

.. code-block:: python

   from da_vinci_cdk.application import Application
   from tables import TaskTable

   # Create application
   app = Application(
       app_name="task_manager",
       deployment_id="dev",
   )

   # Add task table
   app.add_table(TaskTable)

   # Synthesize CDK
   app.synth()

Deploy:

.. code-block:: bash

   cdk bootstrap  # First time only
   cdk deploy --all

Step 4: Use the Application
----------------------------

.. code-block:: python

   from task_service import TaskService

   # Initialize service
   service = TaskService()

   # Create tasks
   task1 = service.create_task(
       title="Write documentation",
       description="Complete the user guide",
       priority=5
   )

   task2 = service.create_task(
       title="Review pull requests",
       priority=4
   )

   task3 = service.create_task(
       title="Fix bug in login",
       description="Users can't login on mobile",
       priority=5
   )

   # Get a task
   task = service.get_task(task1.task_id)
   print(f"Task: {task.title} - Status: {task.status}")

   # Update task status
   service.update_task_status(task1.task_id, "in_progress")
   service.update_task_status(task2.task_id, "completed")

   # Update task details
   service.update_task(
       task3.task_id,
       description="Users can't login on mobile - login button not responding"
   )

   # List all tasks
   all_tasks = service.list_tasks()
   print(f"\nAll tasks ({len(all_tasks)}):")
   for task in all_tasks:
       print(f"  - {task.title} [{task.status}]")

   # List pending tasks
   pending = service.list_tasks(status="pending")
   print(f"\nPending tasks ({len(pending)}):")
   for task in pending:
       print(f"  - {task.title}")

   # List high priority tasks
   high_priority = service.list_tasks_by_priority(min_priority=4)
   print(f"\nHigh priority tasks ({len(high_priority)}):")
   for task in high_priority:
       print(f"  - {task.title} (Priority: {task.priority})")

   # Delete a task
   service.delete_task(task2.task_id)

Expected Output:

.. code-block:: text

   Task: Write documentation - Status: pending

   All tasks (3):
     - Write documentation [in_progress]
     - Review pull requests [completed]
     - Fix bug in login [pending]

   Pending tasks (1):
     - Fix bug in login

   High priority tasks (3):
     - Write documentation (Priority: 5)
     - Review pull requests (Priority: 4)
     - Fix bug in login (Priority: 5)

Key Concepts
------------

**Table Definition**
   The ``TaskTable`` class defines the table schema with typed attributes.

**Service Layer**
   The ``TaskService`` class encapsulates business logic and table operations.

**TableClient**
   Provides methods for CRUD operations (``get``, ``put``, ``delete``, ``scan``).

**Scan Filters**
   Use ``TableScanDefinition`` to filter results when scanning the table.

**Type Safety**
   Table objects provide type-safe access to attributes.

Variations
----------

**Add GSI for Status Queries**

.. code-block:: python

   class TaskTable(TableObject):
       # ... existing code ...

       global_secondary_indexes = [
           {
               "index_name": "status_priority_index",
               "partition_key": "status",
               "sort_key": "priority",
           }
       ]

   # Query instead of scan
   tasks = client.query(
       index_name="status_priority_index",
       partition_key_value="pending"
   )

**Add Batch Operations**

.. code-block:: python

   def create_tasks_batch(self, tasks_data: list[dict]) -> list[TaskTable]:
       """Create multiple tasks at once"""
       tasks = []
       for data in tasks_data:
           task = self.create_task(**data)
           tasks.append(task)
       return tasks

Next Steps
----------

- Add :doc:`event_driven` capabilities to notify when tasks change
- Implement :doc:`api_backend` to expose tasks via REST API
- Add user assignment with :doc:`multi_table` relationships
