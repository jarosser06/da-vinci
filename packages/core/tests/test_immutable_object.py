"""Tests for immutable object and schema validation functionality."""

import pytest

from da_vinci.core.immutable_object import (
    InvalidObjectSchemaError,
    MissingAttributeError,
    ObjectBody,
    ObjectBodySchema,
    RequiredCondition,
    RequiredConditionGroup,
    SchemaAttribute,
    SchemaAttributeType,
)
from da_vinci.core.orm.table_object import TableObjectAttributeType


@pytest.mark.unit
class TestSchemaAttributeType:
    """Test SchemaAttributeType enum."""

    def test_enum_values_exist(self):
        """Test that all expected schema attribute types are defined."""
        assert SchemaAttributeType.ANY
        assert SchemaAttributeType.STRING
        assert SchemaAttributeType.NUMBER
        assert SchemaAttributeType.BOOLEAN
        assert SchemaAttributeType.DATETIME
        assert SchemaAttributeType.OBJECT
        assert SchemaAttributeType.LIST
        assert SchemaAttributeType.STRING_LIST
        assert SchemaAttributeType.NUMBER_LIST
        assert SchemaAttributeType.OBJECT_LIST

    def test_to_str(self):
        """Test converting schema attribute type to string."""
        assert SchemaAttributeType.STRING.to_str() == "STRING"
        assert SchemaAttributeType.NUMBER.to_str() == "NUMBER"

    def test_table_object_attribute_type_conversion(self):
        """Test conversion to TableObjectAttributeType."""
        assert (
            SchemaAttributeType.STRING.table_object_attribute_type
            == TableObjectAttributeType.STRING
        )
        assert (
            SchemaAttributeType.NUMBER.table_object_attribute_type
            == TableObjectAttributeType.NUMBER
        )
        assert (
            SchemaAttributeType.BOOLEAN.table_object_attribute_type
            == TableObjectAttributeType.BOOLEAN
        )
        assert (
            SchemaAttributeType.DATETIME.table_object_attribute_type
            == TableObjectAttributeType.DATETIME
        )
        assert (
            SchemaAttributeType.OBJECT.table_object_attribute_type
            == TableObjectAttributeType.JSON_STRING
        )
        assert (
            SchemaAttributeType.STRING_LIST.table_object_attribute_type
            == TableObjectAttributeType.STRING_LIST
        )
        assert (
            SchemaAttributeType.NUMBER_LIST.table_object_attribute_type
            == TableObjectAttributeType.NUMBER_LIST
        )
        assert (
            SchemaAttributeType.OBJECT_LIST.table_object_attribute_type
            == TableObjectAttributeType.JSON_STRING_LIST
        )


@pytest.mark.unit
class TestRequiredCondition:
    """Test RequiredCondition and RequiredConditionGroup."""

    def test_required_condition_creation(self):
        """Test creating a required condition."""
        condition = RequiredCondition(
            param="execution_type",
            operator="equals",
            value="type1",
        )

        assert condition.param == "execution_type"
        assert condition.operator == "equals"
        assert condition.value == "type1"

    def test_required_condition_to_dict(self):
        """Test converting condition to dictionary."""
        condition = RequiredCondition(
            param="execution_type",
            operator="equals",
            value="type1",
        )

        condition_dict = condition.to_dict()
        assert condition_dict["param"] == "execution_type"
        assert condition_dict["operator"] == "equals"
        assert condition_dict["value"] == "type1"

    def test_required_condition_group_creation(self):
        """Test creating a required condition group."""
        group = RequiredConditionGroup(
            group_operator="or",
            conditions=[
                RequiredCondition(param="field1", operator="equals", value="val1"),
                RequiredCondition(param="field2", operator="equals", value="val2"),
            ],
        )

        assert group.group_operator == "or"
        assert len(group.conditions) == 2


