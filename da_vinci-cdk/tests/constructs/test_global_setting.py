"""Unit tests for da_vinci_cdk.constructs.global_setting module."""

import pytest
from aws_cdk import App, Stack
from aws_cdk.assertions import Template

from da_vinci.core.exceptions import GlobalSettingsNotEnabledError
from da_vinci.core.tables.global_settings_table import GlobalSetting as GlobalSettingTblObj
from da_vinci.core.tables.global_settings_table import GlobalSettingType
from da_vinci_cdk.constructs.global_setting import GlobalSetting, GlobalSettingLookup


class TestGlobalSetting:
    """Tests for GlobalSetting construct."""

    def test_global_setting_creation(self, stack):
        """Test GlobalSetting creation."""
        setting = GlobalSetting(
            namespace="test-namespace",
            scope=stack,
            setting_key="test-key",
            description="Test description",
            setting_value="test-value",
        )

        assert setting is not None
        template = Template.from_stack(stack)
        assert template is not None

    def test_global_setting_with_different_type(self, stack):
        """Test GlobalSetting with different setting type."""
        setting = GlobalSetting(
            namespace="test-namespace",
            scope=stack,
            setting_key="test-key",
            setting_type=GlobalSettingType.INTEGER,
            setting_value="123",
        )

        assert setting is not None

    def test_global_setting_with_boolean_type(self, stack):
        """Test GlobalSetting with boolean type."""
        setting = GlobalSetting(
            namespace="test-namespace",
            scope=stack,
            setting_key="test-key",
            setting_type=GlobalSettingType.BOOLEAN,
            setting_value="true",
        )

        assert setting is not None

    def test_global_setting_with_string_type(self, stack):
        """Test GlobalSetting with STRING type."""
        setting = GlobalSetting(
            namespace="test-namespace",
            scope=stack,
            setting_key="test-key",
            setting_type=GlobalSettingType.STRING,
            setting_value="test string value",
        )

        assert setting is not None

    def test_global_setting_without_description(self, stack):
        """Test GlobalSetting without description."""
        setting = GlobalSetting(
            namespace="test-namespace",
            scope=stack,
            setting_key="test-key",
            setting_value="test-value",
        )

        assert setting is not None

    def test_global_setting_disabled_raises_error(self):
        """Test GlobalSetting raises error when global settings disabled."""
        app = App(
            context={
                "app_name": "test-app",
                "deployment_id": "test-deployment",
                "global_settings_enabled": False,
            }
        )
        stack = Stack(app, "TestStack")

        with pytest.raises(GlobalSettingsNotEnabledError):
            GlobalSetting(
                namespace="test-namespace",
                scope=stack,
                setting_key="test-key",
                setting_value="test-value",
            )

    def test_global_setting_from_definition(self, stack):
        """Test GlobalSetting.from_definition class method."""
        tbl_obj = GlobalSettingTblObj(
            namespace="test-namespace",
            setting_key="test-key",
            description="Test description",
            setting_type=GlobalSettingType.STRING,
            setting_value="test-value",
        )

        setting = GlobalSetting.from_definition(setting=tbl_obj, scope=stack)

        assert setting is not None


class TestGlobalSettingLookup:
    """Tests for GlobalSettingLookup construct."""

    def test_global_setting_lookup_creation(self, stack):
        """Test GlobalSettingLookup creation."""
        lookup = GlobalSettingLookup(
            scope=stack,
            construct_id="test-lookup",
            namespace="test-namespace",
            setting_key="test-key",
        )

        assert lookup is not None
        assert lookup.namespace == "test-namespace"
        assert lookup.setting_key == "test-key"

    def test_global_setting_lookup_get_value(self, stack):
        """Test GlobalSettingLookup get_value method."""
        lookup = GlobalSettingLookup(
            scope=stack,
            construct_id="test-lookup",
            namespace="test-namespace",
            setting_key="test-key",
        )

        # The method returns a token, so we just verify it doesn't raise
        value = lookup.get_value()
        assert value is not None
