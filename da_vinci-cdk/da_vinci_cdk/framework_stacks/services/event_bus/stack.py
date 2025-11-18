import os

from aws_cdk import DockerImage, Duration
from aws_cdk import aws_iam as cdk_iam
from aws_cdk.aws_lambda import RecursiveLoop
from constructs import Construct

from da_vinci_cdk.constructs.access_management import (
    ResourceAccessRequest,
)
from da_vinci_cdk.constructs.global_setting import GlobalSetting, GlobalSettingType
from da_vinci_cdk.constructs.service import AsyncService, SimpleRESTService
from da_vinci_cdk.framework_stacks.services.exceptions_trap.stack import ExceptionsTrapStack
from da_vinci_cdk.framework_stacks.tables.event_bus_responses.stack import (
    EventBusResponsesTableStack,
)
from da_vinci_cdk.framework_stacks.tables.event_bus_subscriptions.stack import (
    EventBusSubscriptionsTableStack,
)
from da_vinci_cdk.stack import Stack


class EventBusStack(Stack):
    def __init__(
        self,
        app_name: str,
        architecture: str,
        deployment_id: str,
        scope: Construct,
        stack_name: str,
        library_base_image: DockerImage,
    ) -> None:
        """
        Initialize a new EventBusStack object

        Keyword Arguments:
            app_name -- Name of the application
            architecture -- Architecture to use for the stack
            deployment_id -- Identifier assigned to the installation
            scope -- Parent construct for the stack
            stack_name -- Name of the stack
            library_base_image -- Base image built for the library
        """

        base_dir = self.absolute_dir(__file__)

        self.runtime_path = os.path.join(base_dir, "runtime")

        super().__init__(
            app_name=app_name,
            architecture=architecture,
            deployment_id=deployment_id,
            scope=scope,
            stack_name=stack_name,
            library_base_image=library_base_image,
            required_stacks=[
                EventBusSubscriptionsTableStack,
                EventBusResponsesTableStack,
                ExceptionsTrapStack,
            ],
        )

        self.bus_service = AsyncService(
            base_image=self.library_base_image,  # type: ignore[arg-type]
            description="Invokes functions with event bodies from the event bus",
            entry=self.runtime_path,
            handler="handler",
            index="bus.py",
            recursive_loop=RecursiveLoop.ALLOW,
            resource_access_requests=[
                ResourceAccessRequest(
                    resource_name="da_vinci_event_bus_subscriptions",
                    resource_type="table",
                    policy_name="read",
                ),
            ],
            scope=self,
            service_name="event_bus",
            timeout=Duration.seconds(30),
        )

        self.bus_service.handler.function.add_to_role_policy(
            cdk_iam.PolicyStatement(
                actions=["lambda:InvokeFunction"],
                conditions={
                    "StringEquals": {
                        "aws:ResourceTag/DaVinciFramework::FunctionPurpose": "EventSubscription"
                    }
                },
                resources=["arn:aws:lambda:*"],
            )
        )

        self.bus_watcher = SimpleRESTService(
            base_image=self.library_base_image,  # type: ignore[arg-type]
            description="Handles responses from functions executed from the event bus",
            entry=self.runtime_path,
            handler="api",
            index="bus_watcher.py",
            resource_access_requests=[
                ResourceAccessRequest(
                    resource_name="da_vinci_event_bus_subscriptions",
                    resource_type="table",
                    policy_name="read",
                ),
                ResourceAccessRequest(
                    resource_name="da_vinci_event_bus_responses",
                    resource_type="table",
                    policy_name="read_write",
                ),
            ],
            scope=self,
            service_name="event_bus_responses",
            timeout=Duration.seconds(30),
        )

        self.bus_watcher.grant_invoke(
            resource=self.bus_service.handler.function,
        )

        self.response_ttl_in_hours = GlobalSetting(
            description="The number of hours to retain responses in the event bus",
            namespace="da_vinci_framework::event_bus",
            setting_key="response_retention_hours",
            setting_type=GlobalSettingType.INTEGER,
            setting_value="8",
            scope=self,
        )