@pytest.mark.unit
class TestSchemaAttribute:
    """Test SchemaAttribute functionality."""

    def test_basic_attribute_creation(self):
        """Test creating a basic schema attribute."""
        attr = SchemaAttribute(
            name="test_field",
            type_name=SchemaAttributeType.STRING,
            description="A test field",
        )

        assert attr.name == "test_field"
        assert attr.type_name == SchemaAttributeType.STRING
        assert attr.description == "A test field"
        assert attr.required is True

    def test_optional_attribute(self):
        """Test creating an optional attribute."""
        attr = SchemaAttribute(
            name="optional_field",
            type_name=SchemaAttributeType.STRING,
            required=False,
        )

        assert attr.required is False
        assert attr.is_required({}) is False

    def test_attribute_with_default_value(self):
        """Test attribute with default value."""
        attr = SchemaAttribute(
            name="field_with_default",
            type_name=SchemaAttributeType.STRING,
            default_value="default",
            required=False,
        )

        assert attr.default_value == "default"

    def test_attribute_with_enum(self):
        """Test attribute with enum values."""
        attr = SchemaAttribute(
            name="status",
            type_name=SchemaAttributeType.STRING,
            enum=["active", "inactive", "pending"],
        )

        assert attr.enum == ["active", "inactive", "pending"]

    def test_attribute_with_regex_pattern(self):
        """Test attribute with regex pattern."""
        attr = SchemaAttribute(
            name="email",
            type_name=SchemaAttributeType.STRING,
            regex_pattern=r"^[\w\.-]+@[\w\.-]+\.\w+$",
        )

        assert attr.regex_pattern is not None

    def test_is_required_simple(self):
        """Test simple required check."""
        required_attr = SchemaAttribute(
            name="required_field",
            type_name=SchemaAttributeType.STRING,
            required=True,
        )

        optional_attr = SchemaAttribute(
            name="optional_field",
            type_name=SchemaAttributeType.STRING,
            required=False,
        )

        assert required_attr.is_required({}) is True
        assert optional_attr.is_required({}) is False

    def test_is_required_with_condition(self):
        """Test required check with condition."""
        attr = SchemaAttribute(
            name="conditional_field",
            type_name=SchemaAttributeType.STRING,
            required_conditions=[
                {
                    "param": "execution_type",
                    "operator": "equals",
                    "value": "type1",
                }
            ],
        )

        # Should be required when condition is met
        assert attr.is_required({"execution_type": "type1"}) is True

        # Should not be required when condition is not met
        assert attr.is_required({"execution_type": "type2"}) is False

    def test_required_condition_operators(self):
        """Test different required condition operators."""
        test_cases = [
            ("equals", {"field": "value"}, "value", True),
            ("equals", {"field": "other"}, "value", False),
            ("not_equals", {"field": "other"}, "value", True),
            ("not_equals", {"field": "value"}, "value", False),
            ("gt", {"field": 10}, 5, True),
            ("gt", {"field": 3}, 5, False),
            ("gte", {"field": 5}, 5, True),
            ("gte", {"field": 3}, 5, False),
            ("lt", {"field": 3}, 5, True),
            ("lt", {"field": 10}, 5, False),
            ("lte", {"field": 5}, 5, True),
            ("lte", {"field": 10}, 5, False),
            ("in", {"field": "b"}, ["a", "b", "c"], True),
            ("in", {"field": "d"}, ["a", "b", "c"], False),
            ("not_in", {"field": "d"}, ["a", "b", "c"], True),
            ("not_in", {"field": "b"}, ["a", "b", "c"], False),
            ("contains", {"field": "hello world"}, "world", True),
            ("contains", {"field": "hello world"}, "foo", False),
            ("starts_with", {"field": "hello world"}, "hello", True),
            ("starts_with", {"field": "hello world"}, "world", False),
            ("ends_with", {"field": "hello world"}, "world", True),
            ("ends_with", {"field": "hello world"}, "hello", False),
            ("exists", {"field": "value"}, None, True),
            ("exists", {}, None, False),
            ("not_exists", {}, None, True),
            ("not_exists", {"field": "value"}, None, False),
        ]

        for operator, param_values, value, expected in test_cases:
            attr = SchemaAttribute(
                name="test_field",
                type_name=SchemaAttributeType.STRING,
                required_conditions=[
                    {
                        "param": "field",
                        "operator": operator,
                        "value": value,
                    }
                ],
            )

            assert attr.is_required(param_values) is expected, f"Failed for operator: {operator}"

    def test_required_condition_group_or(self):
        """Test required condition group with OR operator."""
        attr = SchemaAttribute(
            name="test_field",
            type_name=SchemaAttributeType.STRING,
            required_conditions=[
                {
                    "group_operator": "or",
                    "conditions": [
                        {"param": "field1", "operator": "equals", "value": "val1"},
                        {"param": "field2", "operator": "equals", "value": "val2"},
                    ],
                }
            ],
        )

        # Should be required if any condition is met
        assert attr.is_required({"field1": "val1", "field2": "other"}) is True
        assert attr.is_required({"field1": "other", "field2": "val2"}) is True
        assert attr.is_required({"field1": "val1", "field2": "val2"}) is True

        # Should not be required if no conditions are met
        assert attr.is_required({"field1": "other", "field2": "other"}) is False

    def test_required_condition_group_and(self):
        """Test required condition group with AND operator."""
        attr = SchemaAttribute(
            name="test_field",
            type_name=SchemaAttributeType.STRING,
            required_conditions=[
                {
                    "group_operator": "and",
                    "conditions": [
                        {"param": "field1", "operator": "equals", "value": "val1"},
                        {"param": "field2", "operator": "equals", "value": "val2"},
                    ],
                }
            ],
        )

        # Should be required only if all conditions are met
        assert attr.is_required({"field1": "val1", "field2": "val2"}) is True

        # Should not be required if any condition is not met
        assert attr.is_required({"field1": "val1", "field2": "other"}) is False
        assert attr.is_required({"field1": "other", "field2": "val2"}) is False


