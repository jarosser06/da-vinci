from constructs import Construct

from da_vinci_cdk.application import Application
from da_vinci_cdk.constructs.dynamodb import DynamoDBTable
from da_vinci_cdk.stack import Stack

from table_client import ExampleTableClient


class ExampleTableStack(Stack):
    def __init__(self, app_name: str, deployment_id: str,
                 scope: Construct, stack_name: str):
        super().__init__(
            app_name=app_name,
            deployment_id=deployment_id,
            scope=scope,
            stack_name=stack_name
        )

        self.table = DynamoDBTable.from_orm_table_object(
            scope=self,
            table_object=ExampleTableClient,
        )

base_dir = Stack.absolute_dir(__file__)

app = Application(
    app_name="base_orm_example",
    create_hosted_zone=False,
    deployment_id="example",
)

app.add_uninitialized_stack(ExampleTableStack)

app.synth()