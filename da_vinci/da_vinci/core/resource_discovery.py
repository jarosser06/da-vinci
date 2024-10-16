'''Resource Discovery Module'''
import logging
import time
from enum import StrEnum
from typing import Optional, Union

import boto3

from da_vinci.core.execution_environment import (
    APP_NAME_ENV_NAME,
    DEPLOYMENT_ID_ENV_NAME,
    load_runtime_environment_variables
)
from da_vinci.core.exceptions import ResourceNotFoundError

SERVICE_DISCOVERY_PREFIX = '/da_vinci_framework/service_discovery'

# Cache setup
cache = {}

CACHE_TTL = 300  # Cache Time-to-Live in seconds (5 minutes)

cache_timestamps = {}


class ResourceType(StrEnum):
    '''Resource types registered with service discovery'''
    ASYNC_SERVICE = 'async_service'
    BUCKET = 'bucket'
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

    # Check if the parameter is cached
    current_time = time.time()

    if param_name in cache and (current_time - cache_timestamps[param_name] < CACHE_TTL):
        logging.info(f"Cache hit for resource: {resource_name} of type {resource_type}")

        return cache[param_name]

    logging.info(f"Cache miss for resource: {resource_name} of type {resource_type}")

    ssm = boto3.client('ssm')

    try:
        results = ssm.get_parameter(Name=param_name)

        # Cache the result
        cache[param_name] = results['Parameter']['Value']

        cache_timestamps[param_name] = current_time

        logging.info(f"Resource {resource_name} of type {resource_type} fetched from SSM and cached.")

        return results['Parameter']['Value']

    except ssm.exceptions.ParameterNotFound:
        logging.error(f"Resource {resource_name} of type {resource_type} not found in SSM.")

        raise ResourceNotFoundError(resource_name=resource_name, resource_type=resource_type)

    except Exception as e:
        logging.exception(f"An error occurred while fetching resource {resource_name} of type {resource_type}: {e}")

        raise


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