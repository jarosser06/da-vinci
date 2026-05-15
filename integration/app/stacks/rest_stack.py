"""SimpleRESTService stack used to validate REST + ORM + GlobalSettings paths."""

from aws_cdk import Duration
from constructs import Construct
from handlers.shared.person import PersonTableObject
from stacks.orm_stack import OrmStack
from stacks.settings_stack import SettingsStack

from da_vinci_cdk.constructs.access_management import ResourceAccessRequest
from da_vinci_cdk.constructs.service import SimpleRESTService
from da_vinci_cdk.stack import Stack


class RestStack(Stack):
    """SimpleRESTService exposing CRUD over PersonTable and a settings round-trip route."""

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
            required_stacks=[OrmStack, SettingsStack],
            # LambdaFunction auto-injects an ``exceptions_trap`` access
            # request whenever exception_trap_enabled is True. That access
            # policy is published to SSM by ``ExceptionsTrapStack``, so we
            # must declare the stack-level dependency or the ``{{resolve:ssm:
            # ...}}`` lookup fails at change-set creation on first deploy.
            requires_exceptions_trap=True,
        )

        handler_dir = self.absolute_dir(__file__).rsplit("/stacks", 1)[0]

        self.rest = SimpleRESTService(
            base_image=app_base_image,
            description="Integration test REST service over PersonTable.",
            entry=handler_dir,
            handler="handler",
            index="handlers/rest_handler.py",
            resource_access_requests=[
                ResourceAccessRequest(
                    resource_name=PersonTableObject.table_name,
                    resource_type="table",
                    policy_name="read_write",
                ),
            ],
            scope=self,
            service_name="it_people",
            timeout=Duration.seconds(30),
        )
