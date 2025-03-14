from enum import StrEnum
from aws_cdk import aws_bedrock as bedrock
from aws_cdk import Aws
from constructs import Construct

from da_vinci.core.resource_discovery import ResourceType

from da_vinci_cdk.constructs.resource_discovery import DiscoverableResource
from da_vinci_cdk.constructs.base import apply_framework_tags, resource_namer

class ModelType(StrEnum):
    """
    Supported model types for the AIInferenceProfile construct
    """
    FOUNDATION_MODEL = 'foundation-model'
    INFERENCE_PROFILE = 'inference-profile'

class AIInferenceProfile(Construct):
    def __init__(self, scope: Construct, profile_name: str, model_id: str, model_type: ModelType = ModelType.FOUNDATION_MODEL):
        """
        Initialize an AIInferenceProfile construct

        Keyword Arguments:
            scope -- Parent construct for the stack
            profile_name -- Name of the profile to be created
            model_id -- Model to use as base for the inference profile
            model_type -- Type of model to use as base for the inference profile (default: ModelType.FOUNDATION_MODEL)
        """
        construct_id = f'{profile_name.replace(':', '').replace('-', '').replace('.', '').replace(' ', '')}_inference_profile_construct'

        super().__init__(scope, construct_id)

        self.inference_profile = bedrock.CfnApplicationInferenceProfile(
            scope=self,
            id=f'application_inference_profile',
            inference_profile_name=resource_namer(name=profile_name, scope=self),
            model_source=bedrock.CfnApplicationInferenceProfile.InferenceProfileModelSourceProperty(
                copy_from=f"arn:aws:bedrock:{Aws.REGION}:{Aws.ACCOUNT_ID}:{model_type.value}/{model_id}"
            )
        )

        apply_framework_tags(resource=self.inference_profile, scope=self)

        self.discovery_resource = DiscoverableResource(
            construct_id='discovery-resource',
            scope=self,
            resource_endpoint=self.inference_profile.attr_inference_profile_arn,
            resource_name=model_id,
            resource_type=ResourceType.LLM,
        )