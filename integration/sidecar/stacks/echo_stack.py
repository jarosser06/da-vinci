"""Sidecar stack with an event-bus subscriber reaching parent resources."""

from aws_cdk import Duration
from constructs import Construct
from handlers.shared.person import PersonTableObject

from da_vinci_cdk.constructs.access_management import ResourceAccessRequest
from da_vinci_cdk.constructs.event_bus import EventBusSubscriptionFunction
from da_vinci_cdk.stack import Stack


class SidecarEchoStack(Stack):
    """A single subscriber that uses the parent application's event bus."""

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
        )

        sidecar_app_name = scope.node.get_context("sidecar_app_name")

        handler_dir = self.absolute_dir(__file__).rsplit("/stacks", 1)[0]

        self.echo = EventBusSubscriptionFunction(
            construct_id="sidecar_echo",
            event_type="it.sidecar.ping",
            function_name=f"{app_name}-{sidecar_app_name}-{deployment_id}-sidecar_echo",
            scope=self,
            base_image=app_base_image,
            entry=handler_dir,
            index="handlers/echo.py",
            handler="handler",
            timeout=Duration.seconds(30),
            active=True,
        )

        # Failing subscriber: proves a sidecar exception routes to the PARENT's
        # shared exception trap.
        self.boom = EventBusSubscriptionFunction(
            construct_id="sidecar_boom",
            event_type="it.sidecar.boom",
            function_name=f"{app_name}-{sidecar_app_name}-{deployment_id}-sidecar_boom",
            scope=self,
            base_image=app_base_image,
            entry=handler_dir,
            index="handlers/sidecar_boom.py",
            handler="handler",
            timeout=Duration.seconds(30),
            active=True,
        )

        # Writer subscriber: requests read_write access to the PARENT's
        # ``people`` table and writes a row, proving cross-application resource
        # use via a granted ResourceAccessRequest.
        self.writer = EventBusSubscriptionFunction(
            construct_id="sidecar_writer",
            event_type="it.sidecar.write",
            function_name=f"{app_name}-{sidecar_app_name}-{deployment_id}-sidecar_writer",
            scope=self,
            base_image=app_base_image,
            entry=handler_dir,
            index="handlers/sidecar_writer.py",
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
