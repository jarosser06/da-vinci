from constructs import Construct

from da_vinci.core.tables.resource_registry import ResourceRegistration

from da_vinci_cdk.stack import Stack
from da_vinci_cdk.constructs.dynamodb import DynamoDBTable


class ResourceRegistrationTableStack(Stack):
    """
    CDK Stack that provisions a Resource Registry DynamoDB Table
    """
    def __init__(self, app_name: str, deployment_id: str, scope: Construct, stack_name: str):
        super().__init__(
            app_name=app_name,
            deployment_id=deployment_id,
            scope=scope,
            stack_name=stack_name,
        )

        self.table = DynamoDBTable.from_orm_table_object(
            # :chicken: & :egg: Can't resource discover the resource registry table
            exclude_from_discovery=True,
            table_object=ResourceRegistration,
            scope=self,
        )