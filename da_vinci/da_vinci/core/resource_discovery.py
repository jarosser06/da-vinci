"""Resource Discovery Module"""

import logging
import time
from enum import StrEnum

import boto3

from da_vinci.core.base import standard_aws_resource_name
from da_vinci.core.exceptions import ResourceNotFoundError
from da_vinci.core.execution_environment import (
    APP_NAME_ENV_NAME,
    DEPLOYMENT_ID_ENV_NAME,
    SERVICE_DISC_STOR_ENV_NAME,
    load_runtime_environment_variables,
)
from da_vinci.core.tables.resource_registry import ResourceRegistration


SSM_SERVICE_DISCOVERY_PREFIX = "/da_vinci_framework/service_discovery"

# Cache setup
cache: dict[str, str] = {}

CACHE_TTL = 300  # Cache Time-to-Live in seconds (5 minutes)

cache_timestamps: dict[str, float] = {}


class ResourceType(StrEnum):
    """Resource types registered with service discovery"""

    ASYNC_SERVICE = "async_service"
    BUCKET = "bucket"
    DOMAIN = "domain"
    REST_SERVICE = "rest_service"
    TABLE = "table"


class ResourceDiscoveryStorageSolution(StrEnum):
    """Resource discovery storage solutions"""

    DYNAMODB = "dynamodb"
    SSM = "ssm"


