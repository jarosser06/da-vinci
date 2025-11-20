Batch Processing Pipeline
=========================

This example demonstrates building a batch data processing pipeline using Da Vinci.

Overview
--------

We'll create a data processing pipeline that:

- Imports data from S3
- Processes records in batches
- Stores results in DynamoDB
- Tracks processing status
- Handles failures gracefully

Table Definitions
-----------------

.. code-block:: python

   from da_vinci.core.orm.table_object import (
       TableObject,
       TableObjectAttribute,
       TableObjectAttributeType,
   )

   class DataRecordTable(TableObject):
       """Table for processed data records"""

       table_name = "data_records"
       partition_key_attribute = "record_id"

       global_secondary_indexes = [
           {
               "index_name": "batch_status_index",
               "partition_key": "batch_id",
               "sort_key": "status",
           }
       ]

       attributes = [
           TableObjectAttribute(
               name="record_id",
               attribute_type=TableObjectAttributeType.STRING,
           ),
           TableObjectAttribute(
               name="batch_id",
               attribute_type=TableObjectAttributeType.STRING,
           ),
           TableObjectAttribute(
               name="source_data",
               attribute_type=TableObjectAttributeType.JSON_STRING,
           ),
           TableObjectAttribute(
               name="processed_data",
               attribute_type=TableObjectAttributeType.JSON_STRING,
               optional=True,
           ),
           TableObjectAttribute(
               name="status",
               attribute_type=TableObjectAttributeType.STRING,
               default="pending",
           ),
           TableObjectAttribute(
               name="error_message",
               attribute_type=TableObjectAttributeType.STRING,
               optional=True,
           ),
           TableObjectAttribute(
               name="created_at",
               attribute_type=TableObjectAttributeType.DATETIME,
           ),
           TableObjectAttribute(
               name="processed_at",
               attribute_type=TableObjectAttributeType.DATETIME,
               optional=True,
           ),
       ]

   class BatchJobTable(TableObject):
       """Table for tracking batch jobs"""

       table_name = "batch_jobs"
       partition_key_attribute = "batch_id"

       attributes = [
           TableObjectAttribute(
               name="batch_id",
               attribute_type=TableObjectAttributeType.STRING,
           ),
           TableObjectAttribute(
               name="s3_key",
               attribute_type=TableObjectAttributeType.STRING,
           ),
           TableObjectAttribute(
               name="total_records",
               attribute_type=TableObjectAttributeType.NUMBER,
               default=0,
           ),
           TableObjectAttribute(
               name="processed_records",
               attribute_type=TableObjectAttributeType.NUMBER,
               default=0,
           ),
           TableObjectAttribute(
               name="failed_records",
               attribute_type=TableObjectAttributeType.NUMBER,
               default=0,
           ),
           TableObjectAttribute(
               name="status",
               attribute_type=TableObjectAttributeType.STRING,
               default="running",
           ),
           TableObjectAttribute(
               name="started_at",
               attribute_type=TableObjectAttributeType.DATETIME,
           ),
           TableObjectAttribute(
               name="completed_at",
               attribute_type=TableObjectAttributeType.DATETIME,
               optional=True,
           ),
       ]

Batch Processor
---------------

