"""ORM-backed DynamoDB table stack for the integration test application."""

from aws_cdk import RemovalPolicy
from constructs import Construct
from handlers.shared.person import PersonTableObject

from da_vinci_cdk.constructs.dynamodb import DynamoDBTable
from da_vinci_cdk.stack import Stack


class OrmStack(Stack):
    """Provision the PersonTable used by the chained handler and the REST service."""

    def __init__(
        self,
        app_name: str,
        architecture: str,
        deployment_id: str,
        scope: Construct,
        stack_name: str,
        library_base_image: str | None = None,
    ) -> None:
        super().__init__(
            app_name=app_name,
            architecture=architecture,
            deployment_id=deployment_id,
            scope=scope,
            stack_name=stack_name,
            library_base_image=library_base_image,
        )

        self.table = DynamoDBTable.from_orm_table_object(
            scope=self,
            table_object=PersonTableObject,
            removal_policy=RemovalPolicy.DESTROY,
        )
