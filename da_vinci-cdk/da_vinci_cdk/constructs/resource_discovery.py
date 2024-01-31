from typing import Optional

from constructs import Construct

from da_vinci.core.resource_discovery import resource_parameter

from da_vinci_cdk.constructs.base import GlobalVariable


class DiscoverableResource(Construct):
    def __init__(self, construct_id: str, scope: Construct, resource_endpoint: str,
                 resource_name: str, resource_type: str, app_name: Optional[str] = None,
                 deployment_id: Optional[str] = None):
        """
        Initialize a DiscoverableResource object to 

        ServiceDiscovery is a wrapper around a service discovery resource that
        provisions a resource utilizing the core service discovery pattern.

        Keyword Arguments:
            construct_id: Identifier for the construct
            scope: Parent construct for the ServiceDiscovery
            app_name: Name of the application
            deployment_id: Unique identifier for the installation
            resource_name: Name of the resource
            resource_type: Type of the resource
        """

        super().__init__(scope, construct_id)

        self.app_name = app_name or scope.node.get_context('app_name')
        self.deployment_id = deployment_id or scope.node.get_context('deployment_id')

        self.resource_endpoint = resource_endpoint
        self.resource_name = resource_name
        self.resource_type = resource_type

        ssm_key = self._gen_parameter_name(
            app_name=self.app_name,
            deployment_id=self.deployment_id,
            resource_name=self.resource_name,
            resource_type=self.resource_type,
        )

        self.parameter = GlobalVariable(
            construct_id=f'service-discovery-ssm-parameter-{self.resource_name}',
            scope=self,
            ssm_key=ssm_key,
            ssm_value=self.resource_endpoint,
        )

    @staticmethod
    def _gen_parameter_name(app_name: str, deployment_id: str, resource_name: str,
                            resource_type: str) -> str:
        """
        Generate a resource name for a service discovery resource

        Keyword Arguments:
            app_name: Name of the application
            deployment_id: Unique identifier for the installation
            resource_name: Name of the resource
            resource_type: Type of the resource
        """

        return resource_parameter(
            app_name=app_name,
            deployment_id=deployment_id,
            resource_name=resource_name,
            resource_type=resource_type,
        )

    @classmethod
    def read_endpoint(cls, resource_name: str, resource_type: str, scope: Construct,
                      app_name: Optional[str] = None, deployment_id: Optional[str] = None) -> str:
        """
        Read the endpoint for a service discovery resource

        Keyword Arguments:
            resource_name: Name of the resource
            resource_type: Type of the resource
            app_name: Name of the application
            deployment_id: Unique identifier for the installation
            scope: Parent construct for the ServiceDiscovery.
        """

        lookup_args = {'resource_name': resource_name, 'resource_type': resource_type}

        lookup_args['app_name'] = app_name or scope.node.get_context('app_name')
        lookup_args['deployment_id'] = deployment_id or scope.node.get_context('deployment_id')

        for arg_name, arg_value in lookup_args.items():
            if not arg_value:
                raise ValueError(f'{arg_name} must not be None')

        ssm_key = cls._gen_parameter_name(**lookup_args)

        endpoint = GlobalVariable.load_variable(
            scope=scope,
            ssm_key=ssm_key,
        )

        return endpoint