.. code-block:: python

   import json
   import uuid
   from datetime import UTC, datetime
   from typing import Any

   import boto3
   from da_vinci.core.orm.client import TableClient
   from tables import DataRecordTable, BatchJobTable


   class BatchProcessor:
       """Process data in batches from S3"""

       def __init__(self):
           self.record_client = TableClient(DataRecordTable)
           self.job_client = TableClient(BatchJobTable)
           self.s3 = boto3.client('s3')

       def start_batch(self, s3_bucket: str, s3_key: str) -> str:
           """Start a new batch processing job"""
           batch_id = str(uuid.uuid4())

           # Create batch job record
           job = BatchJobTable(
               batch_id=batch_id,
               s3_key=f"s3://{s3_bucket}/{s3_key}",
               total_records=0,
               processed_records=0,
               failed_records=0,
               status="running",
               started_at=datetime.now(UTC),
           )
           self.job_client.put(job)

           # Load and process data
           records = self._load_from_s3(s3_bucket, s3_key)

           # Update total count
           job.total_records = len(records)
           self.job_client.put(job)

           # Process in batches
           self._process_records(batch_id, records)

           return batch_id

       def _load_from_s3(self, bucket: str, key: str) -> list[dict]:
           """Load JSON data from S3"""
           response = self.s3.get_object(Bucket=bucket, Key=key)
           data = json.loads(response['Body'].read())
           return data

       def _process_records(self, batch_id: str, records: list[dict]) -> None:
           """Process records in batches"""
           batch_size = 25  # DynamoDB batch write limit

           for i in range(0, len(records), batch_size):
               batch = records[i:i + batch_size]
               self._process_batch(batch_id, batch)

       def _process_batch(self, batch_id: str, records: list[dict]) -> None:
           """Process a single batch of records"""
           job = self.job_client.get(batch_id)

           for record_data in records:
               try:
                   # Process the record
                   processed = self._process_record(record_data)

                   # Save successful result
                   record = DataRecordTable(
                       record_id=str(uuid.uuid4()),
                       batch_id=batch_id,
                       source_data=record_data,
                       processed_data=processed,
                       status="completed",
                       created_at=datetime.now(UTC),
                       processed_at=datetime.now(UTC),
                   )
                   self.record_client.put(record)

                   job.processed_records += 1

               except Exception as e:
                   # Save failed record
                   record = DataRecordTable(
                       record_id=str(uuid.uuid4()),
                       batch_id=batch_id,
                       source_data=record_data,
                       status="failed",
                       error_message=str(e),
                       created_at=datetime.now(UTC),
                   )
                   self.record_client.put(record)

                   job.failed_records += 1

           # Update job status
           if job.processed_records + job.failed_records >= job.total_records:
               job.status = "completed"
               job.completed_at = datetime.now(UTC)

           self.job_client.put(job)

       def _process_record(self, data: dict) -> dict:
           """
           Process a single record
           Implement your business logic here
           """
           # Example: transform and enrich data
           result = {
               "original": data,
               "processed_at": datetime.now(UTC).isoformat(),
               "transformed": {
                   k.upper(): v for k, v in data.items()
               }
           }
           return result

       def get_batch_status(self, batch_id: str) -> dict:
           """Get status of a batch job"""
           job = self.job_client.get(batch_id)

           return {
               "batch_id": job.batch_id,
               "status": job.status,
               "total": job.total_records,
               "processed": job.processed_records,
               "failed": job.failed_records,
               "progress": (
                   job.processed_records + job.failed_records
               ) / job.total_records if job.total_records > 0 else 0,
           }

       def retry_failed_records(self, batch_id: str) -> None:
           """Retry failed records from a batch"""
           # Query records for this batch using the GSI
           # Then filter for failed status
           all_batch_records = list(self.record_client.query(
               index_name="batch_status_index",
               partition_key_value=batch_id
           ))

           # Filter for failed records
           failed_records = [r for r in all_batch_records if r.status == "failed"]

           # Retry each failed record
           for record in failed_records:
               try:
                   processed = self._process_record(record.source_data)
                   record.processed_data = processed
                   record.status = "completed"
                   record.processed_at = datetime.now(UTC)
                   record.error_message = None
               except Exception as e:
                   record.error_message = str(e)

               self.record_client.put(record)

Usage Example
-------------

.. code-block:: python

   processor = BatchProcessor()

   # Start processing a file from S3
   batch_id = processor.start_batch(
       s3_bucket="my-data-bucket",
       s3_key="data/import-2024-01-01.json"
   )

   print(f"Started batch: {batch_id}")

   # Check status
   status = processor.get_batch_status(batch_id)
   print(f"Progress: {status['progress']:.1%}")
   print(f"Processed: {status['processed']}/{status['total']}")
   print(f"Failed: {status['failed']}")

   # Retry failed records
   if status['failed'] > 0:
       processor.retry_failed_records(batch_id)

Key Concepts
------------

**Batch Processing**
   Process records in chunks to optimize throughput.

**Status Tracking**
   Track processing status at both job and record level.

**Error Handling**
   Capture errors without stopping the entire batch.

**Retry Logic**
   Ability to retry failed records separately.

**Progress Monitoring**
   Track progress through the batch job.

Variations
----------

**Add SQS Queue**

Process records asynchronously via SQS:

.. code-block:: python

   def queue_for_processing(self, batch_id: str, records: list[dict]):
       """Queue records for async processing"""
       sqs = boto3.client('sqs')
       queue_url = "your-queue-url"

       for record in records:
           sqs.send_message(
               QueueUrl=queue_url,
               MessageBody=json.dumps({
                   "batch_id": batch_id,
                   "record": record
               })
           )

**Add Lambda Trigger**

Automatically process files when uploaded to S3:

.. code-block:: python

   def s3_handler(event: dict, context: Any) -> None:
       """Lambda handler for S3 events"""
       for record in event['Records']:
           bucket = record['s3']['bucket']['name']
           key = record['s3']['object']['key']

           processor = BatchProcessor()
           processor.start_batch(bucket, key)
