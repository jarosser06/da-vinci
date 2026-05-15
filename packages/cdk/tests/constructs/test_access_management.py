"""Unit tests for da_vinci_cdk.constructs.access_management module."""

from aws_cdk import aws_iam as cdk_iam
from aws_cdk.assertions import Match, Template

from da_vinci_cdk.constructs.access_management import (
    ResourceAccessPolicy,
    ResourceAccessRequest,
)


class TestResourceAccessRequest:
    """Tests for ResourceAccessRequest dataclass."""

    def test_explicit_fields_retained(self):
        """All explicitly supplied fields are stored verbatim."""
        request = ResourceAccessRequest(
            resource_name="test-table",
            resource_type="table",
            policy_name="read",
        )

        assert request.resource_name == "test-table"
        assert request.resource_type == "table"
        assert request.policy_name == "read"
        assert request.app_name is None

    def test_policy_name_defaults_to_default(self):
        """policy_name defaults to 'default' when omitted."""
        request = ResourceAccessRequest(
            resource_name="test-table",
            resource_type="table",
        )

        assert request.policy_name == "default"


class TestResourceAccessPolicy:
    """Tests for ResourceAccessPolicy construct."""

    def test_creates_managed_policy_with_exact_statement(self, stack):
        """The managed policy carries exactly the supplied statement."""
        ResourceAccessPolicy(
            scope=stack,
            policy_statements=[
                cdk_iam.PolicyStatement(
                    actions=["dynamodb:GetItem", "dynamodb:Query"],
                    resources=["arn:aws:dynamodb:*:*:table/test-table"],
                )
            ],
            resource_name="test-table",
            resource_type="table",
            policy_name="read",
        )

        template = Template.from_stack(stack)
        template.resource_count_is("AWS::IAM::ManagedPolicy", 1)
        template.has_resource_properties(
            "AWS::IAM::ManagedPolicy",
            {
                "PolicyDocument": {
                    "Statement": [
                        {
                            "Action": ["dynamodb:GetItem", "dynamodb:Query"],
                            "Effect": "Allow",
                            "Resource": "arn:aws:dynamodb:*:*:table/test-table",
                        }
                    ],
                    "Version": "2012-10-17",
                }
            },
        )

    def test_publishes_policy_arn_to_ssm_at_deterministic_path(self, stack):
        """The managed-policy ARN is published to the access-management SSM path."""
        ResourceAccessPolicy(
            scope=stack,
            policy_statements=[
                cdk_iam.PolicyStatement(
                    actions=["dynamodb:GetItem"],
                    resources=["arn:aws:dynamodb:*:*:table/test-table"],
                )
            ],
            resource_name="test-table",
            resource_type="table",
            policy_name="read",
        )

        template = Template.from_stack(stack)
        template.resource_count_is("AWS::SSM::Parameter", 1)
        template.has_resource_properties(
            "AWS::SSM::Parameter",
            {
                "Name": (
                    "/da_vinci_framework/access_management/test-app/"
                    "test-deployment/table/test-table/read"
                ),
                "Type": "String",
                "Value": Match.any_value(),
            },
        )

    def test_multiple_statements_preserved_in_order(self, stack):
        """Multiple statements are emitted in order into a single managed policy."""
        ResourceAccessPolicy(
            scope=stack,
            policy_statements=[
                cdk_iam.PolicyStatement(
                    actions=["dynamodb:GetItem", "dynamodb:Query"],
                    resources=["arn:aws:dynamodb:*:*:table/test-table"],
                ),
                cdk_iam.PolicyStatement(
                    actions=["s3:GetObject"],
                    resources=["arn:aws:s3:::test-bucket/*"],
                ),
            ],
            resource_name="test-resource",
            resource_type="mixed",
            policy_name="read",
        )

        template = Template.from_stack(stack)
        template.resource_count_is("AWS::IAM::ManagedPolicy", 1)
        template.has_resource_properties(
            "AWS::IAM::ManagedPolicy",
            {
                "PolicyDocument": {
                    "Statement": [
                        {
                            "Action": ["dynamodb:GetItem", "dynamodb:Query"],
                            "Effect": "Allow",
                            "Resource": "arn:aws:dynamodb:*:*:table/test-table",
                        },
                        {
                            "Action": "s3:GetObject",
                            "Effect": "Allow",
                            "Resource": "arn:aws:s3:::test-bucket/*",
                        },
                    ],
                    "Version": "2012-10-17",
                }
            },
        )

    def test_ssm_value_references_managed_policy(self, stack):
        """The SSM parameter value Refs the managed policy logical id."""
        ResourceAccessPolicy(
            scope=stack,
            policy_statements=[
                cdk_iam.PolicyStatement(
                    actions=["dynamodb:GetItem"],
                    resources=["arn:aws:dynamodb:*:*:table/test-table"],
                )
            ],
            resource_name="test-table",
            resource_type="table",
            policy_name="read",
        )

        template = Template.from_stack(stack)
        managed_policies = template.find_resources("AWS::IAM::ManagedPolicy")
        assert len(managed_policies) == 1
        managed_policy_id = next(iter(managed_policies))

        params = template.find_resources("AWS::SSM::Parameter")
        assert len(params) == 1
        param = next(iter(params.values()))
        assert param["Properties"]["Value"] == {"Ref": managed_policy_id}

    def test_gen_parameter_name_layout(self):
        """The parameter name composes the access-management path segments."""
        name = ResourceAccessPolicy._gen_parameter_name(
            app_name="my-app",
            deployment_id="prod",
            policy_name="read_write",
            resource_name="orders",
            resource_type="table",
        )

        assert name == ("/da_vinci_framework/access_management/my-app/prod/table/orders/read_write")
