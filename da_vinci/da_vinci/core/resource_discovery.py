'''Resource Discovery Module'''
from enum import StrEnum
from typing import Optional, Union

import boto3

from da_vinci.core.execution_environment import (
    APP_NAME_ENV_NAME,
    DEPLOYMENT_ID_ENV_NAME,
    load_runtime_environment_variables
)
from da_vinci.core.exceptions import ResourceNotFoundError

SERVICE_DISCOVERY_PREFIX = '/da_vinci_v1/service_discovery'


class ResourceType(StrEnum):
    '''Resource types registered with service discovery'''
    ASYNC_SERVICE = 'async_service'
    DOMAIN = 'domain'
    REST_SERVICE = 'rest_service'
    TABLE = 'table'


def resource_endpoint_lookup(resource_type: Union[ResourceType, str], resource_name: str,
                             app_name: Optional[str] = None, deployment_id: Optional[str] = None) -> str:
    '''
    Return the endpoint for a resource registered with service discovery. The app_name and deployment_id
    parameters are optional. If not provided, the values will be loaded from the environment.

    Keyword Arguments:
        resource_type: Type of the resource
        resource_name: Name of the resource
        app_name: Name of the application (default: None)
        deployment_id: Unique identifier for the installation (default: None)
    '''

    lookup_values = []
    param_args = {
        'resource_type': resource_type,
        'resource_name': resource_name,
    }

    if app_name:
        param_args['app_name'] = app_name
    else:
        lookup_values.append(APP_NAME_ENV_NAME)

    if deployment_id:
        param_args['deployment_id'] = deployment_id
    else:
        lookup_values.append(DEPLOYMENT_ID_ENV_NAME)

    if lookup_values:
        env_vars = load_runtime_environment_variables(variable_names=lookup_values)
        param_args.update(env_vars)

    param_name = resource_parameter(**param_args)

    ssm = boto3.client('ssm')

    try:
        results = ssm.get_parameter(Name=param_name)

        return results['Parameter']['Value']
    except:
        raise ResourceNotFoundError(resource_name=resource_name, resource_type=resource_type)


def resource_parameter(resource_type: Union[ResourceType, str], resource_name: str,
                       app_name: str, deployment_id: str) -> str:
    '''
    Return the parameter for a resource registered with service discovery. 

    Keyword Arguments:
        resource_type: Type of the resource
        resource_name: Name of the resource
        app_name: Name of the application
        deployment_id: Unique identifier for the installation
    '''

    return '/'.join(
        [
            SERVICE_DISCOVERY_PREFIX,
            app_name,
            deployment_id,
            resource_type,
            resource_name,
        ]
    )