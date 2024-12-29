from constructs import Construct

from da_vinci.core.tables.global_settings import (
    GlobalSetting,
)

from da_vinci_cdk.stack import Stack
from da_vinci_cdk.constructs.dynamodb import DynamoDBTable


class GlobalSettingsTableStack(Stack):
    """
    CDK Stack that provisions a Global Settings DynamoDB Table
    """
    def __init__(self, app_name: str, deployment_id: str, scope: Construct, stack_name: str):
        super().__init__(
            app_name=app_name,
            deployment_id=deployment_id,
            scope=scope,
            stack_name=stack_name,
        )

        self.table = DynamoDBTable.from_orm_table_object(
            table_object=GlobalSetting,
            scope=self,
        )