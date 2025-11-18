from aws_cdk import (
    Duration,
    Tags,
)
from aws_cdk import aws_apigatewayv2 as cdk_apigatewayv2
from aws_cdk import aws_certificatemanager as cdk_certificatemanager
from aws_cdk import aws_iam as cdk_iam
from aws_cdk import aws_lambda as cdk_lambda
from aws_cdk import aws_lambda_event_sources as cdk_lambda_event_sources
from aws_cdk import aws_route53 as cdk_route53
from aws_cdk import aws_route53_targets as cdk_route53_targets
from aws_cdk import aws_sqs as cdk_sqs
from aws_cdk.aws_iam import IGrantable
from constructs import Construct

from da_vinci.core.resource_discovery import ResourceType
from da_vinci_cdk.constructs.access_management import (
    ResourceAccessPolicy,
    ResourceAccessRequest,
)
from da_vinci_cdk.constructs.base import apply_framework_tags, resource_namer
from da_vinci_cdk.constructs.dns import PublicDomain
from da_vinci_cdk.constructs.lambda_function import LambdaFunction
from da_vinci_cdk.constructs.resource_discovery import DiscoverableResource


class AsyncService(Construct):
    def __init__(
        self,
        entry: str,
        index: str,
        handler: str,
        scope: Construct,
        service_name: str,
        allow_custom_metrics: bool | None = False,
        architecture: str | None = None,
        base_image: str | None = None,
        description: str | None = None,
        managed_policies: list[cdk_iam.IManagedPolicy] | None = None,
        memory_size: int | None = 128,
        dockerfile: str | None = "Dockerfile",
        resource_access_requests: list[ResourceAccessRequest] | None = None,
        timeout: Duration | None = None,
        **kwargs,
    ) -> None:
        """
        Creates an asynchronous service that can be invoked by publishing to the SQS queue created

        Keyword Arguments:
            entry: Path to the entry file
            index: Name of the entry file
            handler: Name of the handler
            scope: Parent construct for the AsyncService
            service_name: Name of the service
            allow_custom_metrics: Allow custom metrics to be sent to CloudWatch
            architecture: Architecture to use for the Lambda function
            base_image: Base image to use for the Lambda function
            description: Description of the Lambda function
            dockerfile: The name of the Dockerfile to use for the Lambda function
            managed_policies: List of managed policies to attach to the Lambda function
            memory_size: Amount of memory to allocate to the Lambda function
            timeout: Timeout for the Lambda function
            kwargs: Additional arguments to pass to the Lambda function

        Example:
            ```
            import aws_cdk
            from da_vinci_cdk.constructs.access_management import ResourceAccessRequest
            from da_vinci_cdk.constructs.services import AsyncService

            my_service = AsyncService(
                base_image=lib_base_image,
                construct_id='MyAsyncService',
                entry='path/to/entry',
                index='index.py',
                handler='handler',
                resource_access_requests=[
                    ResourceAccessRequest(
                        resource_name='my_table',
                        resource_type='table',
                        policy_name='read',
                    ),
                ],
                scope=scope,
                service_name='my_service',
                timeout=aws_cdk.Duration.seconds(30),
            )
        """
        construct_id = f"{service_name}_async_service"

        super().__init__(scope, construct_id)

        if timeout is None:
            timeout = Duration.seconds(30)

        visibility_timeout = timeout

        self.queue = cdk_sqs.Queue(
            scope=self,
            id=f"{construct_id}_queue",
            queue_name=resource_namer(name=service_name, scope=self),
            visibility_timeout=visibility_timeout,
        )

        apply_framework_tags(resource=self.queue, scope=self)

        function_name = resource_namer(name=f"{service_name}-async-handler", scope=self)

        self.handler = LambdaFunction(
            allow_custom_metrics=allow_custom_metrics,
            architecture=architecture,
            base_image=base_image,
            description=description,
            dockerfile=dockerfile,
            function_name=function_name,
            managed_policies=managed_policies,
            memory_size=memory_size,
            construct_id=f"{construct_id}_lambda_function",
            entry=entry,
            handler=handler,
            index=index,
            resource_access_requests=resource_access_requests,
            scope=self,
            timeout=timeout,
            **kwargs,
        )

        self.handler.function.add_event_source(cdk_lambda_event_sources.SqsEventSource(self.queue))

        Tags.of(self.handler).add(
            key="DaVinciFramework::FunctionPurpose", value="AsyncService", priority=200
        )

        self.discovery_resource = DiscoverableResource(
            construct_id=f"{construct_id}-discovery-resource",
            scope=self,
            resource_endpoint=self.queue.queue_url,
            resource_name=service_name,
            resource_type=ResourceType.ASYNC_SERVICE,
        )

        self.grant_publish(self.handler.function)

        self.queue_access_statement = cdk_iam.PolicyStatement(
            actions=["sqs:SendMessage"],
            resources=[self.queue.queue_arn],
        )

        self.default_access_policy = ResourceAccessPolicy(
            scope=scope,
            policy_statements=[
                self.queue_access_statement,
                self.discovery_resource.access_statement,
            ],
            resource_name=service_name,
            resource_type=ResourceType.ASYNC_SERVICE,
        )

    def grant_publish(self, resource: IGrantable):
        """
        Grants the given resource the ability to publish to the queue
        and invoke the Async Service.

        Keyword Arguments:
            resource: The resource to grant publish permissions to
        """
        self.discovery_resource.grant_read(resource=resource)

        self.queue.grant_send_messages(grantee=resource)


