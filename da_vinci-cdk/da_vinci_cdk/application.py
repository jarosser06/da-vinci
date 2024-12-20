from os import getenv
from os.path import (
    join as path_join,
    realpath,
)

from typing import Optional

from aws_cdk import App as CDKApp
from aws_cdk import (
    aws_lambda as cdk_lambda,
    DockerImage,
)

from constructs import Construct

from da_vinci_cdk.constructs.dns import PublicDomain
from da_vinci_cdk.constructs.global_setting import GlobalSetting
from da_vinci_cdk.constructs.s3 import Bucket
from da_vinci_cdk.framework_stacks.event_bus.stack import EventBusStack
from da_vinci_cdk.framework_stacks.global_settings.stack import GlobalSettingsStack
from da_vinci_cdk.framework_stacks.exceptions_trap.stack import ExceptionsTrapStack
from da_vinci_cdk.stack import Stack


DA_VINCI_DISABLE_DOCKER_CACHE = getenv('DA_VINCI_DISABLE_DOCKER_CACHE', False)


class CoreStack(Stack):
    def __init__(self, app_name: str, deployment_id: str, scope: Construct, stack_name: str,
                 create_hosted_zone: bool = True, global_settings_enabled: bool = True,
                 root_domain_name: Optional[str] = None, s3_logging_bucket_name: str = None,
                 s3_logging_bucket_object_retention_days: Optional[int] = None, using_external_logging_bucket: bool = False):
        """
        Bootstrap the initial infrastructure required to stand up a DaVinci

        Keyword Arguments:
            app_name: Name of the application
            create_hosted_zone: Whether to create a hosted zone for the application if the root_domain_name is set (default: True)
            deployment_id: Identifier assigned to the installation
            global_settings_enabled: Whether to build the global settings stack as part of the application (default: True)
            root_domain_name: Root domain name for the application (default: None)
            scope: Parent construct for the stack
            stack_name: Name of the stack
            s3_logging_bucket_name: Name of the S3 bucket to use for logging (default: None)
            s3_logging_bucket_object_retention_days: Number of days before objects in the bucket expire (default: None)
            using_external_logging_bucket: Whether or not a pre-existing bucket is being used for logging(default: False)
        """

        super().__init__(
            app_name=app_name,
            deployment_id=deployment_id,
            scope=scope,
            stack_name=stack_name
        )

        if global_settings_enabled:
            self.add_required_stack(GlobalSettingsStack)

            GlobalSetting(
                description='Whether Global settings are enabled. Managed by framework deployment, do not modify!',
                namespace='da_vinci_framework::core',
                setting_key='global_settings_enabled',
                setting_value=True,
                scope=self,
            )

            GlobalSetting(
                description='The name of the S3 Logging Bucket, null if not used. Managed by framework deployment, modify at your own risk!',
                namespace='da_vinci_framework::core',
                setting_key='s3_logging_bucket',
                setting_value=s3_logging_bucket_name,
                scope=self,
            )

            core_str_setting_keys = [
                'app_name',
                'deployment_id',
                'log_level',
            ]

            for setting_key in core_str_setting_keys:
                GlobalSetting(
                    description=f'The {setting_key} available to all components of the application.',
                    namespace='da_vinci_framework::core',
                    setting_key=setting_key,
                    setting_value=self.node.get_context(setting_key),
                    scope=self,
                )

        if s3_logging_bucket_name:
            if using_external_logging_bucket:
                Bucket.deploy_access(construct_id='app-logging-bucket', scope=self,
                                     bucket_name=s3_logging_bucket_name)

            else:
                self.logging_bucket = Bucket(
                    bucket_name=s3_logging_bucket_name,
                    construct_id='app-logging-bucket',
                    object_expiration_days=s3_logging_bucket_object_retention_days,
                    scope=self,
                    use_specified_bucket_name=True,
                )

        if root_domain_name:
            if global_settings_enabled:
                GlobalSetting(
                    description='The root domain for the application. Managed for deployment process only!',
                    namespace='da_vinci_framework::core',
                    setting_key='root_domain_name',
                    setting_value=root_domain_name,
                    scope=self,
                )

            if create_hosted_zone:
                self.root_domain = PublicDomain(
                    app_name=app_name,
                    deployment_id=deployment_id,
                    domain_name=root_domain_name,
                    scope=self,
                )


