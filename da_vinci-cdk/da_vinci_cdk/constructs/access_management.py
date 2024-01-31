from dataclasses import dataclass
from typing import List, Optional

from aws_cdk import (
    aws_iam as cdk_iam,
)

from constructs import Construct

from da_vinci_cdk.constructs.base import GlobalVariable


_ACCESS_MANAGEMENT_PREFIX = '/da_vinci_v1/access_management'
_DEFAULT_POLICY_NAME = 'default'


@dataclass
class ResourceAccessRequest:
    """
    ResourceAccessRequest is a dataclass that represents a request to access a
    resource.

    Keyword Arguments:
        app_name: Name of the application
        policy_name: Name of the policy, defaults to "default"
        resource_name: Name of the resource
        resource_type: Type of the resource

    Example:
        ```
        from da_vinci_cdk.constructs.access_management import ResourceAccessRequest

        request = ResourceAccessRequest(
            resource_name='da_vinci',
            resource_type='bucket',
        )
        ```
    """
    resource_name: str
    resource_type: str
    app_name: Optional[str] = None
    policy_name: Optional[str] = _DEFAULT_POLICY_NAME


class ResourceAccessPolicy(Construct):
    def __init__(self, policy_statements: List[cdk_iam.PolicyStatement],
                 resource_name: str, resource_type: str, scope: Construct,
                 app_name: Optional[str] = None,
                 deployment_id: Optional[str] = None,
                 policy_name: Optional[str] = _DEFAULT_POLICY_NAME):
        """
        ResourceAccessPolicy is a wrapper around an IAM policy that is used to
        grant access to a resource.

        Keyword Arguments:
            app_name: Name of the application
            deployment_id: Unique identifier for the installation
            policy_statements: List of policy statements to add to the policy
            resource_name: Name of the resource
            resource_type: Type of the resource
            scope: Parent construct for the ResourceAccessPolicy
            policy_name: Name of the policy, defaults to "default"

        Example:
            ```
            from aws_cdk import aws_iam as cdk_iam

            from da_vinci_cdk.constructs.access_management import ResourceAccessPolicy

            policy = ResourceAccessPolicy(
                policy_statements=[
                    cdk_iam.PolicyStatement(
                        actions=[
                            's3:GetObject',
                        ],
                        resources=[
                            'arn:aws:s3:::da_vinci/*',
                        ],
                    ),
                ],
                resource_name='da_vinci',
                resource_type='bucket',
                scope=self,
            )
            ```
        """

        construct_id = f'resource-access-policy-{resource_name}-{resource_type}-{policy_name}'

        super().__init__(scope, construct_id)

        self.app_name = app_name or scope.node.get_context('app_name')
        self.deployment_id = deployment_id or scope.node.get_context('deployment_id')

        self.policy_name = policy_name
        self.resource_name = resource_name
        self.resource_type = resource_type

        self.managed_policy = cdk_iam.ManagedPolicy(
            scope=scope,
            id=f'managed-policy-{resource_name}-{resource_type}-{policy_name}',
            statements=policy_statements,
        )

        param_name = self._gen_parameter_name(
            app_name=self.app_name,
            deployment_id=self.deployment_id,
            policy_name=policy_name,
            resource_name=resource_name,
            resource_type=resource_type,
        )

        self.variable = GlobalVariable(
            construct_id=f'access-policy-global-{resource_name}-{resource_type}-{policy_name}',
            scope=self,
            ssm_key=param_name,
            ssm_value=self.managed_policy.managed_policy_arn,
        )

    @classmethod
    def _gen_parameter_name(cls, app_name: str, deployment_id: str, policy_name: str,
                            resource_name: str, resource_type: str) -> str:
        """
        Generate a resource name for a service discovery resource

        Keyword Arguments:
            app_name: Name of the application
            deployment_id: Unique identifier for the installation
            resource_name: Name of the resource
            resource_type: Type of the resource
        """

        return '/'.join([
            _ACCESS_MANAGEMENT_PREFIX,
            app_name,
            deployment_id,
            resource_type,
            resource_name,
            policy_name,
        ])

    @classmethod
    def policy_from_resource_name(cls, request: ResourceAccessRequest, scope: Construct,
                                  app_name: Optional[str] = None, construct_id_prefix: Optional[str] = None,
                                  deployment_id: Optional[str] = None) -> cdk_iam.ManagedPolicy:
        """
        Generate a resource name for a access management resource

        Keyword Arguments:
            app_name: Name of the application
            deployment_id: Unique identifier for the installation
            request: ResourceAccessRequest to import
            scope: Parent construct for the ResourceAccessPolicy
        """
        app_name = request.app_name or app_name or scope.node.get_context('app_name')
        deployment_id = deployment_id or scope.node.get_context('deployment_id')

        param_name = cls._gen_parameter_name(
            app_name=app_name,
            deployment_id=deployment_id,
            policy_name=request.policy_name,
            resource_name=request.resource_name,
            resource_type=request.resource_type,
        )

        policy_arn = GlobalVariable.load_variable(
            scope=scope,
            ssm_key=param_name,
        )

        policy_ret_id = f'managed-policy-retrieval-{request.resource_name}-{request.resource_type}-{request.policy_name}'

        if construct_id_prefix:
            policy_ret_id = f'{construct_id_prefix}-{policy_ret_id}'

        policy = cdk_iam.ManagedPolicy.from_managed_policy_arn(
            scope=scope,
            id=policy_ret_id,
            managed_policy_arn=policy_arn,
        )

        return policy

    @classmethod
    def multi_policy_import(cls, resource_access_requests: List[ResourceAccessRequest],
                            scope: Construct, app_name: Optional[str] = None,
                            construct_id_prefix: Optional[str] = None,
                            deployment_id: Optional[str] = None) -> List[cdk_iam.ManagedPolicy]:
        """
        Import multiple policies from SSM

        Keyword Arguments:
            resource_access_requests: List of ResourceAccessRequests to import
            scope: Parent construct for the ResourceAccessPolicy
            app_name: Name of the application
            construct_id_prefix: Optional Prefix for the construct ID, needed for
                                      when multiple imports are utilized in one stack with
                                      overlapping resource names.
            deployment_id: Unique identifier for the installation

        Returns:
            List of ManagedPolicies

        Example:
            ```
            from aws_cdk import aws_iam as cdk_iam

            from da_vinci_cdk.constructs.access_management import (
                ResourceAccessPolicy,
                ResourceAccessRequest,
            )

            policies = ResourceAccessPolicy.multi_policy_import(
                resource_access_requests=[
                    ResourceAccessRequest(
                        resource_name='da_vinci',
                        resource_type='bucket',
                    ),
                ],
                scope=self,
            )
            ```
        """

        policies = []

        for resource_access_request in resource_access_requests:
            policy = cls.policy_from_resource_name(
                app_name=app_name,
                construct_id_prefix=construct_id_prefix,
                deployment_id=deployment_id,
                request=resource_access_request,
                scope=scope,
            )

            policies.append(policy)

        return policies