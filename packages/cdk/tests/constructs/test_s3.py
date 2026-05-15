"""Unit tests for da_vinci_cdk.constructs.s3 module."""

from aws_cdk import Duration, RemovalPolicy
from aws_cdk.assertions import Match, Template
from aws_cdk.aws_iam import Role, ServicePrincipal
from aws_cdk.aws_s3 import LifecycleRule

from da_vinci_cdk.constructs.s3 import Bucket


class TestBucket:
    """Tests for Bucket construct."""

    def test_bucket_creation_defaults(self, stack):
        """A bare bucket synthesizes exactly one S3 bucket that retains on
        delete/replace (CDK default) and has no caller-set name."""
        Bucket(
            scope=stack,
            construct_id="test-bucket",
            bucket_name="test-bucket-name",
        )

        template = Template.from_stack(stack)
        template.resource_count_is("AWS::S3::Bucket", 1)
        template.has_resource(
            "AWS::S3::Bucket",
            {"DeletionPolicy": "Retain", "UpdateReplacePolicy": "Retain"},
        )
        # The construct does not pass the discovery bucket_name through to the
        # physical bucket name unless use_specified_bucket_name is set.
        template.has_resource_properties(
            "AWS::S3::Bucket", Match.not_({"BucketName": "test-bucket-name"})
        )

    def test_bucket_registers_discovery_and_access_policies(self, stack):
        """A bucket publishes its endpoint via SSM and provisions the read,
        default, read_write, and write managed access policies."""
        Bucket(
            scope=stack,
            construct_id="test-bucket",
            bucket_name="test-bucket-name",
        )

        template = Template.from_stack(stack)
        # read + default share an SSM endpoint param plus each policy's own
        # discovery params; assert the access policies are all created.
        template.resource_count_is("AWS::IAM::ManagedPolicy", 4)

    def test_bucket_removal_policy_destroy(self, stack):
        """RemovalPolicy.DESTROY produces Delete deletion/replace policies."""
        Bucket(
            scope=stack,
            construct_id="test-bucket",
            bucket_name="test-bucket-name",
            removal_policy=RemovalPolicy.DESTROY,
        )

        template = Template.from_stack(stack)
        template.has_resource(
            "AWS::S3::Bucket",
            {"DeletionPolicy": "Delete", "UpdateReplacePolicy": "Delete"},
        )

    def test_bucket_with_versioning(self, stack):
        """versioned=True enables the bucket's VersioningConfiguration."""
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

    def test_bucket_without_versioning_has_no_versioning_config(self, stack):
        """A bucket created without versioning emits no VersioningConfiguration."""
        Bucket(
            scope=stack,
            construct_id="test-bucket",
            bucket_name="test-bucket-name",
        )

        template = Template.from_stack(stack)
        template.has_resource_properties(
            "AWS::S3::Bucket",
            Match.not_({"VersioningConfiguration": Match.any_value()}),
        )

    def test_bucket_with_expiration_days(self, stack):
        """object_expiration_days produces an enabled lifecycle rule with the
        exact expiration in days."""
        Bucket(
            scope=stack,
            construct_id="test-bucket-construct",
            bucket_name="test-bucket",
            object_expiration_days=30,
        )

        template = Template.from_stack(stack)
        template.has_resource_properties(
            "AWS::S3::Bucket",
            {
                "LifecycleConfiguration": {
                    "Rules": Match.array_with([{"ExpirationInDays": 30, "Status": "Enabled"}])
                }
            },
        )

    def test_bucket_with_specified_bucket_name(self, stack):
        """use_specified_bucket_name=True sets the physical bucket name."""
        Bucket(
            scope=stack,
            construct_id="test-bucket-construct",
            bucket_name="exact-bucket-name",
            use_specified_bucket_name=True,
        )

        template = Template.from_stack(stack)
        template.has_resource_properties("AWS::S3::Bucket", {"BucketName": "exact-bucket-name"})

    def test_bucket_with_custom_and_expiration_lifecycle_rules(self, stack):
        """Caller-supplied lifecycle rules are merged with the rule generated
        from object_expiration_days (two rules total)."""
        custom_rule = LifecycleRule(expiration=Duration.days(60))

        Bucket(
            scope=stack,
            construct_id="test-bucket-construct",
            bucket_name="test-bucket",
            object_expiration_days=30,
            lifecycle_rules=[custom_rule],
        )

        template = Template.from_stack(stack)
        template.has_resource_properties(
            "AWS::S3::Bucket",
            {
                "LifecycleConfiguration": {
                    "Rules": Match.array_with(
                        [
                            {"ExpirationInDays": 60, "Status": "Enabled"},
                            {"ExpirationInDays": 30, "Status": "Enabled"},
                        ]
                    )
                }
            },
        )

    def test_bucket_read_access_statement_actions(self, stack):
        """The read access statement grants GetObject/ListBucket and excludes
        any mutating action."""
        bucket = Bucket(
            scope=stack,
            construct_id="test-bucket-construct",
            bucket_name="test-bucket",
        )

        read_actions = bucket.read_access_statement.to_json()["Action"]
        assert "s3:GetObject" in read_actions
        assert "s3:ListBucket" in read_actions
        assert "s3:PutObject" not in read_actions
        assert "s3:DeleteObject" not in read_actions

    def test_bucket_write_access_statement_actions(self, stack):
        """The write access statement grants mutating actions."""
        bucket = Bucket(
            scope=stack,
            construct_id="test-bucket-construct",
            bucket_name="test-bucket",
        )

        write_actions = bucket.write_access_statement.to_json()["Action"]
        assert "s3:PutObject" in write_actions
        assert "s3:DeleteObject" in write_actions

    def test_bucket_grant_read_access_attaches_read_policy(self, stack):
        """grant_read_access attaches an IAM policy with S3 read actions scoped
        to the bucket to the grantee role."""
        role = Role(stack, "TestRole", assumed_by=ServicePrincipal("lambda.amazonaws.com"))

        bucket = Bucket(
            scope=stack,
            construct_id="test-bucket-construct",
            bucket_name="test-bucket",
        )
        bucket.grant_read_access(role)

        template = Template.from_stack(stack)
        template.has_resource_properties(
            "AWS::IAM::Policy",
            {
                "PolicyDocument": {
                    "Statement": Match.array_with(
                        [
                            Match.object_like(
                                {
                                    "Action": Match.array_with(["s3:GetObject*", "s3:List*"]),
                                    "Effect": "Allow",
                                }
                            )
                        ]
                    )
                }
            },
        )

    def test_bucket_grant_read_write_access_attaches_write_actions(self, stack):
        """grant_read_write_access attaches a policy that includes write
        actions (PutObject/DeleteObject) to the grantee role."""
        role = Role(stack, "TestRole", assumed_by=ServicePrincipal("lambda.amazonaws.com"))

        bucket = Bucket(
            scope=stack,
            construct_id="test-bucket-construct",
            bucket_name="test-bucket",
        )
        bucket.grant_read_write_access(role)

        template = Template.from_stack(stack)
        template.has_resource_properties(
            "AWS::IAM::Policy",
            {
                "PolicyDocument": {
                    "Statement": Match.array_with(
                        [
                            Match.object_like(
                                {
                                    "Action": Match.array_with(
                                        [
                                            "s3:DeleteObject*",
                                            "s3:PutObject",
                                        ]
                                    ),
                                    "Effect": "Allow",
                                }
                            )
                        ]
                    )
                }
            },
        )

    def test_bucket_deploy_access_creates_discovery_and_policies(self, stack):
        """deploy_access registers a discovery resource and the read/default/
        read_write/write access policies for an externally-owned bucket without
        creating an S3 bucket resource."""
        Bucket.deploy_access(
            construct_id="external-bucket",
            scope=stack,
            bucket_name="external-bucket-name",
        )

        template = Template.from_stack(stack)
        # No physical bucket is created for an externally-owned bucket.
        template.resource_count_is("AWS::S3::Bucket", 0)
        template.resource_count_is("AWS::IAM::ManagedPolicy", 4)
