from aws_cdk import (
    Duration,
)
from aws_cdk import aws_iam as cdk_iam
from aws_cdk import aws_s3 as cdk_s3
from aws_cdk.aws_iam import IGrantable
from constructs import Construct

from da_vinci.core.resource_discovery import ResourceType
from da_vinci_cdk.constructs.access_management import ResourceAccessPolicy
from da_vinci_cdk.constructs.resource_discovery import DiscoverableResource


class Bucket(Construct):
    def __init__(
        self,
        bucket_name: str,
        construct_id: str,
        scope: Construct,
        object_expiration_days: int | None = None,
        use_specified_bucket_name: bool = False,
        **s3_kwargs,
    ) -> None:
        """
        Creates an S3 bucket

        Keyword Arguments:
            bucket_name: Name of the bucket construct, used primarily for resource discovery, can be used as the bucket name if use_real_bucket_name is True
            construct_id: ID of the construct
            scope: Parent construct for the Bucket
            object_expiration_days: Number of days before objects in the bucket expire
            s3_kwargs: Additional keyword arguments for the S3 bucket
            use_specified_bucket_name: Use the bucket_name as the bucket name (default: False)
        """
        super().__init__(scope, construct_id)

        _bucket_name = None

        if use_specified_bucket_name:
            _bucket_name = bucket_name

        lifecycle_rules = None

        if object_expiration_days:
            lifecycle_rules = [
                cdk_s3.LifecycleRule(
                    expiration=Duration.days(object_expiration_days),
                )
            ]

            if "lifecycle_rules" in s3_kwargs:
                s3_kwargs["lifecycle_rules"].extend(lifecycle_rules)

            else:
                s3_kwargs["lifecycle_rules"] = lifecycle_rules

        self.bucket = cdk_s3.Bucket(
            self, f"{construct_id}-bucket", bucket_name=_bucket_name, **s3_kwargs
        )

        self._discovery_resource = DiscoverableResource(
            construct_id=f"{construct_id}-resource",
            scope=self,
            resource_endpoint=self.bucket.bucket_name,
            resource_name=bucket_name,
            resource_type=ResourceType.BUCKET,
        )

        self.read_access_statement = cdk_iam.PolicyStatement(
            actions=[
                "s3:GetObject",
                "s3:GetObjectEncryption",
                "s3:GetObjectTagging",
                "s3:GetObjectVersion",
                "s3:ListBucket",
                "s3:ListBucketVersions",
                "s3:ListBucketMultipartUploads",
            ],
            resources=[
                self.bucket.bucket_arn,
                f"{self.bucket.bucket_arn}/*",
            ],
        )

        self.read_write_access_statement = cdk_iam.PolicyStatement(
            actions=[
                "s3:GetObject",
                "s3:GetObjectEncryption",
                "s3:GetObjectTagging",
                "s3:GetObjectVersion",
                "s3:ListBucket",
                "s3:ListBucketVersions",
                "s3:ListBucketMultipartUploads",
                "s3:PutObject",
                "s3:DeleteObject",
                "s3:AbortMultipartUpload",
                "s3:PutObjectEncryption",
                "s3:PutObjectTagging",
                "s3:DeleteObjectTagging",
                "s3:PutObjectRetention",
                "s3:PutObjectLegalHold",
            ],
            resources=[
                self.bucket.bucket_arn,
                f"{self.bucket.bucket_arn}/*",
            ],
        )

        self.write_access_statement = cdk_iam.PolicyStatement(
            actions=[
                "s3:PutObject",
                "s3:DeleteObject",
                "s3:AbortMultipartUpload",
                "s3:PutObjectEncryption",
                "s3:PutObjectTagging",
                "s3:DeleteObjectTagging",
                "s3:PutObjectRetention",
                "s3:PutObjectLegalHold",
            ],
            resources=[
                self.bucket.bucket_arn,
                f"{self.bucket.bucket_arn}/*",
            ],
        )

        self.param_access_statement = self._discovery_resource.access_statement

        for policy_name in ("read", "default"):
            self.read_access_policy = ResourceAccessPolicy(
                scope=scope,
                policy_name=policy_name,
                policy_statements=[
                    self.read_access_statement,
                    self.param_access_statement,
                ],
                resource_name=bucket_name,
                resource_type=ResourceType.BUCKET,
            )

        self.read_write_access_policy = ResourceAccessPolicy(
            scope=scope,
            policy_name="read_write",
            policy_statements=[
                self.read_write_access_statement,
                self.param_access_statement,
            ],
            resource_name=bucket_name,
            resource_type=ResourceType.BUCKET,
        )

        self.write_access_policy = ResourceAccessPolicy(
            scope=scope,
            policy_name="write",
            policy_statements=[
                self.write_access_statement,
                self.param_access_statement,
            ],
            resource_name=bucket_name,
            resource_type=ResourceType.BUCKET,
        )

    @staticmethod
    def deploy_access(construct_id: str, scope: Construct, bucket_name: str):
        """
        Sets up DaVinci access policies for a bucket arn

        Keyword Arguments:
        bucket_name: Name of the bucket to set up access for
        """
        bucket_arn = f"arn:aws:s3:::{bucket_name}"

        _discovery_resource = DiscoverableResource(
            construct_id=f"{construct_id}-resource-discovery",
            scope=scope,
            resource_endpoint=bucket_name,
            resource_name=bucket_name,
            resource_type=ResourceType.BUCKET,
        )

        read_access_statement = cdk_iam.PolicyStatement(
            actions=[
                "s3:GetObject",
                "s3:GetObjectEncryption",
                "s3:GetObjectTagging",
                "s3:GetObjectVersion",
                "s3:ListBucket",
                "s3:ListBucketVersions",
                "s3:ListBucketMultipartUploads",
            ],
            resources=[
                bucket_arn,
                f"{bucket_arn}/*",
            ],
        )

        read_write_access_statement = cdk_iam.PolicyStatement(
            actions=[
                "s3:GetObject",
                "s3:GetObjectEncryption",
                "s3:GetObjectTagging",
                "s3:GetObjectVersion",
                "s3:ListBucket",
                "s3:ListBucketVersions",
                "s3:ListBucketMultipartUploads",
                "s3:PutObject",
                "s3:DeleteObject",
                "s3:AbortMultipartUpload",
                "s3:PutObjectEncryption",
                "s3:PutObjectTagging",
                "s3:DeleteObjectTagging",
                "s3:PutObjectRetention",
                "s3:PutObjectLegalHold",
            ],
            resources=[
                bucket_arn,
                f"{bucket_arn}/*",
            ],
        )

        write_access_statement = cdk_iam.PolicyStatement(
            actions=[
                "s3:PutObject",
                "s3:DeleteObject",
                "s3:AbortMultipartUpload",
                "s3:PutObjectEncryption",
                "s3:PutObjectTagging",
                "s3:DeleteObjectTagging",
                "s3:PutObjectRetention",
                "s3:PutObjectLegalHold",
            ],
            resources=[
                bucket_arn,
                f"{bucket_arn}/*",
            ],
        )

        param_access_statement = _discovery_resource.access_statement

        for policy_name in ("read", "default"):
            ResourceAccessPolicy(
                scope=scope,
                policy_name=policy_name,
                policy_statements=[
                    read_access_statement,
                    param_access_statement,
                ],
                resource_name=bucket_name,
                resource_type=ResourceType.BUCKET,
            )

        ResourceAccessPolicy(
            scope=scope,
            policy_name="read_write",
            policy_statements=[
                read_write_access_statement,
                param_access_statement,
            ],
            resource_name=bucket_name,
            resource_type=ResourceType.BUCKET,
        )

        ResourceAccessPolicy(
            scope=scope,
            policy_name="write",
            policy_statements=[
                write_access_statement,
                param_access_statement,
            ],
            resource_name=bucket_name,
            resource_type=ResourceType.BUCKET,
        )

    def grant_read_access(self, resource: IGrantable) -> None:
        """
        Grants read access to the bucket

        Keyword Arguments:
            resource: Resource to grant read access
        """
        self.bucket.grant_read(resource)

        self._discovery_resource.grant_read(resource=resource)

    def grant_read_write_access(self, resource: IGrantable) -> None:
        """
        Grants read and write access to the bucket

        Keyword Arguments:
            resource: Resource to grant read and write access
        """
        self.bucket.grant_read_write(identity=resource)

        self._discovery_resource.grant_read(resource=resource)