@pytest.mark.unit
class TestObjectBodySchema:
    """Test ObjectBodySchema functionality."""

    def test_simple_schema_creation(self):
        """Test creating a simple schema."""

        class SimpleSchema(ObjectBodySchema):
            attributes = [
                SchemaAttribute(
                    name="name",
                    type_name=SchemaAttributeType.STRING,
                ),
                SchemaAttribute(
                    name="age",
                    type_name=SchemaAttributeType.NUMBER,
                ),
            ]

        assert len(SimpleSchema.attributes) == 2
        assert SimpleSchema.attributes[0].name == "name"
        assert SimpleSchema.attributes[1].name == "age"

    def test_schema_to_dict(self):
        """Test converting schema to dictionary."""

        class TestSchema(ObjectBodySchema):
            name = "TestSchema"
            description = "A test schema"
            attributes = [
                SchemaAttribute(
                    name="field1",
                    type_name=SchemaAttributeType.STRING,
                ),
            ]

        schema_dict = TestSchema.to_dict()

        assert schema_dict["name"] == "TestSchema"
        assert schema_dict["description"] == "A test schema"
        assert len(schema_dict["attributes"]) == 1

    def test_validate_object_success(self):
        """Test successful object validation."""

        class PersonSchema(ObjectBodySchema):
            attributes = [
                SchemaAttribute(
                    name="name",
                    type_name=SchemaAttributeType.STRING,
                ),
                SchemaAttribute(
                    name="age",
                    type_name=SchemaAttributeType.NUMBER,
                ),
            ]

        result = PersonSchema.validate_object({"name": "John", "age": 30})

        assert result.valid is True
        assert len(result.missing_attributes) == 0
        assert len(result.mismatched_types) == 0

    def test_validate_object_missing_required(self):
        """Test validation with missing required attribute."""

        class PersonSchema(ObjectBodySchema):
            attributes = [
                SchemaAttribute(
                    name="name",
                    type_name=SchemaAttributeType.STRING,
                ),
                SchemaAttribute(
                    name="age",
                    type_name=SchemaAttributeType.NUMBER,
                ),
            ]

        result = PersonSchema.validate_object({"name": "John"})

        assert result.valid is False
        assert "age" in result.missing_attributes

    def test_validate_object_type_mismatch(self):
        """Test validation with type mismatch."""

        class PersonSchema(ObjectBodySchema):
            attributes = [
                SchemaAttribute(
                    name="name",
                    type_name=SchemaAttributeType.STRING,
                ),
                SchemaAttribute(
                    name="age",
                    type_name=SchemaAttributeType.NUMBER,
                ),
            ]

        result = PersonSchema.validate_object({"name": "John", "age": "thirty"})

        assert result.valid is False
        assert "age" in result.mismatched_types

    def test_validate_object_with_enum(self):
        """Test validation with enum constraint."""

        class StatusSchema(ObjectBodySchema):
            attributes = [
                SchemaAttribute(
                    name="status",
                    type_name=SchemaAttributeType.STRING,
                    enum=["active", "inactive"],
                ),
            ]

        # Valid enum value
        result = StatusSchema.validate_object({"status": "active"})
        assert result.valid is True

        # Invalid enum value
        result = StatusSchema.validate_object({"status": "pending"})
        assert result.valid is False
        assert any("enum" in msg for msg in result.mismatched_types)

    def test_validate_object_with_regex(self):
        """Test validation with regex pattern."""

        class EmailSchema(ObjectBodySchema):
            attributes = [
                SchemaAttribute(
                    name="email",
                    type_name=SchemaAttributeType.STRING,
                    regex_pattern=r"^[\w\.-]+@[\w\.-]+\.\w+$",
                ),
            ]

        # Valid email
        result = EmailSchema.validate_object({"email": "test@example.com"})
        assert result.valid is True

        # Invalid email
        result = EmailSchema.validate_object({"email": "invalid-email"})
        assert result.valid is False
        assert any("regex" in msg for msg in result.mismatched_types)

    def test_validate_object_with_nested_object(self):
        """Test validation with nested object."""

        class AddressSchema(ObjectBodySchema):
            attributes = [
                SchemaAttribute(
                    name="street",
                    type_name=SchemaAttributeType.STRING,
                ),
                SchemaAttribute(
                    name="city",
                    type_name=SchemaAttributeType.STRING,
                ),
            ]

        class PersonSchema(ObjectBodySchema):
            attributes = [
                SchemaAttribute(
                    name="name",
                    type_name=SchemaAttributeType.STRING,
                ),
                SchemaAttribute(
                    name="address",
                    type_name=SchemaAttributeType.OBJECT,
                    object_schema=AddressSchema,
                ),
            ]

        result = PersonSchema.validate_object(
            {
                "name": "John",
                "address": {
                    "street": "123 Main St",
                    "city": "Springfield",
                },
            }
        )

        assert result.valid is True