class ResourceDiscovery:
    def __init__(
        self,
        resource_type: ResourceType | str,
        resource_name: str,
        app_name: str | None = None,
        deployment_id: str | None = None,
        storage_solution: ResourceDiscoveryStorageSolution | None = None,
    ) -> None:
        """
        Initialize a ResourceDiscovery object

        Keyword Arguments:
            resource_type: Type of the resource
            resource_name: Name of the resource
            app_name: Name of the application (default: None)
            deployment_id: Unique identifier for the installation (default: None)
        """
        self.app_name = app_name

        self.deployment_id = deployment_id

        self.storage_solution = storage_solution

        lookup_values: list[str] = []

        if not self.app_name:
            lookup_values.append(APP_NAME_ENV_NAME)

        if not self.deployment_id:
            lookup_values.append(DEPLOYMENT_ID_ENV_NAME)

        if not self.storage_solution:
            lookup_values.append(SERVICE_DISC_STOR_ENV_NAME)

        if lookup_values:
            env_vars = load_runtime_environment_variables(variable_names=tuple(lookup_values))  # type: ignore[arg-type]

            if not self.app_name:
                self.app_name = env_vars["app_name"]

            if not self.deployment_id:
                self.deployment_id = env_vars["deployment_id"]

            if not self.storage_solution:
                self.storage_solution = env_vars["resource_discovery_storage"]

        self.resource_type = resource_type

        self.resource_name = resource_name

    @classmethod
    def ssm_parameter_name(
        cls,
        resource_type: ResourceType | str,
        resource_name: str,
        app_name: str,
        deployment_id: str,
    ) -> str:
        """
        Return the parameter for a resource registered with service discovery.

        Keyword Arguments:
            resource_type: Type of the resource
            resource_name: Name of the resource
            app_name: Name of the application
            deployment_id: Unique identifier for the installation
        """

        return "/".join(
            [
                SSM_SERVICE_DISCOVERY_PREFIX,
                app_name,
                deployment_id,
                resource_type,
                resource_name,
            ]
        )

    def endpoint_lookup(self) -> str:
        """
        Return the endpoint for a resource registered with service discovery.
        """
        logging.info(f"Endpoint lookup using storage solution: {self.storage_solution}")

        if self.storage_solution == ResourceDiscoveryStorageSolution.DYNAMODB:
            return self.service_registry_table_lookup()

        return self.ssm_resource_endpoint_lookup()

    def service_registry_table_lookup(self) -> str:
        """
        Return the endpoint for a resource registered with service discovery using the service registry table.
        """
        resource_registration = ResourceRegistration(
            endpoint="PLACEHOLDER",
            resource_type=self.resource_type,
            resource_name=self.resource_name,
        )

        # Create cache key using just the unique identifiers of the resource
        cache_key = f"dynamodb:{self.resource_type}:{self.resource_name}"

        # Check if the result is cached
        current_time = time.time()

        if cache_key in cache and (current_time - cache_timestamps[cache_key] < CACHE_TTL):
            logging.info(
                f"Cache hit for resource: {self.resource_name} of type {self.resource_type} in DynamoDB"
            )

            return cache[cache_key]

        logging.info(
            f"Cache miss for resource: {self.resource_name} of type {self.resource_type} in DynamoDB"
        )

        if self.app_name is None or self.deployment_id is None:
            raise ValueError("app_name and deployment_id must be set for DynamoDB lookup")

        # Determine table name using the same convention as in the ORM
        table_name = standard_aws_resource_name(
            app_name=self.app_name,
            deployment_id=self.deployment_id,
            name=ResourceRegistration.table_name,
        )

        logging.info(f"Using DynamoDB table: {table_name} for resource discovery")

        # Create direct DynamoDB client
        dynamodb = boto3.client("dynamodb")

        try:
            # Query using simple dict format for get_item
            response = dynamodb.get_item(
                TableName=table_name,
                Key=resource_registration.gen_dynamodb_key(
                    partition_key_value=self.resource_type,
                    sort_key_value=self.resource_name,
                ),
            )

            # Check if the item was found
            if "Item" in response and "Endpoint" in response["Item"]:
                endpoint = response["Item"]["Endpoint"]["S"]

                # Cache the result
                cache[cache_key] = endpoint

                cache_timestamps[cache_key] = current_time

                logging.info(
                    f"Resource {self.resource_name} of type {self.resource_type} fetched from DynamoDB and cached."
                )

                return endpoint

            else:
                logging.error(
                    f"Resource {self.resource_name} of type {self.resource_type} not found in DynamoDB."
                )

                raise ResourceNotFoundError(
                    resource_name=self.resource_name, resource_type=self.resource_type
                )

        except Exception as e:
            logging.exception(
                f"An error occurred while fetching resource {self.resource_name} of type {self.resource_type} from DynamoDB: {e}"
            )

            raise

    def ssm_resource_endpoint_lookup(self) -> str:
        """
        Return the endpoint for a resource registered with service discovery. The app_name and deployment_id
        parameters are optional. If not provided, the values will be loaded from the environment.

        Keyword Arguments:
            resource_type: Type of the resource
            resource_name: Name of the resource
            app_name: Name of the application (default: None)
            deployment_id: Unique identifier for the installation (default: None)
        """
        if self.app_name is None or self.deployment_id is None:
            raise ValueError("app_name and deployment_id must be set for SSM lookup")

        param_name = self.ssm_parameter_name(
            app_name=self.app_name,
            deployment_id=self.deployment_id,
            resource_type=self.resource_type,
            resource_name=self.resource_name,
        )

        # Check if the parameter is cached
        current_time = time.time()

        if param_name in cache and (current_time - cache_timestamps[param_name] < CACHE_TTL):
            logging.info(
                f"Cache hit for resource: {self.resource_name} of type {self.resource_type}"
            )

            return cache[param_name]

        logging.info(f"Cache miss for resource: {self.resource_name} of type {self.resource_type}")

        ssm = boto3.client("ssm")

        try:
            results = ssm.get_parameter(Name=param_name)

            # Cache the result
            cache[param_name] = results["Parameter"]["Value"]

            cache_timestamps[param_name] = current_time

            logging.info(
                f"Resource {self.resource_name} of type {self.resource_type} fetched from SSM and cached."
            )

            return str(results["Parameter"]["Value"])

        except ssm.exceptions.ParameterNotFound:
            logging.error(
                f"Resource {self.resource_name} of type {self.resource_type} not found in SSM."
            )

            raise ResourceNotFoundError(
                resource_name=self.resource_name, resource_type=self.resource_type
            ) from None

        except Exception as e:
            logging.exception(
                f"An error occurred while fetching resource {self.resource_name} of type {self.resource_type}: {e}"
            )

            raise
