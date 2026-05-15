"""Tests for Da Vinci core exceptions."""

import pytest

from da_vinci.core.exceptions import (
    DuplicateRouteDefinitionError,
    GlobalSettingNotFoundError,
    GlobalSettingsNotEnabledError,
    MissingRequiredRuntimeVariableError,
    ResourceNotFoundError,
)
from da_vinci.core.orm.orm_exceptions import (
    AugmentedRetrievalInvalidQueryError,
    MissingTableObjectAttributeError,
    TableScanInvalidAttributeError,
    TableScanInvalidComparisonError,
    TableScanMissingAttributeError,
    TableScanQueryError,
)


@pytest.mark.unit
class TestCoreExceptions:
    """Test core Da Vinci exceptions."""

    def test_duplicate_route_definition_error_message_and_type(self):
        """DuplicateRouteDefinitionError renders the exact route message."""
        with pytest.raises(DuplicateRouteDefinitionError) as exc_info:
            raise DuplicateRouteDefinitionError("test_route")

        error = exc_info.value
        assert isinstance(error, Exception)
        assert str(error) == "Route definition for test_route already exists"

    def test_global_settings_not_enabled_error_message_and_type(self):
        """GlobalSettingsNotEnabledError renders the exact static message."""
        with pytest.raises(GlobalSettingsNotEnabledError) as exc_info:
            raise GlobalSettingsNotEnabledError()

        error = exc_info.value
        assert isinstance(error, Exception)
        assert str(error) == ("Attempting to access global settings when they are not enabled")

    def test_global_setting_not_found_error_message_and_type(self):
        """GlobalSettingNotFoundError renders key and namespace exactly."""
        with pytest.raises(GlobalSettingNotFoundError) as exc_info:
            raise GlobalSettingNotFoundError("my_key", "my_namespace")

        error = exc_info.value
        assert isinstance(error, Exception)
        assert str(error) == "Setting my_key in namespace my_namespace not found"

    def test_missing_required_runtime_variable_error_message_and_type(self):
        """MissingRequiredRuntimeVariableError subclasses RuntimeError."""
        with pytest.raises(MissingRequiredRuntimeVariableError) as exc_info:
            raise MissingRequiredRuntimeVariableError("MY_VAR")

        error = exc_info.value
        assert isinstance(error, RuntimeError)
        assert str(error) == "Required runtime variable MY_VAR not found"

    def test_resource_not_found_error_message_and_type(self):
        """ResourceNotFoundError renders resource name and type exactly."""
        with pytest.raises(ResourceNotFoundError) as exc_info:
            raise ResourceNotFoundError("my-resource", "table")

        error = exc_info.value
        assert isinstance(error, Exception)
        assert str(error) == "Resource my-resource of type table not found"


@pytest.mark.unit
class TestORMExceptions:
    """Test ORM-specific exceptions."""

    def test_augmented_retrieval_invalid_query_error_message_and_type(self):
        """AugmentedRetrievalInvalidQueryError subclasses ValueError."""
        with pytest.raises(AugmentedRetrievalInvalidQueryError) as exc_info:
            raise AugmentedRetrievalInvalidQueryError("SELECT *", "Invalid syntax")

        error = exc_info.value
        assert isinstance(error, ValueError)
        assert str(error) == "SELECT * is not a valid query: Invalid syntax"

    def test_missing_table_object_attribute_error_message_and_type(self):
        """MissingTableObjectAttributeError subclasses ValueError."""
        with pytest.raises(MissingTableObjectAttributeError) as exc_info:
            raise MissingTableObjectAttributeError("my_field")

        error = exc_info.value
        assert isinstance(error, ValueError)
        assert str(error) == "Required argument my_field, was not provided"

    def test_table_scan_query_error_message_and_type(self):
        """TableScanQueryError renders attribute name and type exactly."""
        with pytest.raises(TableScanQueryError) as exc_info:
            raise TableScanQueryError("field_name", "STRING")

        error = exc_info.value
        assert isinstance(error, ValueError)
        assert str(error) == "field_name is not a valid STRING"

    def test_table_scan_invalid_comparison_error_message_and_hierarchy(self):
        """TableScanInvalidComparisonError formats via its TableScanQueryError base."""
        with pytest.raises(TableScanInvalidComparisonError) as exc_info:
            raise TableScanInvalidComparisonError("invalid_op")

        error = exc_info.value
        assert isinstance(error, TableScanQueryError)
        assert isinstance(error, ValueError)
        assert str(error) == "invalid_op is not a valid comparison operator"

    def test_table_scan_invalid_attribute_error_message_and_hierarchy(self):
        """TableScanInvalidAttributeError formats via its TableScanQueryError base."""
        with pytest.raises(TableScanInvalidAttributeError) as exc_info:
            raise TableScanInvalidAttributeError("bad_field")

        error = exc_info.value
        assert isinstance(error, TableScanQueryError)
        assert isinstance(error, ValueError)
        assert str(error) == "bad_field is not a valid table object attribute"

    def test_table_scan_missing_attribute_error_message_and_type(self):
        """TableScanMissingAttributeError subclasses ValueError."""
        with pytest.raises(TableScanMissingAttributeError) as exc_info:
            raise TableScanMissingAttributeError("required_field")

        error = exc_info.value
        assert isinstance(error, ValueError)
        assert str(error) == "required_field was not provided"
