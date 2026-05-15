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
        """Validation returns None when all required variables are present."""
        # mock_environment fixture sets all required variables.
        assert validate_expected_environment_variables() is None

    def test_validate_expected_environment_variables_missing(self):
        """Validation fails on the first missing required variable."""
        # Clear environment variables.
        for key in [
            APP_NAME_ENV_NAME,
            DEPLOYMENT_ID_ENV_NAME,
            SERVICE_DISC_STOR_ENV_NAME,
        ]:
            os.environ.pop(key, None)

        with pytest.raises(MissingRequiredRuntimeVariableError) as exc_info:
            validate_expected_environment_variables()

        # validate_* wraps the env name in an "Environment variable ... not found"
        # message and passes that as the variable_name to the exception, which in
        # turn wraps it in "Required runtime variable ... not found".
        assert str(exc_info.value) == (
            f"Required runtime variable Environment variable {APP_NAME_ENV_NAME} "
            "not found not found"
        )

    def test_runtime_environment_dict_without_log_level(self):
        """runtime_environment_dict omits LOG_LEVEL when not supplied."""
        result = runtime_environment_dict(
            app_name="test-app",
            deployment_id="test-deploy",
            resource_discovery_storage="dynamodb",
        )

        assert result == {
            APP_NAME_ENV_NAME: "test-app",
            DEPLOYMENT_ID_ENV_NAME: "test-deploy",
            SERVICE_DISC_STOR_ENV_NAME: "dynamodb",
        }

    def test_runtime_environment_dict_with_log_level(self):
        """runtime_environment_dict includes LOG_LEVEL when supplied."""
        result = runtime_environment_dict(
            app_name="test-app",
            deployment_id="test-deploy",
            resource_discovery_storage="dynamodb",
            log_level="DEBUG",
        )

        assert result == {
            APP_NAME_ENV_NAME: "test-app",
            DEPLOYMENT_ID_ENV_NAME: "test-deploy",
            SERVICE_DISC_STOR_ENV_NAME: "dynamodb",
            "LOG_LEVEL": "DEBUG",
        }

    def test_load_runtime_environment_variables_success(self, mock_environment):
        """Loading all defaults maps env names to their app-usage keys."""
        result = load_runtime_environment_variables()

        assert result == {
            "app_name": "test-app",
            "deployment_id": "test-deployment",
            "resource_discovery_storage": "dynamodb",
        }

    def test_load_runtime_environment_variables_specific_vars(self, mock_environment):
        """Loading a subset returns only the requested variables."""
        result = load_runtime_environment_variables(
            variable_names=[APP_NAME_ENV_NAME, DEPLOYMENT_ID_ENV_NAME]
        )

        assert result == {
            "app_name": "test-app",
            "deployment_id": "test-deployment",
        }

    def test_load_runtime_environment_variables_unsupported(self, mock_environment):
        """Requesting an unsupported variable name raises ValueError with its name."""
        with pytest.raises(ValueError) as exc_info:
            load_runtime_environment_variables(
                variable_names=["UNSUPPORTED_VAR", APP_NAME_ENV_NAME]
            )

        message = str(exc_info.value)
        assert message.startswith("Unsupported runtime variables requested: ")
        assert "UNSUPPORTED_VAR" in message
        # Supported variables must not be reported as unsupported.
        assert APP_NAME_ENV_NAME not in message

    def test_load_runtime_environment_variables_missing(self):
        """Loading with a missing variable raises with the exact env name."""
        # Clear environment variables.
        for key in [
            APP_NAME_ENV_NAME,
            DEPLOYMENT_ID_ENV_NAME,
            SERVICE_DISC_STOR_ENV_NAME,
        ]:
            os.environ.pop(key, None)

        with pytest.raises(MissingRequiredRuntimeVariableError) as exc_info:
            load_runtime_environment_variables()

        assert str(exc_info.value) == (f"Required runtime variable {APP_NAME_ENV_NAME} not found")
