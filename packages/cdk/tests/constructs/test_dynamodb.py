"""Unit tests for da_vinci_cdk.constructs.dynamodb module."""

from unittest.mock import patch

from aws_cdk import App, RemovalPolicy, Stack
from aws_cdk.assertions import Match, Template
from aws_cdk.aws_dynamodb import Attribute, AttributeType
from aws_cdk.aws_iam import Role, ServicePrincipal

from da_vinci.core.orm.table_object import TableObjectAttributeType
from da_vinci.core.resource_discovery import ResourceDiscoveryStorageSolution
from da_vinci.core.tables.resource_registry import ResourceRegistration
from da_vinci_cdk.constructs.dynamodb import DynamoDBTable


class TestDynamoDBTable:
    """Tests for DynamoDBTable construct."""

    def test_table_creation_basic(self, stack):
        """A basic table synthesizes one on-demand GlobalTable with the
        namespaced table name, a single string HASH key, and the framework
        management tags on its replica."""
        DynamoDBTable(
            scope=stack,
            table_name="test-table",
            partition_key=Attribute(name="id", type=AttributeType.STRING),
        )

        template = Template.from_stack(stack)
        template.resource_count_is("AWS::DynamoDB::GlobalTable", 1)
        template.has_resource_properties(
            "AWS::DynamoDB::GlobalTable",
            {
                "TableName": "test-app-test-deployment-test-table",
                "BillingMode": "PAY_PER_REQUEST",
                "KeySchema": [{"AttributeName": "id", "KeyType": "HASH"}],
                "AttributeDefinitions": [{"AttributeName": "id", "AttributeType": "S"}],
                "Replicas": Match.array_with(
                    [
                        Match.object_like(
                            {
                                "Tags": Match.array_with(
                                    [
                                        {
                                            "Key": "DaVinciFramework::ApplicationName",
                                            "Value": "test-app",
                                        },
                                        {
                                            "Key": "DaVinciFramework::DeploymentId",
                                            "Value": "test-deployment",
                                        },
                                        {
                                            "Key": "DaVinciFrameworkManaged",
                                            "Value": "True",
                                        },
                                    ]
                                )
                            }
                        )
                    ]
                ),
            },
        )

    def test_table_with_sort_key(self, stack):
        """A table with a sort key emits both HASH and RANGE key entries plus
        matching attribute definitions in the correct order."""
        DynamoDBTable(
            scope=stack,
            table_name="test-table",
            partition_key=Attribute(name="pk", type=AttributeType.STRING),
            sort_key=Attribute(name="sk", type=AttributeType.NUMBER),
        )

        template = Template.from_stack(stack)
        template.has_resource_properties(
            "AWS::DynamoDB::GlobalTable",
            {
                "KeySchema": [
                    {"AttributeName": "pk", "KeyType": "HASH"},
                    {"AttributeName": "sk", "KeyType": "RANGE"},
                ],
                "AttributeDefinitions": [
                    {"AttributeName": "pk", "AttributeType": "S"},
                    {"AttributeName": "sk", "AttributeType": "N"},
                ],
            },
        )

    def test_table_billing_mode_is_on_demand(self, stack):
        """The construct hardcodes on-demand billing regardless of caller."""
        DynamoDBTable(
            scope=stack,
            table_name="test-table",
            partition_key=Attribute(name="id", type=AttributeType.STRING),
        )

        template = Template.from_stack(stack)
        template.has_resource_properties(
            "AWS::DynamoDB::GlobalTable", {"BillingMode": "PAY_PER_REQUEST"}
        )

    def test_table_default_removal_policy_retains(self, stack):
        """With no removal policy supplied, the GlobalTable retains on delete
        and replace."""
        DynamoDBTable(
            scope=stack,
            table_name="test-table",
            partition_key=Attribute(name="id", type=AttributeType.STRING),
        )

        template = Template.from_stack(stack)
        template.has_resource(
            "AWS::DynamoDB::GlobalTable",
            {"DeletionPolicy": "Retain", "UpdateReplacePolicy": "Retain"},
        )

    def test_table_removal_policy_destroy(self, stack):
        """RemovalPolicy.DESTROY produces Delete deletion/replace policies."""
        DynamoDBTable(
            scope=stack,
            table_name="test-table",
            partition_key=Attribute(name="id", type=AttributeType.STRING),
            removal_policy=RemovalPolicy.DESTROY,
        )

        template = Template.from_stack(stack)
        template.has_resource(
            "AWS::DynamoDB::GlobalTable",
            {"DeletionPolicy": "Delete", "UpdateReplacePolicy": "Delete"},
        )

    def test_table_with_time_to_live(self, stack):
        """A TTL attribute enables a TimeToLiveSpecification on the table."""
        DynamoDBTable(
            scope=stack,
            table_name="test-table",
            partition_key=Attribute(name="id", type=AttributeType.STRING),
            time_to_live_attribute="ttl",
        )

        template = Template.from_stack(stack)
        template.has_resource_properties(
            "AWS::DynamoDB::GlobalTable",
            {"TimeToLiveSpecification": {"AttributeName": "ttl", "Enabled": True}},
        )

    def test_table_without_ttl_has_no_ttl_specification(self, stack):
        """Without a TTL attribute no TimeToLiveSpecification is emitted."""
        DynamoDBTable(
            scope=stack,
            table_name="test-table",
            partition_key=Attribute(name="id", type=AttributeType.STRING),
        )

        template = Template.from_stack(stack)
        template.has_resource_properties(
            "AWS::DynamoDB::GlobalTable",
            Match.not_({"TimeToLiveSpecification": Match.any_value()}),
        )

    def test_table_registers_discovery_resource_by_default(self, stack):
        """A discoverable table publishes its endpoint and access policies via
        SSM parameters and managed policies."""
        DynamoDBTable(
            scope=stack,
            table_name="test-table",
            partition_key=Attribute(name="id", type=AttributeType.STRING),
        )

        template = Template.from_stack(stack)
        # Discovery parameters + the read/default/read_write managed policies.
        template.resource_count_is("AWS::SSM::Parameter", 4)
        template.resource_count_is("AWS::IAM::ManagedPolicy", 3)

    def test_table_excluded_from_discovery_emits_fewer_resources(self, stack):
        """Excluding a table from discovery still creates the access managed
        policies but omits the discovery access statement's SSM parameter."""
        DynamoDBTable(
            scope=stack,
            table_name="test-table",
            partition_key=Attribute(name="id", type=AttributeType.STRING),
            exclude_from_discovery=True,
        )

        template = Template.from_stack(stack)
        template.resource_count_is("AWS::DynamoDB::GlobalTable", 1)
        # A discoverable table publishes 4 SSM params; excluding it from
        # discovery drops the endpoint parameter, leaving 3.
        template.resource_count_is("AWS::SSM::Parameter", 3)

    def test_grant_read_access_attaches_read_only_actions(self, stack):
        """grant_read_access attaches an IAM policy carrying the read-only
        DynamoDB actions (and no write actions) to the grantee role."""
        role = Role(stack, "TestRole", assumed_by=ServicePrincipal("lambda.amazonaws.com"))

        table = DynamoDBTable(
            scope=stack,
            table_name="test-table",
            partition_key=Attribute(name="id", type=AttributeType.STRING),
        )
        table.grant_read_access(role)

        template = Template.from_stack(stack)
        template.has_resource_properties(
            "AWS::IAM::Policy",
            {
                "PolicyDocument": {
                    "Statement": Match.array_with(
                        [
                            Match.object_like(
                                {
                                    "Action": Match.array_with(
                                        [
                                            "dynamodb:BatchGetItem",
                                            "dynamodb:Query",
                                            "dynamodb:GetItem",
                                            "dynamodb:Scan",
                                        ]
                                    ),
                                    "Effect": "Allow",
                                }
                            )
                        ]
                    )
                }
            },
        )
        # The read grant must not include any mutating action.
        read_policy = template.find_resources("AWS::IAM::Policy")
        actions = [
            action
            for policy in read_policy.values()
            for statement in policy["Properties"]["PolicyDocument"]["Statement"]
            for action in (
                statement["Action"]
                if isinstance(statement["Action"], list)
                else [statement["Action"]]
            )
        ]
        assert "dynamodb:PutItem" not in actions
        assert "dynamodb:DeleteItem" not in actions

    def test_grant_read_write_access_attaches_write_actions(self, stack):
        """grant_read_write_access attaches an IAM policy that includes write
        actions such as PutItem and DeleteItem."""
        role = Role(stack, "TestRole", assumed_by=ServicePrincipal("lambda.amazonaws.com"))

        table = DynamoDBTable(
            scope=stack,
            table_name="test-table",
            partition_key=Attribute(name="id", type=AttributeType.STRING),
        )
        table.grant_read_write_access(role)

        template = Template.from_stack(stack)
        template.has_resource_properties(
            "AWS::IAM::Policy",
            {
                "PolicyDocument": {
                    "Statement": Match.array_with(
                        [
                            Match.object_like(
                                {
                                    "Action": Match.array_with(
                                        [
                                            "dynamodb:BatchWriteItem",
                                            "dynamodb:PutItem",
                                            "dynamodb:UpdateItem",
                                            "dynamodb:DeleteItem",
                                        ]
                                    ),
                                    "Effect": "Allow",
                                }
                            )
                        ]
                    )
                }
            },
        )

    def test_attribute_type_from_orm_type(self):
        """ORM string types map to STRING; number and datetime map to NUMBER."""
        assert (
            DynamoDBTable.attribute_type_from_orm_type(TableObjectAttributeType.STRING)
            == AttributeType.STRING
        )
        assert (
            DynamoDBTable.attribute_type_from_orm_type(TableObjectAttributeType.NUMBER)
            == AttributeType.NUMBER
        )
        assert (
            DynamoDBTable.attribute_type_from_orm_type(TableObjectAttributeType.DATETIME)
            == AttributeType.NUMBER
        )

    def test_attribute_type_from_orm_type_unknown_defaults_to_string(self):
        """An unrecognized ORM type falls back to STRING rather than raising."""
        result = DynamoDBTable.attribute_type_from_orm_type("INVALID")
        assert result == AttributeType.STRING

    def test_table_with_custom_construct_id(self, stack):
        """A custom construct id still produces exactly one GlobalTable."""
        DynamoDBTable(
            scope=stack,
            table_name="test-table",
            partition_key=Attribute(name="id", type=AttributeType.STRING),
            construct_id="custom-construct-id",
        )

        template = Template.from_stack(stack)
        template.resource_count_is("AWS::DynamoDB::GlobalTable", 1)

    def test_table_with_extra_tags_merges_with_framework_tags(self, stack):
        """Caller-supplied tags are merged with the mandatory framework tags on
        the table replica."""
        DynamoDBTable(
            scope=stack,
            table_name="test-table",
            partition_key=Attribute(name="id", type=AttributeType.STRING),
            tags=[{"key": "Environment", "value": "Test"}],
        )

        template = Template.from_stack(stack)
        template.has_resource_properties(
            "AWS::DynamoDB::GlobalTable",
            {
                "Replicas": Match.array_with(
                    [
                        Match.object_like(
                            {
                                "Tags": Match.array_with(
                                    [
                                        {"Key": "Environment", "Value": "Test"},
                                        {
                                            "Key": "DaVinciFrameworkManaged",
                                            "Value": "True",
                                        },
                                    ]
                                )
                            }
                        )
                    ]
                )
            },
        )

    def test_table_from_orm_table_object(self, stack):
        """from_orm_table_object derives key schema from the TableObject's
        partition/sort attributes."""
        table = DynamoDBTable.from_orm_table_object(
            scope=stack,
            table_object=ResourceRegistration,
        )

        assert table.table is not None
        template = Template.from_stack(stack)
        template.resource_count_is("AWS::DynamoDB::GlobalTable", 1)

    def test_table_full_name_lookup_with_ssm(self, stack):
        """SSM lookup delegates to DiscoverableResource.read_endpoint and
        returns the resolved endpoint value."""
        with patch(
            "da_vinci_cdk.constructs.dynamodb.DiscoverableResource.read_endpoint"
        ) as mock_read:
            mock_read.return_value = "test-table-name"

            name = DynamoDBTable.table_full_name_lookup(
                scope=stack,
                table_name="test-table",
                resource_discovery_storage_solution=(ResourceDiscoveryStorageSolution.SSM),
            )

            assert name == "test-table-name"
            mock_read.assert_called_once()

    def test_table_full_name_lookup_with_dynamodb(self):
        """DynamoDB-backed lookup returns a resolvable token for the name."""
        app = App(
            context={
                "app_name": "test-app",
                "deployment_id": "test-deployment",
                "resource_discovery_storage_solution": (ResourceDiscoveryStorageSolution.DYNAMODB),
                "resource_discovery_table_name": "resource-registry",
            }
        )
        test_stack = Stack(app, "TestStack")

        name = DynamoDBTable.table_full_name_lookup(
            scope=test_stack,
            table_name="test-table",
            resource_discovery_storage_solution=(ResourceDiscoveryStorageSolution.DYNAMODB),
        )

        assert name is not None
