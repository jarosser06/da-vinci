from typing import List, Optional

from aws_cdk import (
    aws_lambda as cdk_lambda,
    aws_iam as cdk_iam,
    Duration,
    Tags,
)

from constructs import Construct

from da_vinci.core.execution_environment import runtime_environment_dict
from da_vinci.core.global_settings import SETTINGS_ENABLED_VAR_NAME
from da_vinci.core.resource_discovery import ResourceType
from da_vinci.core.tables.settings import Setting

from da_vinci.exception_trap.client import EXCEPTION_TRAP_ENV_VAR

from da_vinci_cdk.constructs.access_management import (
    ResourceAccessRequest,
    ResourceAccessPolicy,
)
from da_vinci_cdk.constructs.base import apply_framework_tags


_DEFAULT_BASE_IMAGE = 'public.ecr.aws/lambda/python:3.11.2023.11.18.02'


class LambdaFunction(Construct):
    def __init__(self, construct_id: str, entry: str, index: str,
                 handler: str, scope: Construct,
                 allow_custom_metrics: Optional[bool] = False,
                 architecture: Optional[str] = None,
                 base_image: Optional[str] = _DEFAULT_BASE_IMAGE,
                 description: Optional[str] = None,
                 disable_framework_access_requests: Optional[bool] = False,
                 disable_image_cache: Optional[bool] = False,
                 dockerfile: Optional[str] = 'Dockerfile',
                 function_name: Optional[str] = None,
                 managed_policies: Optional[List[cdk_iam.IManagedPolicy]] = None,
                 memory_size: Optional[int] = 128,
                 resource_access_requests: Optional[List[ResourceAccessRequest]] = None,
                 timeout: Duration = Duration.seconds(30), **kwargs):

        """
        Creates a Lambda function using a Docker image

        Keyword Arguments:
            construct_id: ID of the construct
            entry: Path to the entry file
            index: Name of the entry file
            handler: Name of the handler
            scope: Parent construct for the LambdaFunction
            allow_custom_metrics: Allow custom metrics to be sent to CloudWatch
            architecture: Architecture to use for the Lambda function
            base_image: Base image to use for the Lambda function
            description: Description of the Lambda function
            disable_framework_access_requests: Disables the automatic creation of resource access policies used by common framework features (e.g. global settings)
            disable_image_cache: Disables the Docker image cache
            dockerfile: The name of the Dockerfile to use for the Lambda function
            function_name: Name of the Lambda function
            managed_policies: List of managed policies to attach to the Lambda function
            memory_size: Amount of memory to allocate to the Lambda function
            timeout: Timeout for the Lambda function
            kwargs: Additional arguments supported by CDK to pass to the Lambda function

        Example:
            ```
            from da_vinci_cdk.constructs import LambdaFunction

            my_function = LambdaFunction(
                construct_id='MyLambdaFunction',
                entry='path/to/entry',
                index='index.py',
                handler='handler',
                scope=scope,
            )
            ```
        """
        super().__init__(scope, construct_id)

        if allow_custom_metrics:
            initial_access_statements = [
                cdk_iam.PolicyStatement(
                    actions=['cloudwatch:PutMetricData'],
                    effect=cdk_iam.Effect.ALLOW,
                    resources=['*'],
                )
            ]
        else:
            initial_access_statements = []

        self.architecture = architecture or scope.node.get_context('architecture')

        environment = runtime_environment_dict(
            app_name=scope.node.get_context('app_name'),
            deployment_id=scope.node.get_context('deployment_id'),
        )

        environment[SETTINGS_ENABLED_VAR_NAME] = str(
            scope.node.get_context('global_settings_enabled')
        )

        exception_trap_enabled = scope.node.get_context('exception_trap_enabled')

        environment[EXCEPTION_TRAP_ENV_VAR] = str(exception_trap_enabled)

        fn_index = index.replace('.py', '')

        cmd = [f'{fn_index}.{handler}']

        build_args = {
            'FUNCTION_HANDLER': handler,
            'FUNCTION_INDEX': fn_index,
            'IMAGE': base_image
        }

        code = cdk_lambda.DockerImageCode.from_image_asset(
            cache_disabled=disable_image_cache,
            cmd=cmd,
            directory=entry,
            file=dockerfile,
            build_args=build_args,
        )

        self.function = cdk_lambda.DockerImageFunction(
            self,
            f'{construct_id}-fn',
            architecture=self.architecture,
            code=code,
            description=description,
            environment=environment,
            function_name=function_name,
            initial_policy=initial_access_statements,
            memory_size=memory_size,
            timeout=timeout,
            **kwargs
        )

        Tags.of(self.function).add(
            key='DaVinciFramework::FunctionPurpose',
            value='General',
            priority=100
        )
        apply_framework_tags(self.function, self)

        _managed_policies = managed_policies or []

        global_settings_enabled = scope.node.get_context('global_settings_enabled')

        if global_settings_enabled and not disable_framework_access_requests:
            # Check if settings table requests are already present
            add_settings_table_access = True

            if resource_access_requests:
                for existing_req in resource_access_requests:
                    if existing_req.resource_name == Setting.table_name:
                        add_settings_table_access = False
                        break
            else:
                resource_access_requests = []

            if add_settings_table_access:
                resource_access_requests.append(
                    ResourceAccessRequest(
                        policy_name='read',
                        resource_type=ResourceType.TABLE,
                        resource_name=Setting.table_name,
                    )
                )

        Tags.of(self.function).add(
            key='DaVinciFramework::GlobalSettingsEnabled',
            value=str(global_settings_enabled),
            priority=100
        )

        if exception_trap_enabled and not disable_framework_access_requests:
            # Check if exceptions table requests are already present
            add_exceptions_access = True

            if resource_access_requests:
                for existing_req in resource_access_requests:
                    if existing_req.resource_name == 'exceptions_trap':
                        add_exceptions_access = False
                        break
            else:
                resource_access_requests = []

            if add_exceptions_access:
                resource_access_requests.append(
                    ResourceAccessRequest(
                        resource_type=ResourceType.REST_SERVICE,
                        resource_name='exceptions_trap',
                    )
                )

        Tags.of(self.function).add(
            key='DaVinciFramework::ExceptionsTrapEnabled',
            value=str(exception_trap_enabled),
            priority=100
        )

        if resource_access_requests:
            resource_access_policies = ResourceAccessPolicy.multi_policy_import(
                construct_id_prefix=construct_id,
                resource_access_requests=resource_access_requests,
                scope=self,
            )

            _managed_policies.extend(resource_access_policies)

        if _managed_policies:
            for policy in _managed_policies:
                self.function.role.add_managed_policy(policy)