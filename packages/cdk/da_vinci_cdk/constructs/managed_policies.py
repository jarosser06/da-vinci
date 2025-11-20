import logging

from aws_cdk import aws_iam as cdk_iam
from constructs import Construct


class BedrockAccessManagedPolicy(Construct):
    def __init__(self, construct_id: str, scope: Construct) -> None:
        """
        Creates a managed policy for Bedrock access

        Keyword Arguments:
            construct_id: The ID of the construct
            scope: The parent of the construct
        """
        logging.warning(
            "BedrockAccessManagedPolicy is deprecated. Use AWS Provided Managed Policy instead."
        )

        super().__init__(scope, construct_id)

        policy_statements = [
            cdk_iam.PolicyStatement(
                actions=[
                    "bedrock:ListFoundationModels",
                    "bedrock:GetFoundationModel",
                    "bedrock:InvokeModel",
                    "bedrock:InvokeModelWithResponseStream",
                ],
                resources=["*"],
            )
        ]

        self.managed_policy = cdk_iam.ManagedPolicy(
            scope=self,
            id=f"{construct_id}-bedrock-managed-policy",
            statements=policy_statements,
        )
