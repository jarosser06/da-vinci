import os

from constructs import Construct

from aws_cdk import DockerImage, Duration

from da_vinci.core.tables.global_settings import (
    GlobalSetting as GlobalSettingTblObj,
    GlobalSettingType,
)
from da_vinci.exception_trap.tables.trapped_exceptions import TrappedException

from da_vinci_cdk.constructs.access_management import ResourceAccessRequest
from da_vinci_cdk.constructs.global_setting import GlobalSetting
from da_vinci_cdk.constructs.service import SimpleRESTService
from da_vinci_cdk.stack import Stack

from da_vinci_cdk.framework_stacks.tables.global_settings.stack import GlobalSettingsTableStack
from da_vinci_cdk.framework_stacks.tables.trapped_exceptions.stack import TrappedExceptionsTableStack


class ExceptionsTrapStack(Stack):
    def __init__(self, app_name: str, architecture: str, deployment_id: str, scope: Construct,
                 stack_name: str, library_base_image: DockerImage):
        """
        Initialize a new ExceptionsTrapStack object

        Keyword Arguments:
            app_name -- Name of the application
            architecture -- Architecture to use for the stack
            deployment_id -- Identifier assigned to the installation
            scope -- Parent construct for the stack
            stack_name -- Name of the stack
            library_base_image -- Base image built for the library
        """

        base_dir = self.absolute_dir(__file__)

        self.runtime_path = os.path.join(base_dir, 'runtime')

        super().__init__(
            app_name=app_name,
            architecture=architecture,
            deployment_id=deployment_id,
            scope=scope,
            stack_name=stack_name,
            library_base_image=library_base_image,
            required_stacks=[
                GlobalSettingsTableStack,
                TrappedExceptionsTableStack,
            ],
        )

        self.exception_retention_hours = GlobalSetting(
            description='The number of hours to retain responses in the exceptions trap',
            namespace='da_vinci_framework::exceptions_trap',
            setting_key='exception_retention_hours',
            setting_type=GlobalSettingType.INTEGER,
            setting_value=48,
            scope=self,
        )

        self.exceptions_trap = SimpleRESTService(
            base_image=self.library_base_image,
            architecture=architecture,
            description='Catches exceptions and stores them in a DynamoDB table',
            disable_framework_access_requests=True,
            entry=self.runtime_path,
            handler='api',
            index='service.py',
            resource_access_requests=[
                ResourceAccessRequest(
                    resource_name=GlobalSettingTblObj.table_name,
                    resource_type='table',
                    policy_name='read',
                ),
                ResourceAccessRequest(
                    resource_name=TrappedException.table_name,
                    resource_type='table',
                    policy_name='read_write',
                ),
            ],
            scope=self,
            service_name='exceptions_trap',
            timeout=Duration.seconds(30),
        )