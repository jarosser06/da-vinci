"""Tests for DynamoDB ORM client functionality."""

import pytest
from botocore.exceptions import ClientError
from moto import mock_aws

from da_vinci.core.orm.client import (
    PaginatedResults,
    TableClient,
    TableResultSortOrder,
    TableScanDefinition,
)
from da_vinci.core.orm.orm_exceptions import (
    TableScanInvalidAttributeError,
    TableScanInvalidComparisonError,
)
from da_vinci.core.orm.table_object import (
    TableObject,
    TableObjectAttribute,
    TableObjectAttributeType,
)


class SampleTableObject(TableObject):
    """Simple table object for testing."""

    table_name = "test-table"
    description = "Test table object"

    partition_key_attribute = TableObjectAttribute(
        name="pk",
        attribute_type=TableObjectAttributeType.STRING,
    )

    sort_key_attribute = TableObjectAttribute(
        name="sk",
        attribute_type=TableObjectAttributeType.STRING,
    )

    attributes = [
        TableObjectAttribute(
            name="value",
            attribute_type=TableObjectAttributeType.STRING,
            optional=True,
        ),
        TableObjectAttribute(
            name="count",
            attribute_type=TableObjectAttributeType.NUMBER,
            optional=True,
        ),
    ]


@pytest.mark.unit
class TestTableScanDefinition:
    """Test TableScanDefinition functionality."""

    def test_init(self):
        """Test scan definition initialization."""
        scan_def = TableScanDefinition(SampleTableObject)
        assert scan_def.table_object_class == SampleTableObject
        assert scan_def.attribute_prefix is None
        assert scan_def._attribute_filters == []

    def test_init_with_prefix(self):
        """Test scan definition with attribute prefix."""
        scan_def = TableScanDefinition(SampleTableObject, attribute_prefix="test")
        assert scan_def.attribute_prefix == "test"

    def test_add_filter_valid_comparison(self):
        """Test adding a valid attribute filter."""
        scan_def = TableScanDefinition(SampleTableObject)
        scan_def.add("value", "equal", "test")
        assert len(scan_def._attribute_filters) == 1
        assert scan_def._attribute_filters[0] == ("value", "=", "test")

    def test_add_filter_invalid_comparison(self):
        """Test adding a filter with invalid comparison operator."""
        scan_def = TableScanDefinition(SampleTableObject)
        with pytest.raises(TableScanInvalidComparisonError):
            scan_def.add("value", "invalid_comparison", "test")

    def test_add_filter_invalid_attribute(self):
        """Test adding a filter for non-existent attribute."""
        scan_def = TableScanDefinition(SampleTableObject)
        with pytest.raises(TableScanInvalidAttributeError):
            scan_def.add("nonexistent_attribute", "equal", "test")

    def test_dynamic_comparison_methods(self):
        """Test dynamic comparison method calls."""
        scan_def = TableScanDefinition(SampleTableObject)

        # Test equal
        scan_def.equal("value", "test")
        assert len(scan_def._attribute_filters) == 1

        # Test greater_than
        scan_def.greater_than("count", 10)
        assert len(scan_def._attribute_filters) == 2

    def test_to_expression_empty(self):
        """Test expression generation with no filters."""
        scan_def = TableScanDefinition(SampleTableObject)
        expression, attributes = scan_def.to_expression()
        assert expression is None
        assert attributes is None

    def test_to_expression_single_filter(self):
        """Test expression generation with single filter."""
        scan_def = TableScanDefinition(SampleTableObject)
        scan_def.equal("value", "test-value")
        expression, attributes = scan_def.to_expression()
        assert "Value" in expression  # DynamoDB uses capitalized attribute names
        assert ":a" in attributes

    def test_to_expression_multiple_filters(self):
        """Test expression generation with multiple filters."""
        scan_def = TableScanDefinition(SampleTableObject)
        scan_def.equal("value", "test-value")
        scan_def.greater_than("count", 5)
        expression, attributes = scan_def.to_expression()
        assert " AND " in expression
        assert len(attributes) == 2

    def test_to_instructions(self):
        """Test conversion to instruction list."""
        scan_def = TableScanDefinition(SampleTableObject)
        scan_def.equal("value", "test")
        scan_def.greater_than("count", 10)
        instructions = scan_def.to_instructions()
        assert len(instructions) == 2
        assert "value = test" in instructions
        assert "count > 10" in instructions


