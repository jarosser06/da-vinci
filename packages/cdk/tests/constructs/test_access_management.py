"""Unit tests for da_vinci_cdk.constructs.access_management module."""

from aws_cdk import aws_iam as cdk_iam

from da_vinci_cdk.constructs.access_management import (
    ResourceAccessPolicy,
    ResourceAccessRequest,
)


class TestResourceAccessRequest:
    """Tests for ResourceAccessRequest dataclass."""

    def test_resource_access_request_creation(self):
        """Test ResourceAccessRequest creation."""
        request = ResourceAccessRequest(
            resource_name="test-table",
            resource_type="table",
            policy_name="read",
        )

        assert request.resource_name == "test-table"
        assert request.resource_type == "table"
        assert request.policy_name == "read"


class TestResourceAccessPolicy:
    """Tests for ResourceAccessPolicy construct."""

    def test_resource_access_policy_creation(self, stack):
        """Test ResourceAccessPolicy creation."""
        policy_statements = [
            cdk_iam.PolicyStatement(
                actions=["dynamodb:GetItem", "dynamodb:Query"],
                resources=["arn:aws:dynamodb:*:*:table/test-table"],
            )
        ]

        policy = ResourceAccessPolicy(
            scope=stack,
            policy_statements=policy_statements,
            resource_name="test-table",
            resource_type="table",
            policy_name="read",
        )

        assert policy is not None
        assert policy.managed_policy is not None

    def test_resource_access_policy_with_multiple_requests(self, stack):
        """Test ResourceAccessPolicy with multiple policy statements."""
        policy_statements = [
            cdk_iam.PolicyStatement(
                actions=["dynamodb:GetItem", "dynamodb:Query"],
                resources=["arn:aws:dynamodb:*:*:table/test-table"],
            ),
            cdk_iam.PolicyStatement(
                actions=["s3:GetObject"],
                resources=["arn:aws:s3:::test-bucket/*"],
            ),
        ]

        policy = ResourceAccessPolicy(
            scope=stack,
            policy_statements=policy_statements,
            resource_name="test-resource",
            resource_type="mixed",
            policy_name="read",
        )

        assert policy is not None
        assert policy.managed_policy is not None
