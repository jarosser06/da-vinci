"""
Common CDK constructs used across the framework
"""

from aws_cdk import (
    Tags,
)
from aws_cdk import aws_iam as cdk_iam
from aws_cdk import aws_ssm as cdk_ssm
from constructs import Construct

from da_vinci.core.base import standard_aws_resource_name


def custom_type_name(name: str, prefix: str | None = "DaVinci", separator: str | None = "@") -> str:
    """
    Create a custom type name for a construct

    Keyword Arguments:
        name: The name of the construct
        prefix: The prefix to use for the custom type name (defaults to 'DaVinci')
        separator: The separator to use between the prefix and name (defaults to '::')
    """

    return f"Custom::{prefix}{separator}{name}"


def resource_namer(
    name: str, scope: Construct, app_name: str | None = None, deployment_id: str | None = None
) -> str:
    """
    Generate a name for a resource by adding a prefix of app_name-deployment_id

    Keyword Arguments:
    name -- The name of the resource
    scope -- The scope of the construct
    app_name -- The name of the application (optional, defaults to context value)
    deployment_id -- The deployment ID (optional, defaults to context value)
    """
    if not app_name:
        app_name = scope.node.get_context("app_name")

    if not deployment_id:
        deployment_id = scope.node.get_context("deployment_id")

    return standard_aws_resource_name(app_name, deployment_id, name)


def apply_framework_tags(resource: Construct, scope: Construct):
    """Apply framework tags to a resource"""
    app_name = scope.node.get_context("app_name")
    Tags.of(resource).add("DaVinciFramework::ApplicationName", app_name)

    deployment_id = scope.node.get_context("deployment_id")
    Tags.of(resource).add("DaVinciFramework::DeploymentId", deployment_id)

    Tags.of(resource).add("DaVinciFrameworkManaged", "True")


class GlobalVariable(Construct):
    def __init__(self, construct_id: str, scope: Construct, ssm_key: str, ssm_value: str):
        """
        Initialize a GlobalVariable object

        GlobalVariable is a wrapper around a SSM parameter that is used to
        store a value that can be shared across multiple stacks. The SSM Key would
        need to be unique for the entire application.

        Keyword Arguments:
            construct_id: Identifier for the construct
            scope: Parent construct for the CrossStackVariable
            ssm_key: SSM key to store the value in
            ssm_value: Value to store in the SSM parameter

        Example:
            ```
            from da_vinci_cdk.constructs.base import GlobalVariable

            global_var = GlobalVariable(
                construct_id='my_global_var-construct',
                scope=scope,
                ssm_key='my_global_var',
                ssm_value='my value',
            )
        """

        super().__init__(scope, construct_id)

        self.ssm_key = ssm_key
        self.ssm_value = ssm_value

        self.ssm_parameter = cdk_ssm.StringParameter(
            scope=self,
            id=f"global-var-{self.ssm_key}",
            parameter_name=self.ssm_key,
            simple_name=False,
            string_value=self.ssm_value,
        )

    @staticmethod
    def load_variable(scope: Construct, ssm_key: str) -> str:
        """
        Load a GlobalVariable from SSM

        Keyword Arguments:
            construct_id: Identifier for the construct
            scope: Parent construct for the CrossStackVariable
            ssm_key: SSM key to load the value from
        """

        variable = cdk_ssm.StringParameter.value_for_string_parameter(
            scope=scope,
            parameter_name=ssm_key,
        )

        return variable

    def access_statement(self) -> cdk_iam.PolicyStatement:
        """
        Generate a policy statement to access the GlobalVariable
        """

        return cdk_iam.PolicyStatement(
            actions=[
                "ssm:DescribeParameters",
                "ssm:GetParameters",
                "ssm:GetParameter",
                "ssm:GetParameterHistory",
            ],
            resources=[self.ssm_parameter.parameter_arn],
        )

    def grant_read(self, resource: Construct):
        """
        Grant read access to the GlobalVariable

        Keyword Arguments:
            resource: Resource to grant access to
        """
        self.ssm_parameter.grant_read(resource)