class SimpleRESTService(Construct):
    def __init__(
        self,
        entry: str,
        index: str,
        handler: str,
        scope: Construct,
        service_name: str,
        allow_custom_metrics: bool | None = False,
        architecture: str | None = None,
        base_image: str | None = None,
        description: str | None = None,
        dockerfile: str | None = "Dockerfile",
        managed_policies: list[cdk_iam.IManagedPolicy] | None = None,
        memory_size: int | None = 128,
        public: bool | None = False,
        resource_access_requests: list[ResourceAccessRequest] | None = None,
        timeout: Duration | None = None,
        **kwargs,
    ) -> None:
        """
        Creates a Simle REST Service that generates an endpoint using Lambda function URLs

        Keyword Arguments:
            entry: Path to the entry file
            index: Name of the entry file
            handler: Name of the handler
            scope: Parent construct for the SimpleRESTService
            service_name: Name of the service
            allow_custom_metrics: Allow custom metrics to be sent to CloudWatch
            architecture: Architecture to use for the Lambda function
            base_image: Base image to use for the Lambda function
            description: Description of the Lambda function
            managed_policies: List of managed policies to attach to the Lambda function
            memory_size: Amount of memory to allocate to the Lambda function
            dockerfile: Name of the Dockerfile used to build the Lambda function
            public: Whether or not the endpoint should be publicly accessible
            timeout: Timeout for the Lambda function
            kwargs: Additional arguments to pass to the Lambda function

        Example:
            ```
            import aws_cdk
            from da_vinci_cdk.constructs.access_management import ResourceAccessRequest
            from da_vinci_cdk.constructs.services import SimpleRESTService

            my_service = SimpleRESTService(
                base_image=lib_base_image,
                construct_id='MySimpleRESTService',
                entry='path/to/entry',
                index='index.py',
                handler='handler',
                resource_access_requests=[
                    ResourceAccessRequest(
                        resource_name='my_table',
                        resource_type='table',
                        policy_name='read_write',
                    ),
                ],
                scope=scope,
                service_name='my_service',
                timeout=aws_cdk.Duration.seconds(30),
            )
        """

        construct_id = f"{service_name}_simple_rest_service"

        super().__init__(scope, construct_id)

        if timeout is None:
            timeout = Duration.seconds(30)

        self.handler = LambdaFunction(
            allow_custom_metrics=allow_custom_metrics,
            architecture=architecture,
            base_image=base_image,
            description=description,
            dockerfile=dockerfile,
            function_name=resource_namer(name=f"{service_name}-rest-handler", scope=self),
            managed_policies=managed_policies,
            memory_size=memory_size,
            construct_id=f"{construct_id}_lambda_function",
            entry=entry,
            handler=handler,
            index=index,
            resource_access_requests=resource_access_requests,
            scope=self,
            timeout=timeout,
            **kwargs,
        )

        Tags.of(self.handler).add(
            key="DaVinciFramework::FunctionPurpose", value="SimpleRESTService", priority=200
        )

        auth_type = cdk_lambda.FunctionUrlAuthType.AWS_IAM

        if public:
            auth_type = cdk_lambda.FunctionUrlAuthType.NONE

        self.function_url = self.handler.function.add_function_url(
            auth_type=auth_type,
        )

        self.discovery_resource = DiscoverableResource(
            construct_id=f"{construct_id}-discovery-resource",
            scope=self,
            resource_endpoint=self.function_url.url,
            resource_name=service_name,
            resource_type=ResourceType.REST_SERVICE,
        )

        self.fn_url_access_statement = cdk_iam.PolicyStatement(
            actions=["lambda:InvokeFunctionURL"],
            resources=[self.function_url.function_arn],
        )

        self.default_access_policy = ResourceAccessPolicy(
            scope=scope,
            policy_statements=[
                self.fn_url_access_statement,
                self.discovery_resource.access_statement,
            ],
            resource_name=service_name,
            resource_type=ResourceType.REST_SERVICE,
        )

    def grant_invoke(self, resource: IGrantable):
        """
        Grants the given resource the ability to invoke the Simple REST Service.

        Keyword Arguments:
            resource: The resource to grant invoke permissions to
        """
        self.discovery_resource.grant_read(resource=resource)

        self.function_url.grant_invoke_url(grantee=resource)