@pytest.mark.unit
class TestObjectBody:
    """Test ObjectBody functionality."""

    def test_create_simple_object(self):
        """Test creating a simple object body."""

        class SimpleSchema(ObjectBodySchema):
            attributes = [
                SchemaAttribute(
                    name="name",
                    type_name=SchemaAttributeType.STRING,
                ),
                SchemaAttribute(
                    name="age",
                    type_name=SchemaAttributeType.NUMBER,
                ),
            ]

        body = ObjectBody(
            body={"name": "John", "age": 30},
            schema=SimpleSchema,
        )

        assert body.get("name") == "John"
        assert body.get("age") == 30

    def test_object_immutability(self):
        """Test that ObjectBody is immutable."""
        body = ObjectBody(body={"name": "John"})

        with pytest.raises(TypeError, match="immutable"):
            body["name"] = "Jane"

    def test_get_with_default(self):
        """Test getting attribute with default value."""
        body = ObjectBody(body={"name": "John"})

        assert body.get("age", default_return=25) == 25
        assert body.get("name", default_return="Unknown") == "John"

    def test_get_strict_mode(self):
        """Test getting attribute in strict mode."""
        body = ObjectBody(body={"name": "John"})

        with pytest.raises(MissingAttributeError):
            body.get("age", strict=True)

    def test_dict_like_access(self):
        """Test dictionary-like access patterns."""

        class SimpleSchema(ObjectBodySchema):
            attributes = [
                SchemaAttribute(
                    name="name",
                    type_name=SchemaAttributeType.STRING,
                ),
                SchemaAttribute(
                    name="age",
                    type_name=SchemaAttributeType.NUMBER,
                ),
            ]

        body = ObjectBody(body={"name": "John", "age": 30}, schema=SimpleSchema)

        # Test __getitem__
        assert body["name"] == "John"

        # Test __contains__
        assert "name" in body
        assert "unknown" not in body

        # Test keys()
        assert "name" in body.keys()
        assert "age" in body.keys()

        # Test values()
        assert "John" in body.values()
        assert 30 in body.values()

        # Test items()
        items_dict = dict(body.items())
        assert items_dict["name"] == "John"
        assert items_dict["age"] == 30

    def test_iteration(self):
        """Test iterating over object body."""

        class SimpleSchema(ObjectBodySchema):
            attributes = [
                SchemaAttribute(
                    name="name",
                    type_name=SchemaAttributeType.STRING,
                ),
                SchemaAttribute(
                    name="age",
                    type_name=SchemaAttributeType.NUMBER,
                ),
            ]

        body = ObjectBody(body={"name": "John", "age": 30}, schema=SimpleSchema)

        keys = list(body)
        assert "name" in keys
        assert "age" in keys

    def test_to_dict(self):
        """Test converting object body to dictionary."""
        body = ObjectBody(body={"name": "John", "age": 30})

        result_dict = body.to_dict()
        assert result_dict["name"] == "John"
        assert result_dict["age"] == 30

    def test_nested_object(self):
        """Test object with nested objects."""

        class AddressSchema(ObjectBodySchema):
            attributes = [
                SchemaAttribute(
                    name="street",
                    type_name=SchemaAttributeType.STRING,
                ),
                SchemaAttribute(
                    name="city",
                    type_name=SchemaAttributeType.STRING,
                ),
            ]

        class PersonSchema(ObjectBodySchema):
            attributes = [
                SchemaAttribute(
                    name="name",
                    type_name=SchemaAttributeType.STRING,
                ),
                SchemaAttribute(
                    name="address",
                    type_name=SchemaAttributeType.OBJECT,
                    object_schema=AddressSchema,
                ),
            ]

        body = ObjectBody(
            body={
                "name": "John",
                "address": {
                    "street": "123 Main St",
                    "city": "Springfield",
                },
            },
            schema=PersonSchema,
        )

        assert body.get("name") == "John"
        address = body.get("address")
        assert isinstance(address, ObjectBody)
        assert address.get("street") == "123 Main St"
        assert address.get("city") == "Springfield"

    def test_object_list(self):
        """Test object with list of objects."""

        class ItemSchema(ObjectBodySchema):
            attributes = [
                SchemaAttribute(
                    name="name",
                    type_name=SchemaAttributeType.STRING,
                ),
                SchemaAttribute(
                    name="quantity",
                    type_name=SchemaAttributeType.NUMBER,
                ),
            ]

        class OrderSchema(ObjectBodySchema):
            attributes = [
                SchemaAttribute(
                    name="order_id",
                    type_name=SchemaAttributeType.STRING,
                ),
                SchemaAttribute(
                    name="items",
                    type_name=SchemaAttributeType.OBJECT_LIST,
                    object_schema=ItemSchema,
                ),
            ]

        body = ObjectBody(
            body={
                "order_id": "12345",
                "items": [
                    {"name": "Widget", "quantity": 2},
                    {"name": "Gadget", "quantity": 1},
                ],
            },
            schema=OrderSchema,
        )

        assert body.get("order_id") == "12345"
        items = body.get("items")
        assert len(items) == 2
        assert isinstance(items[0], ObjectBody)
        assert items[0].get("name") == "Widget"
        assert items[0].get("quantity") == 2

    def test_unknown_attributes(self):
        """Test handling of unknown attributes not in schema."""

        class SimpleSchema(ObjectBodySchema):
            attributes = [
                SchemaAttribute(
                    name="name",
                    type_name=SchemaAttributeType.STRING,
                ),
            ]

        body = ObjectBody(
            body={"name": "John", "extra_field": "extra_value"},
            schema=SimpleSchema,
        )

        # Should be able to access both schema and unknown attributes
        assert body.get("name") == "John"
        assert body.get("extra_field") == "extra_value"
        assert "extra_field" in body

    def test_schemaless_object(self):
        """Test creating object without schema."""
        body = ObjectBody(body={"name": "John", "age": 30, "active": True})

        assert body.get("name") == "John"
        assert body.get("age") == 30
        assert body.get("active") is True

    def test_invalid_schema_raises_error(self):
        """Test that invalid object raises error."""

        class StrictSchema(ObjectBodySchema):
            attributes = [
                SchemaAttribute(
                    name="required_field",
                    type_name=SchemaAttributeType.STRING,
                ),
            ]

        with pytest.raises(InvalidObjectSchemaError):
            ObjectBody(body={}, schema=StrictSchema)

    def test_map_to_new_schema(self):
        """Test mapping object to new schema."""

        class SourceSchema(ObjectBodySchema):
            attributes = [
                SchemaAttribute(
                    name="first_name",
                    type_name=SchemaAttributeType.STRING,
                ),
                SchemaAttribute(
                    name="last_name",
                    type_name=SchemaAttributeType.STRING,
                ),
            ]

        class TargetSchema(ObjectBodySchema):
            attributes = [
                SchemaAttribute(
                    name="full_name",
                    type_name=SchemaAttributeType.STRING,
                ),
                SchemaAttribute(
                    name="last_name",
                    type_name=SchemaAttributeType.STRING,
                ),
            ]

        source = ObjectBody(
            body={"first_name": "John", "last_name": "Doe"},
            schema=SourceSchema,
        )

        target = source.map_to(
            new_schema=TargetSchema,
            attribute_map={"first_name": "full_name"},
        )

        assert target.get("full_name") == "John"
        assert target.get("last_name") == "Doe"

    def test_new_with_additions(self):
        """Test creating new object with additions."""

        class SimpleSchema(ObjectBodySchema):
            attributes = [
                SchemaAttribute(
                    name="name",
                    type_name=SchemaAttributeType.STRING,
                ),
                SchemaAttribute(
                    name="age",
                    type_name=SchemaAttributeType.NUMBER,
                ),
            ]

        original = ObjectBody(body={"name": "John", "age": 30}, schema=SimpleSchema)

        new = original.new(additions={"city": "Springfield"})

        assert new.get("name") == "John"
        assert new.get("age") == 30
        assert new.get("city") == "Springfield"

        # Original should be unchanged
        assert original.get("city") is None

    def test_new_with_subtractions(self):
        """Test creating new object with subtractions."""

        class ExtendedSchema(ObjectBodySchema):
            attributes = [
                SchemaAttribute(
                    name="name",
                    type_name=SchemaAttributeType.STRING,
                ),
                SchemaAttribute(
                    name="age",
                    type_name=SchemaAttributeType.NUMBER,
                ),
                SchemaAttribute(
                    name="city",
                    type_name=SchemaAttributeType.STRING,
                ),
            ]

        original = ObjectBody(
            body={"name": "John", "age": 30, "city": "Springfield"}, schema=ExtendedSchema
        )

        new = original.new(subtractions=["city"])

        assert new.get("name") == "John"
        assert new.get("age") == 30
        assert new.get("city") is None

        # Original should be unchanged
        assert original.get("city") == "Springfield"


