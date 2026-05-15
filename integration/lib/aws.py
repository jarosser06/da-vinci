"""Low-level AWS helpers shared by the read-side validation modules.

Reads in this suite go directly to DynamoDB (rather than through the ORM)
because the tests assert against the *physical* item exactly as the framework
stored it — PascalCase column names and native value types. Centralising the
client, the deserializer, and the name convention here keeps every reader
consistent.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Any

import boto3
from boto3.dynamodb.types import TypeDeserializer
from lib.context import Context

_DESERIALIZER = TypeDeserializer()


@lru_cache(maxsize=None)
def dynamodb_client(region: str):
    """Return a cached low-level DynamoDB client for ``region``."""
    return boto3.client("dynamodb", region_name=region)


def physical_table_name(ctx: Context, logical_table_name: str) -> str:
    """Map a logical table name to its deployed physical name.

    Mirrors ``da_vinci.core.base.standard_aws_resource_name``:
    ``{app_name}-{deployment_id}-{logical_table_name}``.
    """
    return f"{ctx.app_name}-{ctx.deployment_id}-{logical_table_name}"


def deserialize_item(item: dict[str, Any]) -> dict[str, Any]:
    """Convert a raw DynamoDB item into native Python values."""
    return {key: _DESERIALIZER.deserialize(value) for key, value in item.items()}


def query_partition(
    ctx: Context,
    logical_table_name: str,
    partition_key_name: str,
    partition_key_value: str,
) -> list[dict[str, Any]]:
    """Return every deserialized item under one partition key value."""
    client = dynamodb_client(ctx.region)

    table = physical_table_name(ctx, logical_table_name)

    response = client.query(
        TableName=table,
        KeyConditionExpression="#pk = :pk",
        ExpressionAttributeNames={"#pk": partition_key_name},
        ExpressionAttributeValues={":pk": {"S": partition_key_value}},
    )

    return [deserialize_item(item) for item in response.get("Items", [])]


def get_item_by_key(
    ctx: Context,
    logical_table_name: str,
    key: dict[str, dict],
) -> dict[str, Any] | None:
    """Return the deserialized item for a fully-specified DynamoDB key."""
    client = dynamodb_client(ctx.region)

    table = physical_table_name(ctx, logical_table_name)

    response = client.get_item(TableName=table, Key=key)

    item = response.get("Item")

    if item is None:
        return None

    return deserialize_item(item)