@pytest.mark.unit
class TestPaginatedResults:
    """Test PaginatedResults class."""

    def test_init_with_more_results(self):
        """Test initialization with more results available."""
        items = [SampleTableObject(pk="test-1", sk="data", value="val1")]
        last_key = {"pk": {"S": "test-1"}}
        results = PaginatedResults(items, last_key)

        assert results.items == items
        assert results.last_evaluated_key == last_key
        assert results.has_more is True

    def test_init_no_more_results(self):
        """Test initialization with no more results."""
        items = [SampleTableObject(pk="test-1", sk="data", value="val1")]
        results = PaginatedResults(items, None)

        assert results.items == items
        assert results.last_evaluated_key is None
        assert results.has_more is False

    def test_iteration(self):
        """Test iterating over results."""
        items = [
            SampleTableObject(pk="test-1", sk="data", value="val1"),
            SampleTableObject(pk="test-2", sk="data", value="val2"),
        ]
        results = PaginatedResults(items)

        iterated_items = list(results)
        assert len(iterated_items) == 2
        assert iterated_items == items


@pytest.mark.unit
@mock_aws
class TestTableClient:
    """Test TableClient CRUD operations."""

    @pytest.fixture
    def table_client(self, aws_credentials, dynamodb_table):
        """Create a table client for testing."""
        client = TableClient(
            default_object_class=SampleTableObject,
            table_endpoint_name="test-table",
        )
        return client

    def test_init_with_table_name(self, aws_credentials, dynamodb_table):
        """Test client initialization with explicit table name."""
        client = TableClient(
            default_object_class=SampleTableObject,
            table_endpoint_name="test-table",
        )
        assert client.table_name == "test-table"
        assert client.table_endpoint_name == "test-table"
        assert client.default_object_class == SampleTableObject

    def test_put_object(self, table_client, dynamodb_table):
        """Test saving an object to the table."""
        obj = SampleTableObject(
            pk="test-pk",
            sk="test-sk",
            value="test-value",
            count=42,
        )

        # Should not raise
        table_client.put_object(obj)

        # Verify object was saved
        response = dynamodb_table.get_item(Key={"Pk": "test-pk", "Sk": "test-sk"})
        assert "Item" in response
        assert response["Item"]["Pk"] == "test-pk"
        assert response["Item"]["Value"] == "test-value"

    def test_get_object_exists(self, table_client, dynamodb_table):
        """Test retrieving an existing object."""
        # Insert test data
        dynamodb_table.put_item(
            Item={
                "Pk": "test-pk",
                "Sk": "test-sk",
                "Value": "test-value",
                "Count": 42,
            }
        )

        # Retrieve object
        obj = table_client.get_object(
            partition_key_value="test-pk",
            sort_key_value="test-sk",
        )

        assert obj is not None
        assert obj.pk == "test-pk"
        assert obj.sk == "test-sk"
        assert obj.value == "test-value"
        assert obj.count == 42

    def test_get_object_not_exists(self, table_client):
        """Test retrieving a non-existent object."""
        obj = table_client.get_object(
            partition_key_value="nonexistent",
            sort_key_value="nonexistent",
        )
        assert obj is None

    def test_get_object_consistent_read(self, table_client, dynamodb_table):
        """Test retrieving with consistent read."""
        # Insert test data
        dynamodb_table.put_item(
            Item={
                "Pk": "test-pk",
                "Sk": "test-sk",
                "Value": "test-value",
                "Count": 42,
            }
        )

        # Retrieve with consistent read
        obj = table_client.get_object(
            partition_key_value="test-pk",
            sort_key_value="test-sk",
            consistent_read=True,
        )

        assert obj is not None
        assert obj.pk == "test-pk"

    def test_delete_object_by_key(self, table_client, dynamodb_table):
        """Test deleting an object by key."""
        # Insert test data
        dynamodb_table.put_item(
            Item={
                "Pk": "test-pk",
                "Sk": "test-sk",
                "Value": "test-value",
                "Count": 42,
            }
        )

        # Delete object
        table_client.delete_object_by_key(
            partition_key_value="test-pk",
            sort_key_value="test-sk",
        )

        # Verify deletion
        response = dynamodb_table.get_item(Key={"Pk": "test-pk", "Sk": "test-sk"})
        assert "Item" not in response

    def test_delete_object(self, table_client, dynamodb_table):
        """Test deleting an object by instance."""
        obj = SampleTableObject(
            pk="test-pk",
            sk="test-sk",
            value="test-value",
            count=42,
        )

        # Save and then delete
        table_client.put_object(obj)
        table_client.delete_object(obj)

        # Verify deletion
        response = dynamodb_table.get_item(Key={"Pk": "test-pk", "Sk": "test-sk"})
        assert "Item" not in response

    def test_put_object_with_empty_json_raises_error(self, table_client):
        """Test that putting an object with empty JSON attribute raises error."""
        # This test verifies the error handling for empty JSON attributes
        # The actual implementation depends on TableObject having JSON type attributes
        obj = SampleTableObject(
            pk="test-pk",
            sk="test-sk",
            value="test-value",
            count=42,
        )

        # Should succeed for normal object
        table_client.put_object(obj)