class Application:
    def __init__(self, app_name: str, deployment_id: str,
                 app_entry: Optional[str] = None, app_image_use_lib_base: Optional[bool] = True,
                 architecture: Optional[str] = cdk_lambda.Architecture.ARM_64,
                 create_hosted_zone: Optional[bool] = False,
                 disable_docker_image_cache: Optional[bool] = DA_VINCI_DISABLE_DOCKER_CACHE,
                 enable_exception_trap: Optional[bool] = True, enable_global_settings: Optional[bool] = True,
                 enable_logging_bucket: Optional[bool] = False, existing_s3_logging_bucket_name: Optional[str] = None,
                 include_event_bus: Optional[bool] = False, log_level: Optional[str] = 'INFO',
                 root_domain_name: Optional[str] = None, s3_logging_bucket_name_postfix: Optional[str] = None,
                 s3_logging_bucket_name_prefix: Optional[str] = None,
                 s3_logging_bucket_object_retention_days: Optional[int] = None):
        """
        Initialize a new Application object

        S3 Logging Bucket Note:
            When using an existing S3 logging bucket, the framework will deploy access for itself but it will not manage the bucket
            or its lifecycle. This is useful for when the bucket is managed by another process or team.

        Keyword Arguments:
            app_entry: Path to the application entry point (default: None)
            app_image_use_lib_base: Use the library base image for the application (default: True)
            app_name: Name of the application
            create_hosted_zone: Whether to create a hosted zone for the application if the root_domain_name is set (default: True)
            deployment_id: Identifier assigned to the installation
            enable_exception_trap: Whether to enable the exception trap (default: True)
            enable_global_settings: Whether to build the global settings stack as part of the application (default: True)
            enable_logging_bucket: Whether to enable the logging bucket (default: False)
            existing_s3_logging_bucket_name: Name of an existing S3 bucket to use for logging (default: None)
            include_event_bus: Whether to build the event bus stack as part of the application (default: False)
            log_level: Logging level to use for the application (default: INFO)
            root_domain_name: Root domain name for the application (default: None)
            s3_logging_bucket_name_postfix: Postfix name of the S3 bucket to use for logging, appends the deployment_id (default: None)
            s3_logging_bucket_name_prefix: Prefix name of the S3 bucket to use for logging, appends the deployment_id (default: None)

        Example:
            ```
            from os.path import dirname, abspath

            from da_vinci_cdk.application import Application

            app = Application(
                app_name='da_vinci',
                deployment_id='test',
                app_entry=abspath(dirname(__file__))),
            )

            app.synth()
            ```
        """
        self.app_entry = app_entry

        self.app_name = app_name

        self.architecture = architecture

        self.deployment_id = deployment_id

        self.log_level = log_level

        self.global_settings_enabled = enable_global_settings

        self.root_domain_name = root_domain_name

        self.lib_docker_image = DockerImage.from_build(
            cache_disabled=disable_docker_image_cache,
            path=self.lib_container_entry,
        )

        if app_entry:
            if app_image_use_lib_base:
                app_entry_build_args = {
                    'IMAGE': self.lib_docker_image.image,
                }
            else:
                app_entry_build_args = {}

            self.app_docker_image = DockerImage.from_build(
                build_args=app_entry_build_args,
                cache_disabled=disable_docker_image_cache,
                path=realpath(app_entry),
            )
        else:
            self.app_docker_image = None

        self._stacks = {}

        external_logging_bucket = False

        if enable_logging_bucket:
            if existing_s3_logging_bucket_name:
                external_logging_bucket = True

                if s3_logging_bucket_name_prefix:
                    raise ValueError('Both existing_s3_logging_bucket_name and s3_logging_bucket_name_prefix cannot be set')

                s3_logging_bucket_name = existing_s3_logging_bucket_name

            else:
                prefix = s3_logging_bucket_name_prefix or ''

                postfix = s3_logging_bucket_name_postfix or ''

            s3_logging_bucket_name = f'{prefix}{app_name}-{deployment_id}{postfix}'

        else:
            s3_logging_bucket_name = None

        context = {
            'app_name': self.app_name,
            'architecture': self.architecture,
            'deployment_id': self.deployment_id,
            'global_settings_enabled': self.global_settings_enabled,
            's3_logging_bucket_name': s3_logging_bucket_name,
            'exception_trap_enabled': enable_exception_trap,
            'log_level': self.log_level,
            'root_domain_name': self.root_domain_name,
        }

        self.cdk_app = CDKApp(context=context)

        self.dependency_stacks = []

        if enable_global_settings:
            global_settings_stack = self.add_uninitialized_stack(
                stack=GlobalSettingsStack,
                include_core_dependencies=False,
            )

            self.dependency_stacks.append(global_settings_stack)

        self.core_stack = CoreStack(
            app_name=self.app_name,
            create_hosted_zone=create_hosted_zone,
            deployment_id=self.deployment_id,
            global_settings_enabled=self.global_settings_enabled,
            scope=self.cdk_app,
            stack_name=self.generate_stack_name(CoreStack),
            root_domain_name=self.root_domain_name,
            using_external_logging_bucket=external_logging_bucket,
            s3_logging_bucket_name=s3_logging_bucket_name,
            s3_logging_bucket_object_retention_days=s3_logging_bucket_object_retention_days,
        )

        self.dependency_stacks.append(self.core_stack)

        if enable_exception_trap:
            exceptions_trap_stack = self.add_uninitialized_stack(
                stack=ExceptionsTrapStack,
                include_core_dependencies=False,
            )

            self.dependency_stacks.append(exceptions_trap_stack)

        if include_event_bus:
            self.add_uninitialized_stack(EventBusStack)

    @staticmethod
    def generate_stack_name(stack: Stack) -> str:
        """
        Generate a stack name

        Keyword Arguments:
            stack: Stack to generate the name for
        """

        return stack.__name__.lower()

    @property
    def lib_container_entry(self) -> str:
        '''
        Return the entry point for this library's container image
        '''

        # DaVinci library should be installed by poetry as a dev dependency
        # this allows for the ability to build the container image located
        # in the library's root directory
        import da_vinci

        da_vinci_spec = da_vinci.__spec__
        da_vinci_lib_path = da_vinci_spec.submodule_search_locations[0]

        return realpath(path_join(da_vinci_lib_path, '../'))

    def add_uninitialized_stack(self, stack: Stack,
                                include_core_dependencies: Optional[bool] = True) -> Stack:
        """
        Add a new unintialized stack to the application. This is useful for
        adding stacks that take standard parameters.

        Keyword Arguments:
            stack: Stack to add to the application
        """
        stack_name = self.generate_stack_name(stack)

        if stack_name in self._stacks:
            return self._stacks[stack_name]

        init_args = {
            'architecture': self.architecture,
            'app_name': self.app_name,
            'library_base_image': self.lib_docker_image.image,
            'deployment_id': self.deployment_id,
            'scope': self.cdk_app,
            'stack_name': stack_name,
        }

        if self.app_docker_image:
            init_args['app_base_image'] = self.app_docker_image.image
        else:
            init_args['app_base_image'] = None

        req_init_vars = stack.__init__.__code__.co_varnames

        stk_req_init_vars = set(req_init_vars)
        stk_avail_init_vars = set(init_args.keys())

        stk_args = stk_avail_init_vars.difference(stk_req_init_vars)

        for arg in stk_args:
            del init_args[arg]

        self._stacks[stack_name] = stack(**init_args)

        if include_core_dependencies:
            for dependency in self.dependency_stacks:
                self._stacks[stack_name].add_dependency(dependency)

        for dependency in self._stacks[stack_name].required_stacks:

            dependency_stack_name = self.generate_stack_name(dependency)

            if dependency_stack_name not in self._stacks:
                self.add_uninitialized_stack(dependency)

            self._stacks[stack_name].add_dependency(
                self._stacks[dependency_stack_name]
            )

        return self._stacks[stack_name]

    def synth(self, **kwargs):
        """
        Synthesize the CDK application
        """

        self.cdk_app.synth(**kwargs)
