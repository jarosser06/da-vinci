
from constructs import Construct

from aws_cdk import (
    aws_iam as cdk_iam,
    aws_s3 as cdk_s3,
)

from da_vinci.core.resource_discovery import ResourceType

from da_vinci_cdk.constructs.access_management import ResourceAccessPolicy
from da_vinci_cdk.constructs.resource_discovery import DiscoverableResource


class Bucket(Construct):
    def __init__(self, bucket_name: str, construct_id: str, scope: Construct, use_specified_bucket_name: bool = False,
                 **s3_kwargs) -> None:
        """
        Creates an S3 bucket

        Keyword Arguments:
            bucket_name: Name of the bucket construct, used primarily for resource discovery, can be used as the bucket name if use_real_bucket_name is True
            construct_id: ID of the construct
            scope: Parent construct for the Bucket
            s3_kwargs: Additional keyword arguments for the S3 bucket
            use_specified_bucket_name: Use the bucket_name as the bucket name (default: False)
        """
        super().__init__(scope, construct_id)

        _bucket_name = None

        if use_specified_bucket_name:
            _bucket_name = bucket_name

        self.bucket = cdk_s3.Bucket(
            self,
            f"{construct_id}-bucket",
            bucket_name=_bucket_name,
            **s3_kwargs
        )

        self._discovery_resource = DiscoverableResource(
            construct_id=f'{construct_id}-resource',
            scope=self,
            resource_endpoint=self.bucket.bucket_name,
            resource_name=bucket_name,
            resource_type=ResourceType.BUCKET,
        )

        self.read_access_statement = cdk_iam.PolicyStatement(
            actions=[
                's3:GetObject',
                's3:GetObjectEncryption',
                's3:GetObjectTagging',
                's3:GetObjectVersion',
                's3:ListBucket',
                's3:ListBucketVersions',
                's3:ListBucketMultipartUploads',
            ],
            resources=[
                self.bucket.bucket_arn,
                f'{self.bucket.bucket_arn}/*',
            ],
        )

        self.read_write_access_statement = cdk_iam.PolicyStatement(
            actions=[
                's3:GetObject',
                's3:GetObjectEncryption',
                's3:GetObjectTagging',
                's3:GetObjectVersion',
                's3:ListBucket',
                's3:ListBucketVersions',
                's3:ListBucketMultipartUploads',
                's3:PutObject',
                's3:DeleteObject',
                's3:AbortMultipartUpload',
                's3:PutObjectEncryption',
                's3:PutObjectTagging',
                's3:DeleteObjectTagging',
                's3:PutObjectRetention',
                's3:PutObjectLegalHold',
            ],
            resources=[
                self.bucket.bucket_arn,
                f'{self.bucket.bucket_arn}/*',
            ],
        )

        self.write_access_statement = cdk_iam.PolicyStatement(
            actions=[
                's3:PutObject',
                's3:DeleteObject',
                's3:AbortMultipartUpload',
                's3:PutObjectEncryption',
                's3:PutObjectTagging',
                's3:DeleteObjectTagging',
                's3:PutObjectRetention',
                's3:PutObjectLegalHold',
            ],
            resources=[
                self.bucket.bucket_arn,
                f'{self.bucket.bucket_arn}/*',
            ],
        )

        self.param_access_statement = self._discovery_resource.parameter.access_statement()

        for policy_name in ('read', 'default'):
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
            policy_name='read_write',
            policy_statements=[
                self.read_write_access_statement,
                self.param_access_statement,
            ],
            resource_name=bucket_name,
            resource_type=ResourceType.BUCKET,
        )

        self.write_access_policy = ResourceAccessPolicy(
            scope=scope,
            policy_name='write',
            policy_statements=[
                self.write_access_statement,
                self.param_access_statement,
            ],
            resource_name=bucket_name,
            resource_type=ResourceType.BUCKET,
        )

    def grant_read_access(self, resource: Construct) -> None:
        """
        Grants read access to the bucket

        Keyword Arguments:
            resource: Resource to grant read access
        """
        self.bucket.grant_read(resource)

        self._discovery_resource.parameter.grant_read(resource)

    def grant_read_write_access(self, resource: Construct) -> None:
        """
        Grants read and write access to the bucket

        Keyword Arguments:
            resource: Resource to grant read and write access
        """
        self.bucket.grant_read_write(resource)

        self._discovery_resource.parameter.grant_read(resource)