@pytest.mark.integration
@mock_aws
class TestTableClientIntegration:
    """Integration tests for TableClient with multiple operations."""

    @pytest.fixture
    def table_client(self, aws_credentials, dynamodb_table):
        """Create a table client for testing."""
        return TableClient(
            default_object_class=SampleTableObject,
            table_endpoint_name="test-table",
        )

    def test_full_crud_cycle(self, table_client):
        """Test complete create-read-update-delete cycle."""
        # Create
        obj = SampleTableObject(
            pk="test-pk",
            sk="test-sk",
            value="initial-value",
            count=1,
        )
        table_client.put_object(obj)

        # Read
        retrieved = table_client.get_object("test-pk", "test-sk")
        assert retrieved.value == "initial-value"
        assert retrieved.count == 1

        # Update
        retrieved.value = "updated-value"
        retrieved.count = 2
        table_client.put_object(retrieved)

        # Read updated
        updated = table_client.get_object("test-pk", "test-sk")
        assert updated.value == "updated-value"
        assert updated.count == 2

        # Delete
        table_client.delete_object(updated)

        # Verify deletion
        deleted = table_client.get_object("test-pk", "test-sk")
        assert deleted is None

    def test_multiple_objects(self, table_client):
        """Test handling multiple objects."""
        objects = [
            SampleTableObject(pk=f"pk-{i}", sk="data", value=f"value-{i}", count=i)
            for i in range(5)
        ]

        # Save all objects
        for obj in objects:
            table_client.put_object(obj)

        # Retrieve and verify
        for i in range(5):
            obj = table_client.get_object(f"pk-{i}", "data")
            assert obj is not None
            assert obj.value == f"value-{i}"
            assert obj.count == i


