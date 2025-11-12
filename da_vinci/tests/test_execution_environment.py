"""Tests for execution environment utilities."""

import os

import pytest

from da_vinci.core.exceptions import MissingRequiredRuntimeVariableError
from da_vinci.core.execution_environment import (
    APP_NAME_ENV_NAME,
    DEPLOYMENT_ID_ENV_NAME,
    SERVICE_DISC_STOR_ENV_NAME,
    load_runtime_environment_variables,
    runtime_environment_dict,
    validate_expected_environment_variables,
)


@pytest.mark.unit
class TestExecutionEnvironment:
    """Test execution environment utilities."""

    def test_validate_expected_environment_variables_success(self, mock_environment):
        """Test validation succeeds when all required variables are present."""
        # mock_environment fixture sets all required variables
        # Should not raise an exception
        validate_expected_environment_variables()

    def test_validate_expected_environment_variables_missing(self):
        """Test validation fails when required variables are missing."""
        # Clear environment variables
        for key in [APP_NAME_ENV_NAME, DEPLOYMENT_ID_ENV_NAME, SERVICE_DISC_STOR_ENV_NAME]:
            os.environ.pop(key, None)

        with pytest.raises(MissingRequiredRuntimeVariableError) as exc_info:
            validate_expected_environment_variables()

        # Should mention the environment variable name
        assert "DA_VINCI_" in str(exc_info.value)

    def test_runtime_environment_dict_without_log_level(self):
        """Test runtime_environment_dict without log_level parameter."""
        result = runtime_environment_dict(
            app_name="test-app",
            deployment_id="test-deploy",
            resource_discovery_storage="dynamodb",
        )

        assert result[APP_NAME_ENV_NAME] == "test-app"
        assert result[DEPLOYMENT_ID_ENV_NAME] == "test-deploy"
        assert result[SERVICE_DISC_STOR_ENV_NAME] == "dynamodb"
        assert "LOG_LEVEL" not in result

    def test_runtime_environment_dict_with_log_level(self):
        """Test runtime_environment_dict with log_level parameter."""
        result = runtime_environment_dict(
            app_name="test-app",
            deployment_id="test-deploy",
            resource_discovery_storage="dynamodb",
            log_level="DEBUG",
        )

        assert result[APP_NAME_ENV_NAME] == "test-app"
        assert result[DEPLOYMENT_ID_ENV_NAME] == "test-deploy"
        assert result[SERVICE_DISC_STOR_ENV_NAME] == "dynamodb"
        assert result["LOG_LEVEL"] == "DEBUG"

    def test_load_runtime_environment_variables_success(self, mock_environment):
        """Test loading runtime environment variables successfully."""
        result = load_runtime_environment_variables()

        assert result["app_name"] == "test-app"
        assert result["deployment_id"] == "test-deployment"
        assert result["resource_discovery_storage"] == "dynamodb"

    def test_load_runtime_environment_variables_specific_vars(self, mock_environment):
        """Test loading specific runtime environment variables."""
        result = load_runtime_environment_variables(
            variable_names=[APP_NAME_ENV_NAME, DEPLOYMENT_ID_ENV_NAME]
        )

        assert result["app_name"] == "test-app"
        assert result["deployment_id"] == "test-deployment"
        assert "resource_discovery_storage" not in result

    def test_load_runtime_environment_variables_unsupported(self, mock_environment):
        """Test loading unsupported runtime environment variables raises error."""
        with pytest.raises(ValueError, match="Unsupported runtime variables"):
            load_runtime_environment_variables(
                variable_names=["UNSUPPORTED_VAR", APP_NAME_ENV_NAME]
            )

    def test_load_runtime_environment_variables_missing(self):
        """Test loading runtime environment variables when they're missing."""
        # Clear environment variables
        for key in [APP_NAME_ENV_NAME, DEPLOYMENT_ID_ENV_NAME, SERVICE_DISC_STOR_ENV_NAME]:
            os.environ.pop(key, None)

        with pytest.raises(MissingRequiredRuntimeVariableError) as exc_info:
            load_runtime_environment_variables()

        assert "DA_VINCI_" in str(exc_info.value)
