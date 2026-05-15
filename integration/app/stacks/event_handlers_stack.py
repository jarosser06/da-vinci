"""Event bus subscription functions exercised by the integration suite."""

from aws_cdk import Duration
from constructs import Construct
from handlers.shared.person import PersonTableObject
from stacks.orm_stack import OrmStack

from da_vinci_cdk.constructs.access_management import ResourceAccessRequest
from da_vinci_cdk.constructs.event_bus import EventBusSubscriptionFunction
from da_vinci_cdk.stack import Stack


class EventHandlersStack(Stack):
    """Four event-bus subscribers covering success, failure, and callback chaining."""

    def __init__(
        self,
        app_name: str,
        architecture: str,
        deployment_id: str,
        scope: Construct,
        stack_name: str,
        app_base_image: str | None = None,
        library_base_image: str | None = None,
    ) -> None:
        super().__init__(
            app_name=app_name,
            architecture=architecture,
            deployment_id=deployment_id,
            scope=scope,
            stack_name=stack_name,
            app_base_image=app_base_image,
            library_base_image=library_base_image,
            required_stacks=[OrmStack],
            requires_event_bus=True,
            requires_exceptions_trap=True,
        )

        handler_dir = self.absolute_dir(__file__).rsplit("/stacks", 1)[0]

        self.successful = EventBusSubscriptionFunction(
            construct_id="it_successful",
            event_type="it.echo",
            function_name=f"{app_name}-{deployment_id}-successful_handler",
            scope=self,
            base_image=app_base_image,
            entry=handler_dir,
            index="handlers/successful_handler.py",
            handler="handler",
            timeout=Duration.seconds(30),
            active=True,
        )

        self.failing = EventBusSubscriptionFunction(
            construct_id="it_failing",
            event_type="it.boom",
            function_name=f"{app_name}-{deployment_id}-failing_handler",
            scope=self,
            base_image=app_base_image,
            entry=handler_dir,
            index="handlers/failing_handler.py",
            handler="handler",
            timeout=Duration.seconds(30),
            active=True,
        )

        self.chain_first = EventBusSubscriptionFunction(
            construct_id="it_chain_first",
            event_type="it.chain.start",
            function_name=f"{app_name}-{deployment_id}-chain_first",
            scope=self,
            base_image=app_base_image,
            entry=handler_dir,
            index="handlers/chain_first.py",
            handler="handler",
            timeout=Duration.seconds(30),
            generates_events=["it.chain.end"],
            active=True,
        )

        self.chain_second = EventBusSubscriptionFunction(
            construct_id="it_chain_second",
            event_type="it.chain.end",
            function_name=f"{app_name}-{deployment_id}-chain_second",
            scope=self,
            base_image=app_base_image,
            entry=handler_dir,
            index="handlers/chain_second.py",
            handler="handler",
            timeout=Duration.seconds(30),
            resource_access_requests=[
                ResourceAccessRequest(
                    resource_name=PersonTableObject.table_name,
                    resource_type="table",
                    policy_name="read_write",
                ),
            ],
            active=True,
        )