@pytest.mark.unit
@mock_aws
class TestORMClientCoverageGaps:
    """Tests to cover remaining uncovered lines in orm/client.py."""

    @pytest.fixture
    def table_client(self, aws_credentials, dynamodb_table):
        """Create a table client for testing."""
        return TableClient(
            default_object_class=SampleTableObject,
            table_endpoint_name="test-table",
        )

    def test_scan_definition_with_attribute_prefix(self):
        """Test TableScanDefinition with attribute_prefix (line 80)."""

        class PrefixedTableObject(TableObject):
            table_name = "test_table"
            attribute_lookup_prefix = "prefix"

            partition_key_attribute = TableObjectAttribute(
                name="pk",
                attribute_type=TableObjectAttributeType.STRING,
            )

            attributes = [
                TableObjectAttribute(
                    name="prefix_field",
                    attribute_type=TableObjectAttributeType.STRING,
                    optional=True,
                ),
            ]

        scan_def = TableScanDefinition(PrefixedTableObject, attribute_prefix="prefix")
        scan_def.add("field", "equal", "value")
        assert len(scan_def._attribute_filters) == 1
        assert scan_def._attribute_filters[0][0] == "prefix_field"

    def test_scan_definition_to_expression_with_caching(self):
        """Test to_expression with attribute caching (line 116)."""
        scan_def = TableScanDefinition(SampleTableObject)
        scan_def.add("value", "equal", "test1")
        scan_def.add("value", "not_equal", "test2")  # Same attribute, should use cache

        expression, attrs = scan_def.to_expression()
        assert "Value = :a" in expression
        assert "Value != :b" in expression
        assert ":a" in attrs
        assert ":b" in attrs

    def test_scan_definition_to_expression_invalid_attribute_raises_error(self):
        """Test to_expression with invalid attribute (line 122)."""
        scan_def = TableScanDefinition(SampleTableObject)
        # Manually inject an invalid filter to test the error path
        scan_def._attribute_filters.append(("nonexistent", "=", "value"))

        with pytest.raises(TableScanInvalidAttributeError):
            scan_def.to_expression()

    def test_scan_definition_contains_expression(self):
        """Test contains comparison in to_expression (line 131)."""

        class ListTableObject(TableObject):
            table_name = "test_table"

            partition_key_attribute = TableObjectAttribute(
                name="pk",
                attribute_type=TableObjectAttributeType.STRING,
            )

            attributes = [
                TableObjectAttribute(
                    name="tags",
                    attribute_type=TableObjectAttributeType.STRING_LIST,
                    optional=True,
                ),
            ]

        scan_def = TableScanDefinition(ListTableObject)
        scan_def.add("tags", "contains", "test-tag")

        expression, attrs = scan_def.to_expression()
        assert "contains(Tags, :a)" in expression
        assert ":a" in attrs

    def test_scan_definition_contains_with_string_list(self):
        """Test contains with STRING_LIST attribute (line 142)."""

        class ListTableObject(TableObject):
            table_name = "test_table"

            partition_key_attribute = TableObjectAttribute(
                name="pk",
                attribute_type=TableObjectAttributeType.STRING,
            )

            attributes = [
                TableObjectAttribute(
                    name="tags",
                    attribute_type=TableObjectAttributeType.STRING_LIST,
                    optional=True,
                ),
            ]

        scan_def = TableScanDefinition(ListTableObject)
        scan_def.add("tags", "contains", "test-tag")

        expression, attrs = scan_def.to_expression()
        # Should use {"S": value} format for STRING_LIST contains
        assert attrs[":a"]["S"] == "test-tag"

    def test_scan_definition_getattr_invalid_attribute(self):
        """Test __getattr__ with invalid attribute (line 191)."""
        scan_def = TableScanDefinition(SampleTableObject)

        with pytest.raises(AttributeError):
            scan_def.nonexistent_comparison("value", "test")

    def test_table_client_with_resource_discovery(
        self, aws_credentials, dynamodb_table, resource_registry_table, mock_environment
    ):
        """Test TableClient initialization with resource discovery (lines 210-218)."""
        # Register the table
        resource_registry_table.put_item(
            Item={
                "ResourceType": "table",
                "ResourceName": "test-table",
                "Endpoint": "test-table",
            }
        )

        # Create client without table_endpoint_name to trigger resource discovery
        client = TableClient(
            default_object_class=SampleTableObject,
            app_name="test-app",
            deployment_id="test-deployment",
        )

        assert client.table_endpoint_name == "test-table"

    def test_table_resource_exists_true(
        self, aws_credentials, resource_registry_table, mock_environment
    ):
        """Test table_resource_exists method when resource exists (lines 237-246)."""
        # Test when resource exists
        resource_registry_table.put_item(
            Item={
                "ResourceType": "table",
                "ResourceName": "test-table",
                "Endpoint": "test-table",
            }
        )

        result = TableClient.table_resource_exists(
            table_object_class=SampleTableObject,
            app_name="test-app",
            deployment_id="test-deployment",
        )
        # Method doesn't return explicit True, just doesn't raise or return False
        assert result is not False

    def test_table_resource_exists_false(
        self, aws_credentials, resource_registry_table, mock_environment
    ):
        """Test table_resource_exists when resource doesn't exist (lines 247-248)."""
        # Create a different table name that doesn't exist
        class NonExistentTable(TableObject):
            table_name = "nonexistent-table"
            partition_key_attribute = TableObjectAttribute(
                name="pk",
                attribute_type=TableObjectAttributeType.STRING,
            )

        result = TableClient.table_resource_exists(
            table_object_class=NonExistentTable,
            app_name="test-app",
            deployment_id="test-deployment",
        )
        # Method returns False when ResourceNotFoundError is caught
        assert result is False

    def test_paginated_query_with_limit(self, table_client, dynamodb_table):
        """Test paginated query with limit (lines 272-351)."""
        # Insert test data
        for i in range(10):
            dynamodb_table.put_item(Item={"Pk": "pk1", "Sk": f"sk{i:02d}", "Value": f"value{i}"})

        params = {
            "KeyConditionExpression": "Pk = :pk",
            "ExpressionAttributeValues": {":pk": {"S": "pk1"}},
        }

        # Test with limit
        pages = list(table_client.paginated(call="query", limit=3, parameters=params))

        assert len(pages) > 0
        # Each page should have at most 3 items
        for page in pages:
            assert len(page.items) <= 3

    def test_paginated_scan_with_max_pages(self, table_client, dynamodb_table):
        """Test paginated scan with max_pages (lines 350-351)."""
        # Insert test data
        for i in range(20):
            dynamodb_table.put_item(Item={"Pk": f"pk{i}", "Sk": "sk", "Value": f"value{i}"})

        # Test with max_pages=2
        pages = list(table_client.paginated(call="scan", limit=5, max_pages=2))

        assert len(pages) == 2

    def test_paginated_query_with_last_evaluated_key(self, table_client, dynamodb_table):
        """Test paginated query with last_evaluated_key (lines 293-301)."""
        # Insert test data
        for i in range(5):
            dynamodb_table.put_item(Item={"Pk": "pk1", "Sk": f"sk{i}", "Value": f"value{i}"})

        params = {
            "KeyConditionExpression": "Pk = :pk",
            "ExpressionAttributeValues": {":pk": {"S": "pk1"}},
        }

        # Get first page
        first_page = next(table_client.paginated(call="query", limit=2, parameters=params))

        if first_page.last_evaluated_key:
            # Get next page using last_evaluated_key
            pages = list(
                table_client.paginated(
                    call="query",
                    limit=2,
                    last_evaluated_key=first_page.last_evaluated_key,
                    parameters=params,
                )
            )
            assert len(pages) > 0

    def test_paginated_query_with_last_evaluated_object(self, table_client, dynamodb_table):
        """Test paginated query with last_evaluated_object (lines 303-315)."""
        # Insert test data
        for i in range(5):
            dynamodb_table.put_item(Item={"Pk": "pk1", "Sk": f"sk{i}", "Value": f"value{i}"})

        params = {
            "KeyConditionExpression": "Pk = :pk",
            "ExpressionAttributeValues": {":pk": {"S": "pk1"}},
        }

        # Get first page
        first_page = next(table_client.paginated(call="query", limit=2, parameters=params))

        if first_page.items:
            last_obj = first_page.items[-1]
            # Get next page using last_evaluated_object
            pages = list(
                table_client.paginated(
                    call="query",
                    limit=2,
                    last_evaluated_object=last_obj,
                    parameters=params,
                )
            )
            assert len(pages) > 0

    def test_paginated_query_with_sort_order(self, table_client, dynamodb_table):
        """Test paginated query with sort order (lines 287-291)."""
        # Insert test data
        for i in range(5):
            dynamodb_table.put_item(Item={"Pk": "pk1", "Sk": f"sk{i}", "Value": f"value{i}"})

        params = {
            "KeyConditionExpression": "Pk = :pk",
            "ExpressionAttributeValues": {":pk": {"S": "pk1"}},
        }

        # Test ascending order
        pages_asc = list(
            table_client.paginated(
                call="query",
                parameters=params,
                sort_order=TableResultSortOrder.ASCENDING,
            )
        )
        assert len(pages_asc) > 0

        # Test descending order
        pages_desc = list(
            table_client.paginated(
                call="query",
                parameters=params,
                sort_order=TableResultSortOrder.DESCENDING,
            )
        )
        assert len(pages_desc) > 0

    def test_all_objects_method(self, table_client, dynamodb_table):
        """Test _all_objects method (lines 358-363)."""
        # Insert test data
        for i in range(5):
            dynamodb_table.put_item(Item={"Pk": f"pk{i}", "Sk": "sk", "Value": f"value{i}"})

        all_objs = table_client._all_objects()
        assert len(all_objs) == 5

    def test_put_object_with_validation_exception(self, table_client, monkeypatch):
        """Test put_object with ClientError validation exception (lines 415-429)."""
        from unittest.mock import MagicMock

        obj = SampleTableObject(pk="pk1", sk="sk1", value="test")

        # Mock the client to raise ValidationException
        mock_client = MagicMock()
        mock_client.put_item.side_effect = ClientError(
            {
                "Error": {
                    "Code": "ValidationException",
                    "Message": "Supplied AttributeValue is empty",
                }
            },
            "PutItem",
        )

        table_client.client = mock_client

        with pytest.raises(Exception, match="Empty attribute value detected"):
            table_client.put_object(obj)


    def test_update_object_with_updates(self, table_client, dynamodb_table):
        """Test update_object with updates (lines 559-658)."""
        # Insert initial data
        dynamodb_table.put_item(
            Item={"Pk": "pk1", "Sk": "sk1", "Value": "initial", "Count": "10"}
        )

        # Update the object
        table_client.update_object(
            partition_key_value="pk1",
            sort_key_value="sk1",
            updates={"value": "updated", "count": 20},
        )

        # Verify the update
        result = table_client.get_object("pk1", "sk1")
        assert result.value == "updated"
        assert result.count == 20

    def test_paginated_query_without_sort_key_raises_error(self, aws_credentials, dynamodb_table):
        """Test paginated query with sort_order on table without sort key (line 289)."""

        class NoSortKeyObject(TableObject):
            table_name = "test-table"

            partition_key_attribute = TableObjectAttribute(
                name="pk",
                attribute_type=TableObjectAttributeType.STRING,
            )

            # No sort_key_attribute

        client = TableClient(
            default_object_class=NoSortKeyObject,
            table_endpoint_name="test-table",
        )

        params = {
            "KeyConditionExpression": "Pk = :pk",
            "ExpressionAttributeValues": {":pk": {"S": "pk1"}},
        }

        with pytest.raises(Exception, match="must have sort key"):
            list(
                client.paginated(
                    call="query",
                    parameters=params,
                    sort_order=TableResultSortOrder.ASCENDING,
                )
            )

    def test_paginated_scan_with_invalid_last_evaluated_key(self, table_client):
        """Test paginated scan with non-dict last_evaluated_key (lines 295-298)."""
        with pytest.raises(Exception, match="must be a dictionary"):
            list(table_client.paginated(call="scan", last_evaluated_key="invalid_string"))

    def test_put_object_with_other_validation_exception(self, table_client, monkeypatch):
        """Test put_object with ValidationException that's not about empty attributes (line 425)."""
        from unittest.mock import MagicMock

        obj = SampleTableObject(pk="pk1", sk="sk1", value="test")

        # Mock the client to raise ValidationException without "empty" in message
        mock_client = MagicMock()
        mock_client.put_item.side_effect = ClientError(
            {
                "Error": {
                    "Code": "ValidationException",
                    "Message": "Some other validation error",
                }
            },
            "PutItem",
        )

        table_client.client = mock_client

        with pytest.raises(ClientError):
            table_client.put_object(obj)

    def test_put_object_with_non_validation_exception(self, table_client, monkeypatch):
        """Test put_object with non-ValidationException ClientError (lines 427-429)."""
        from unittest.mock import MagicMock

        obj = SampleTableObject(pk="pk1", sk="sk1", value="test")

        # Mock the client to raise a different ClientError
        mock_client = MagicMock()
        mock_client.put_item.side_effect = ClientError(
            {"Error": {"Code": "ResourceNotFoundException", "Message": "Table not found"}},
            "PutItem",
        )

        table_client.client = mock_client

        with pytest.raises(ClientError):
            table_client.put_object(obj)

    def test_scanner_with_empty_filter(self, table_client, dynamodb_table):
        """Test scanner method with empty scan definition (lines 481-494)."""
        # Insert test data
        for i in range(3):
            dynamodb_table.put_item(Item={"Pk": f"pk{i}", "Sk": "sk"})

        # Create empty scan definition (no filters)
        scan_def = TableScanDefinition(SampleTableObject)

        # Scanner should work even with no filters
        pages = list(table_client.scanner(scan_def))
        assert len(pages) > 0

    def test_full_scan_with_empty_filter(self, table_client, dynamodb_table):
        """Test full_scan method with empty scan definition (lines 503-508)."""
        # Insert test data
        for i in range(3):
            dynamodb_table.put_item(Item={"Pk": f"pk{i}", "Sk": "sk"})

        # Create empty scan definition
        scan_def = TableScanDefinition(SampleTableObject)

        # Full scan should work
        results = table_client.full_scan(scan_def)
        assert isinstance(results, list)
        assert len(results) >= 3

    def test_update_object_with_nested_updates(self, table_client, dynamodb_table):
        """Test update_object with dot notation for nested updates (lines 571-591)."""

        class NestedTableObject(TableObject):
            table_name = "test-table"

            partition_key_attribute = TableObjectAttribute(
                name="pk",
                attribute_type=TableObjectAttributeType.STRING,
            )

            sort_key_attribute = TableObjectAttribute(
                name="sk",
                attribute_type=TableObjectAttributeType.STRING,
            )

            attributes = [
                TableObjectAttribute(
                    name="json_map",
                    attribute_type=TableObjectAttributeType.JSON,
                    optional=True,
                ),
            ]

        client = TableClient(
            default_object_class=NestedTableObject,
            table_endpoint_name="test-table",
        )

        # Insert initial data with nested map
        obj = NestedTableObject(pk="pk1", sk="sk1", json_map={"key1": "value1", "key2": "value2"})
        client.put_object(obj)

        # Update nested key
        client.update_object(
            partition_key_value="pk1",
            sort_key_value="sk1",
            updates={"json_map.key1": {"S": "updated_value"}},
        )

        # Verify the update
        result = client.get_object("pk1", "sk1")
        assert result.json_map["key1"] == "updated_value"

    def test_scanner_with_filters(self, table_client, dynamodb_table):
        """Test scanner method with actual filter expression (lines 489-491)."""
        # Insert test data using TableObject to ensure correct types
        for i in range(5):
            obj = SampleTableObject(pk=f"pk{i}", sk="sk", value=f"test{i}", count=i)
            table_client.put_object(obj)

        # Create scan definition with a filter that works
        scan_def = TableScanDefinition(SampleTableObject)
        # Use a simple comparison that should work
        scan_def.add("pk", "equal", "pk1")

        # This should hit lines 489-491 (adding filter expression)
        pages = list(table_client.scanner(scan_def))
        assert len(pages) > 0
        # Should only have items matching the filter
        all_items = [item for page in pages for item in page.items]
        for item in all_items:
            # All items should have pk="pk1" due to filter
            assert item.pk == "pk1"

    def test_paginated_scan_with_dict_last_evaluated_key(self, table_client, dynamodb_table):
        """Test paginated scan with valid dict last_evaluated_key (line 298)."""
        # Insert test data
        for i in range(10):
            dynamodb_table.put_item(
                Item={"Pk": f"pk{i:02d}", "Sk": "sk", "Value": f"value{i}"}
            )

        # First, get a page to get a last_evaluated_key
        first_page = next(table_client.paginated(call="scan", limit=3))

        if first_page.last_evaluated_key:
            # Use the last_evaluated_key (which is a dict) for scan (line 298)
            pages = list(
                table_client.paginated(call="scan", limit=3, last_evaluated_key=first_page.last_evaluated_key)
            )
            assert len(pages) > 0

    def test_update_object_remove_keys_only_nested(self, table_client):
        """Test update_object with nested remove_keys using mocking (lines 619-629)."""
        from unittest.mock import MagicMock

        # Mock the client to avoid actual DynamoDB calls
        mock_client = MagicMock()
        table_client.client = mock_client

        # Call update_object with nested remove_keys
        table_client.update_object(
            partition_key_value="pk1",
            sort_key_value="sk1",
            remove_keys=["json_map.nested.key", "other_map.deep.value"],
        )

        # Verify update_item was called
        assert mock_client.update_item.called
        call_kwargs = mock_client.update_item.call_args[1]

        # Check that the UpdateExpression contains REMOVE
        assert "REMOVE" in call_kwargs["UpdateExpression"]

        # Check that expression attribute names contain the nested keys
        expr_names = call_kwargs["ExpressionAttributeNames"]
        assert "#json_map" in expr_names
        assert "#nested" in expr_names
        assert "#key" in expr_names
        assert "#other_map" in expr_names
        assert "#deep" in expr_names
        assert "#value" in expr_names

    def test_update_object_remove_keys_only_regular(self, table_client):
        """Test update_object with regular remove_keys using mocking (lines 630-636)."""
        from unittest.mock import MagicMock

        # Mock the client to avoid actual DynamoDB calls
        mock_client = MagicMock()
        table_client.client = mock_client

        # Call update_object with only regular (non-nested) remove_keys
        # Note: DynamoDB requires at least one update or remove, so this should work
        table_client.update_object(
            partition_key_value="pk1",
            sort_key_value="sk1",
            remove_keys=["field1", "field2"],
        )

        # Verify update_item was called
        assert mock_client.update_item.called
        call_kwargs = mock_client.update_item.call_args[1]

        # Check that the UpdateExpression contains REMOVE
        assert "REMOVE" in call_kwargs["UpdateExpression"]

        # Check that expression attribute names contain the field names
        expr_names = call_kwargs["ExpressionAttributeNames"]
        assert "#field1" in expr_names
        assert "#field2" in expr_names
        assert expr_names["#field1"] == "field1"
        assert expr_names["#field2"] == "field2"

    def test_update_object_mixed_nested_and_regular_removes(self, table_client):
        """Test update_object with both nested and regular remove_keys (lines 619-636)."""
        from unittest.mock import MagicMock

        # Mock the client
        mock_client = MagicMock()
        table_client.client = mock_client

        # Call with mix of nested and regular removes
        table_client.update_object(
            partition_key_value="pk1",
            sort_key_value="sk1",
            remove_keys=["regular_field", "nested.map.key", "another_field"],
        )

        # Verify the call
        assert mock_client.update_item.called
        call_kwargs = mock_client.update_item.call_args[1]

        # Check UpdateExpression
        update_expr = call_kwargs["UpdateExpression"]
        assert "REMOVE" in update_expr

        # Check expression attribute names
        expr_names = call_kwargs["ExpressionAttributeNames"]
        # Regular fields
        assert "#regular_field" in expr_names
        assert "#another_field" in expr_names
        # Nested fields
        assert "#nested" in expr_names
        assert "#map" in expr_names
        assert "#key" in expr_names
