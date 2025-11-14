from aws_cdk import aws_route53 as cdk_route53

from constructs import Construct
from da_vinci.core.resource_discovery import ResourceType
from da_vinci_cdk.constructs.resource_discovery import (
    DiscoverableResource,
)


class CName(Construct):
    def __init__(
        self,
        record_name: str,
        scope: Construct,
        value: str,
        app_name: str | None = None,
        construct_id: str | None = None,
        deployment_id: str | None = None,
        domain_name: str | None = None,
    ) -> None:
        """
        Create a CNAME record

        Keyword Arguments:
            record_name: The record name
            scope: The parent construct
            value: The CNAME value
            construct_id: The construct identifier, Optional
            domain_name: The domain name, defaults to the root domain name if set
        """
        full_record_name = f"{record_name}.{domain_name}"

        construct_id = construct_id or f"{full_record_name}-cname"

        super().__init__(scope, construct_id)

        root_hosted_zone = PublicDomain.hosted_zone_from_name(
            app_name=app_name,
            deployment_id=deployment_id,
            name=domain_name or self.node.get_context("root_domain_name"),
            scope=self,
        )

        self.cname = cdk_route53.CnameRecord(
            self,
            id=f"{full_record_name}-cname-record",
            domain_name=value,
            record_name=record_name,
            zone=root_hosted_zone,
        )


class PublicDomain(Construct):
    def __init__(
        self,
        domain_name: str,
        scope: Construct,
        app_name: str | None = None,
        construct_id: str | None = None,
        deployment_id: str | None = None,
        sub_domain_of: str | None = None,
    ) -> None:

        construct_id = construct_id or f"domain-{domain_name}"

        super().__init__(scope, construct_id)

        self.hosted_zone = cdk_route53.PublicHostedZone(
            self,
            f"{construct_id}-hosted-zone",
            zone_name=domain_name,
        )

        self.discovery_resource = DiscoverableResource(
            app_name=app_name,
            deployment_id=deployment_id,
            construct_id=f"{construct_id}-discovery-resource",
            resource_name=domain_name,
            resource_type=ResourceType.DOMAIN,
            resource_endpoint=self.hosted_zone.hosted_zone_id,
            scope=self,
        )

        if sub_domain_of:
            root_hosted_zone = self.hosted_zone_from_name(
                app_name=app_name,
                deployment_id=deployment_id,
                name=sub_domain_of,
                scope=self,
            )

            self.sub_domain_ns_record = cdk_route53.NsRecord(
                self,
                id=f"{construct_id}-ns-record",
                record_name=domain_name,
                values=self.hosted_zone.hosted_zone_name_servers,
                zone=root_hosted_zone,
            )

    def record_name(self, name: str, root_domain: str):
        """
        Find the record name for a sub domain of the root domain

        Keyword Arguments:
            name: The sub domain name
            root_domain: The root domain name
        """

        return name.replace(f".{root_domain}", "")

    @staticmethod
    def hosted_zone_from_name(
        name: str, scope: Construct, app_name: str | None = None, deployment_id: str | None = None
    ) -> cdk_route53.IHostedZone:
        """
        Lookup a public hosted zone by domain name

        Keyword Arguments:
            app_name: The application name, Optional
            deployment_id: The deployment identifier, Optional
            name: The domain name to lookup
            scope: The parent construct
        """

        zone_id = DiscoverableResource.read_endpoint(
            app_name=app_name,
            deployment_id=deployment_id,
            resource_name=name,
            resource_type=ResourceType.DOMAIN,
            scope=scope,
        )

        return cdk_route53.PublicHostedZone.from_hosted_zone_attributes(
            scope=scope,
            id=f"f{name}-hosted-zone-lookup",
            hosted_zone_id=zone_id,
            zone_name=name,
        )