@pytest.mark.integration
class TestObjectBodyIntegration:
    """Integration tests for ObjectBody with complex scenarios."""

    def test_complex_nested_structure(self):
        """Test complex nested object structure."""

        class TagSchema(ObjectBodySchema):
            attributes = [
                SchemaAttribute(
                    name="key",
                    type_name=SchemaAttributeType.STRING,
                ),
                SchemaAttribute(
                    name="value",
                    type_name=SchemaAttributeType.STRING,
                ),
            ]

        class AddressSchema(ObjectBodySchema):
            attributes = [
                SchemaAttribute(
                    name="street",
                    type_name=SchemaAttributeType.STRING,
                ),
                SchemaAttribute(
                    name="city",
                    type_name=SchemaAttributeType.STRING,
                ),
                SchemaAttribute(
                    name="zip",
                    type_name=SchemaAttributeType.STRING,
                ),
            ]

        class PersonSchema(ObjectBodySchema):
            attributes = [
                SchemaAttribute(
                    name="name",
                    type_name=SchemaAttributeType.STRING,
                ),
                SchemaAttribute(
                    name="age",
                    type_name=SchemaAttributeType.NUMBER,
                ),
                SchemaAttribute(
                    name="active",
                    type_name=SchemaAttributeType.BOOLEAN,
                ),
                SchemaAttribute(
                    name="addresses",
                    type_name=SchemaAttributeType.OBJECT_LIST,
                    object_schema=AddressSchema,
                ),
                SchemaAttribute(
                    name="tags",
                    type_name=SchemaAttributeType.OBJECT_LIST,
                    object_schema=TagSchema,
                ),
                SchemaAttribute(
                    name="scores",
                    type_name=SchemaAttributeType.NUMBER_LIST,
                ),
            ]

        body = ObjectBody(
            body={
                "name": "John Doe",
                "age": 30,
                "active": True,
                "addresses": [
                    {"street": "123 Main St", "city": "Springfield", "zip": "12345"},
                    {"street": "456 Oak Ave", "city": "Shelbyville", "zip": "67890"},
                ],
                "tags": [
                    {"key": "department", "value": "engineering"},
                    {"key": "level", "value": "senior"},
                ],
                "scores": [85, 90, 88, 92],
            },
            schema=PersonSchema,
        )

        # Verify basic attributes
        assert body.get("name") == "John Doe"
        assert body.get("age") == 30
        assert body.get("active") is True

        # Verify nested object list
        addresses = body.get("addresses")
        assert len(addresses) == 2
        assert addresses[0].get("city") == "Springfield"
        assert addresses[1].get("city") == "Shelbyville"

        # Verify nested object list with tags
        tags = body.get("tags")
        assert len(tags) == 2
        assert tags[0].get("key") == "department"

        # Verify number list
        scores = body.get("scores")
        assert scores == [85, 90, 88, 92]

        # Verify to_dict preserves structure
        result_dict = body.to_dict()
        assert result_dict["addresses"][0]["city"] == "Springfield"
        assert result_dict["tags"][0]["key"] == "department"

    def test_conditional_required_fields(self):
        """Test schema with complex conditional requirements."""

        class ConfigSchema(ObjectBodySchema):
            attributes = [
                SchemaAttribute(
                    name="config_type",
                    type_name=SchemaAttributeType.STRING,
                    enum=["basic", "advanced"],
                ),
                SchemaAttribute(
                    name="basic_setting",
                    type_name=SchemaAttributeType.STRING,
                    required_conditions=[
                        {"param": "config_type", "operator": "equals", "value": "basic"}
                    ],
                ),
                SchemaAttribute(
                    name="advanced_setting",
                    type_name=SchemaAttributeType.STRING,
                    required_conditions=[
                        {"param": "config_type", "operator": "equals", "value": "advanced"}
                    ],
                ),
                SchemaAttribute(
                    name="optional_setting",
                    type_name=SchemaAttributeType.STRING,
                    required=False,
                ),
            ]

        # Basic config should require basic_setting
        body_basic = ObjectBody(
            body={
                "config_type": "basic",
                "basic_setting": "value1",
            },
            schema=ConfigSchema,
        )
        assert body_basic.get("config_type") == "basic"

        # Advanced config should require advanced_setting
        body_advanced = ObjectBody(
            body={
                "config_type": "advanced",
                "advanced_setting": "value2",
            },
            schema=ConfigSchema,
        )
        assert body_advanced.get("config_type") == "advanced"

        # Missing required conditional field should raise error
        with pytest.raises(InvalidObjectSchemaError):
            ObjectBody(
                body={"config_type": "basic"},
                schema=ConfigSchema,
            )
