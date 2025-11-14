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

    def test_duplicate_route_definition_error(self):
        """Test DuplicateRouteDefinitionError exception."""
        error = DuplicateRouteDefinitionError("test_route")
        assert "test_route" in str(error)
        assert "already exists" in str(error)

    def test_global_settings_not_enabled_error(self):
        """Test GlobalSettingsNotEnabledError exception."""
        error = GlobalSettingsNotEnabledError()
        assert "not enabled" in str(error)

    def test_global_setting_not_found_error(self):
        """Test GlobalSettingNotFoundError exception."""
        error = GlobalSettingNotFoundError("my_key", "my_namespace")
        assert "my_key" in str(error)
        assert "my_namespace" in str(error)
        assert "not found" in str(error)

    def test_missing_required_runtime_variable_error(self):
        """Test MissingRequiredRuntimeVariableError exception."""
        error = MissingRequiredRuntimeVariableError("MY_VAR")
        assert "MY_VAR" in str(error)
        assert "not found" in str(error)

    def test_resource_not_found_error(self):
        """Test ResourceNotFoundError exception."""
        error = ResourceNotFoundError("my-resource", "table")
        assert "my-resource" in str(error)
        assert "table" in str(error)
        assert "not found" in str(error)


@pytest.mark.unit
class TestORMExceptions:
    """Test ORM-specific exceptions."""

    def test_augmented_retrieval_invalid_query_exception(self):
        """Test AugmentedRetrievalInvalidQueryException exception."""
        error = AugmentedRetrievalInvalidQueryError("SELECT *", "Invalid syntax")
        assert "SELECT *" in str(error)
        assert "Invalid syntax" in str(error)
        assert "not a valid query" in str(error)

    def test_missing_table_object_attribute_exception(self):
        """Test MissingTableObjectAttributeException exception."""
        error = MissingTableObjectAttributeError("my_field")
        assert "my_field" in str(error)
        assert "not provided" in str(error)

    def test_table_scan_query_exception(self):
        """Test TableScanQueryException exception."""
        error = TableScanQueryError("field_name", "STRING")
        assert "field_name" in str(error)
        assert "STRING" in str(error)
        assert "not a valid" in str(error)

    def test_table_scan_invalid_comparison_exception(self):
        """Test TableScanInvalidComparisonException exception."""
        error = TableScanInvalidComparisonError("invalid_op")
        assert "invalid_op" in str(error)
        assert "comparison operator" in str(error)

    def test_table_scan_invalid_attribute_exception(self):
        """Test TableScanInvalidAttributeException exception."""
        error = TableScanInvalidAttributeError("bad_field")
        assert "bad_field" in str(error)
        assert "table object attribute" in str(error)

    def test_table_scan_missing_attribute_exception(self):
        """Test TableScanMissingAttributeException exception."""
        error = TableScanMissingAttributeError("required_field")
        assert "required_field" in str(error)
        assert "not provided" in str(error)
