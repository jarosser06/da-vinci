"""Read arbitrary ORM-backed DynamoDB tables in a deployed application.

Used to assert that a handler actually wrote the row it claimed to. Keys are
given using the *physical* DynamoDB attribute names (PascalCase), matching the
framework's ``default_dynamodb_key_name`` convention.
"""

from __future__ import annotations

from typing import Any

from lib import aws
from lib.context import Context


def get_item(
    ctx: Context,
    logical_table_name: str,
    key: dict[str, Any],
) -> dict[str, Any] | None:
    """Return the deserialized row for ``key``, or ``None`` if absent.

    Keyword Arguments:
        ctx: The deployed application owning the table.
        logical_table_name: The ORM ``table_name`` (e.g. ``"people"``).
        key: Primary key as ``{PascalColumn: value}`` (e.g. ``{"PersonId": "x"}``).
    """
    dynamo_key = {column: {"S": str(value)} for column, value in key.items()}

    return aws.get_item_by_key(ctx, logical_table_name, dynamo_key)