class APIGatewayRESTService(Construct):
    def __init__(
        self,
        scope: Construct,
        service_name: str,
        subdomain_name: str | None = None,
        subdomain_certificate: cdk_certificatemanager.ICertificate | None = None,
        **api_gw_args,
    ) -> None:
        """
        Creates a REST Service that generates an endpoint using API Gateway

        Keyword Arguments:
            service_name: Name of the service
            scope: Parent construct for the APIGatewayRESTService
            api_gw_args: Additional arguments to pass to the API Gateway construct
            subdomain_name: The subdomain name to use for the API Gateway, adds the subdomain name to the app root domain
            subdomain_certificate: The certificate to use for the subdomain, if not specified a new one will be created

        Example:
            ```
            import aws_cdk
            from da_vinci_cdk.constructs.access_management import ResourceAccessRequest
            from da_vinci_cdk.constructs.services import APIGatewayRESTService

            my_service = APIGatewayRESTService(
                construct_id='MyAPIGatewayRESTService',
                scope=scope,
                service_name='my_service',
            )
            ```
        """
        construct_id = f"{service_name}_api_gateway_rest_service"

        super().__init__(scope, construct_id)

        self.domain = None

        if subdomain_name:
            if not self.node.try_get_context("root_domain_name"):
                raise ValueError(
                    "Root domain name must be set in the context to use subdomain functionality"
                )

            root_domain_name = self.node.get_context("root_domain_name")

            full_subdomain_name = f"{subdomain_name}.{root_domain_name}"

            cert = subdomain_certificate

            root_hosted_zone = PublicDomain.hosted_zone_from_name(
                app_name=self.node.get_context("app_name"),
                deployment_id=self.node.get_context("deployment_id"),
                name=root_domain_name,
                scope=self,
            )

            if not cert:
                cert = cdk_certificatemanager.Certificate(
                    self,
                    f"{construct_id}-cert",
                    domain_name=full_subdomain_name,
                    validation=cdk_certificatemanager.CertificateValidation.from_dns(
                        root_hosted_zone
                    ),
                )

            self.domain = cdk_apigatewayv2.DomainName(
                self,
                f"{construct_id}-domain",
                domain_name=full_subdomain_name,
                certificate=cert,
            )

        if self.domain:
            api_gw_args["default_domain_mapping"] = cdk_apigatewayv2.DomainMappingOptions(
                domain_name=self.domain,
            )

        self.api = cdk_apigatewayv2.HttpApi(
            scope=self,
            id=f"{construct_id}_api",
            api_name=resource_namer(name=service_name, scope=self),
            **api_gw_args,
        )

        if self.domain:
            self.dns_record = cdk_route53.ARecord(
                self,
                f"{construct_id}-dns-record",
                zone=root_hosted_zone,
                target=cdk_route53.RecordTarget.from_alias(
                    cdk_route53_targets.ApiGatewayv2DomainProperties(
                        regional_domain_name=self.domain.regional_domain_name,
                        regional_hosted_zone_id=self.domain.regional_hosted_zone_id,
                    )
                ),
                record_name=subdomain_name,
            )

        self.discovery_resource = DiscoverableResource(
            construct_id=f"{construct_id}-discovery-resource",
            scope=self,
            resource_endpoint=self.api.url,
            resource_name=service_name,
            resource_type=ResourceType.REST_SERVICE,
        )
