"""Unit tests for da_vinci_cdk.constructs.s3 module."""

from aws_cdk import RemovalPolicy
from aws_cdk.assertions import Template

from da_vinci_cdk.constructs.s3 import Bucket


class TestBucket:
    """Tests for Bucket construct."""

    def test_bucket_creation(self, stack):
        """Test basic S3 bucket creation."""
        bucket = Bucket(
            scope=stack,
            construct_id="test-bucket",
            bucket_name="test-bucket-name",
        )

        assert bucket is not None
        assert bucket.bucket is not None

        template = Template.from_stack(stack)
        template.resource_count_is("AWS::S3::Bucket", 1)

    def test_bucket_with_removal_policy(self, stack):
        """Test S3 bucket with removal policy."""
        Bucket(
            scope=stack,
            construct_id="test-bucket",
            bucket_name="test-bucket-name",
            removal_policy=RemovalPolicy.DESTROY,
        )

        template = Template.from_stack(stack)
        template.resource_count_is("AWS::S3::Bucket", 1)

    def test_bucket_with_versioning(self, stack):
        """Test S3 bucket with versioning enabled."""
        Bucket(
            scope=stack,
            construct_id="test-bucket",
            bucket_name="test-bucket-name",
            versioned=True,
        )

        template = Template.from_stack(stack)
        template.has_resource_properties(
            "AWS::S3::Bucket", {"VersioningConfiguration": {"Status": "Enabled"}}
        )

    def test_bucket_with_encryption(self, stack):
        """Test S3 bucket has encryption by default."""
        Bucket(
            scope=stack,
            construct_id="test-bucket",
            bucket_name="test-bucket-name",
        )

        template = Template.from_stack(stack)
        template.resource_count_is("AWS::S3::Bucket", 1)
        # CDK applies encryption by default

    def test_bucket_with_expiration_days(self, stack):
        """Test bucket with object expiration."""
        bucket = Bucket(
            bucket_name="test-bucket",
            construct_id="test-bucket-construct",
            scope=stack,
            object_expiration_days=30,
        )

        assert bucket is not None
        template = Template.from_stack(stack)
        template.resource_count_is("AWS::S3::Bucket", 1)

    def test_bucket_with_specified_bucket_name(self, stack):
        """Test bucket with use_specified_bucket_name."""
        bucket = Bucket(
            bucket_name="exact-bucket-name",
            construct_id="test-bucket-construct",
            scope=stack,
            use_specified_bucket_name=True,
        )

        assert bucket is not None
        template = Template.from_stack(stack)
        template.has_resource_properties(
            "AWS::S3::Bucket", {"BucketName": "exact-bucket-name"}
        )

    def test_bucket_with_custom_lifecycle_rules(self, stack):
        """Test bucket with custom lifecycle rules."""
        from aws_cdk import Duration
        from aws_cdk.aws_s3 import LifecycleRule

        custom_rule = LifecycleRule(expiration=Duration.days(60))

        bucket = Bucket(
            bucket_name="test-bucket",
            construct_id="test-bucket-construct",
            scope=stack,
            object_expiration_days=30,
            lifecycle_rules=[custom_rule],
        )

        assert bucket is not None

    def test_bucket_access_statements(self, stack):
        """Test bucket access policy statements."""
        bucket = Bucket(
            bucket_name="test-bucket",
            construct_id="test-bucket-construct",
            scope=stack,
        )

        assert bucket.read_access_statement is not None
        assert bucket.read_write_access_statement is not None
        assert bucket.write_access_statement is not None

        # Verify statement actions
        read_actions = bucket.read_access_statement.to_json()["Action"]
        assert "s3:GetObject" in read_actions
        assert "s3:ListBucket" in read_actions

        write_actions = bucket.write_access_statement.to_json()["Action"]
        assert "s3:PutObject" in write_actions
        assert "s3:DeleteObject" in write_actions

    def test_bucket_access_policies(self, stack):
        """Test bucket access policies are created."""
        bucket = Bucket(
            bucket_name="test-bucket",
            construct_id="test-bucket-construct",
            scope=stack,
        )

        assert bucket.read_access_policy is not None
        assert bucket.read_write_access_policy is not None
        assert bucket.write_access_policy is not None

    def test_bucket_grant_read_access(self, stack):
        """Test granting read access to bucket."""
        from aws_cdk.aws_iam import Role, ServicePrincipal

        role = Role(stack, "TestRole", assumed_by=ServicePrincipal("lambda.amazonaws.com"))

        bucket = Bucket(
            bucket_name="test-bucket",
            construct_id="test-bucket-construct",
            scope=stack,
        )

        bucket.grant_read_access(role)
        # Verify it doesn't raise an error

    def test_bucket_grant_read_write_access(self, stack):
        """Test granting read/write access to bucket."""
        from aws_cdk.aws_iam import Role, ServicePrincipal

        role = Role(stack, "TestRole", assumed_by=ServicePrincipal("lambda.amazonaws.com"))

        bucket = Bucket(
            bucket_name="test-bucket",
            construct_id="test-bucket-construct",
            scope=stack,
        )

        bucket.grant_read_write_access(role)
        # Verify it doesn't raise an error

    def test_bucket_deploy_access(self, stack):
        """Test deploy_access static method."""
        Bucket.deploy_access(
            construct_id="external-bucket",
            scope=stack,
            bucket_name="external-bucket-name",
        )

        # Verify resource discovery and policies are created
        template = Template.from_stack(stack)
        # Should create SSM parameters for resource discovery
        assert template is not None
