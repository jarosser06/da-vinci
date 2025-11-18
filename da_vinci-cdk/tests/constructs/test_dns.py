"""Unit tests for da_vinci_cdk.constructs.dns module."""

from unittest.mock import patch

from aws_cdk.assertions import Template

from da_vinci_cdk.constructs.dns import CName, PublicDomain


class TestPublicDomain:
    """Tests for PublicDomain construct."""

    def test_public_domain_creation(self, stack):
        """Test PublicDomain creation."""
        domain = PublicDomain(
            domain_name="example.com",
            scope=stack,
        )

        assert domain is not None
        assert domain.hosted_zone is not None

        template = Template.from_stack(stack)
        template.resource_count_is("AWS::Route53::HostedZone", 1)
        template.has_resource_properties(
            "AWS::Route53::HostedZone",
            {"Name": "example.com."},
        )

    def test_public_domain_with_custom_construct_id(self, stack):
        """Test PublicDomain with custom construct ID."""
        domain = PublicDomain(
            domain_name="example.com",
            scope=stack,
            construct_id="custom-domain",
        )

        assert domain is not None
        template = Template.from_stack(stack)
        template.resource_count_is("AWS::Route53::HostedZone", 1)

    def test_public_domain_with_app_name_and_deployment_id(self, stack):
        """Test PublicDomain with app_name and deployment_id."""
        domain = PublicDomain(
            domain_name="example.com",
            scope=stack,
            app_name="test-app",
            deployment_id="test-deployment",
        )

        assert domain is not None
        template = Template.from_stack(stack)
        template.resource_count_is("AWS::Route53::HostedZone", 1)

    @patch("da_vinci_cdk.constructs.dns.DiscoverableResource.read_endpoint")
    def test_public_domain_with_subdomain(self, mock_read_endpoint, stack):
        """Test PublicDomain as a subdomain of another domain."""
        # Mock the parent hosted zone lookup
        mock_read_endpoint.return_value = "Z1234567890ABC"

        domain = PublicDomain(
            domain_name="sub.example.com",
            scope=stack,
            sub_domain_of="example.com",
        )

        assert domain is not None
        template = Template.from_stack(stack)
        template.resource_count_is("AWS::Route53::HostedZone", 1)
        template.resource_count_is("AWS::Route53::RecordSet", 1)

    def test_record_name_method(self, stack):
        """Test the record_name method."""
        domain = PublicDomain(
            domain_name="example.com",
            scope=stack,
        )

        result = domain.record_name("api.example.com", "example.com")
        assert result == "api"

    @patch("da_vinci_cdk.constructs.dns.DiscoverableResource.read_endpoint")
    def test_hosted_zone_from_name(self, mock_read_endpoint, stack):
        """Test hosted_zone_from_name static method."""
        mock_read_endpoint.return_value = "Z1234567890ABC"

        zone = PublicDomain.hosted_zone_from_name(
            name="example.com",
            scope=stack,
        )

        assert zone is not None
        mock_read_endpoint.assert_called_once()


class TestCName:
    """Tests for CName construct."""

    @patch("da_vinci_cdk.constructs.dns.DiscoverableResource.read_endpoint")
    def test_cname_creation(self, mock_read_endpoint, stack):
        """Test CName creation."""
        mock_read_endpoint.return_value = "Z1234567890ABC"

        cname = CName(
            record_name="api",
            scope=stack,
            value="target.example.com",
            domain_name="example.com",
        )

        assert cname is not None
        assert cname.cname is not None

        template = Template.from_stack(stack)
        template.resource_count_is("AWS::Route53::RecordSet", 1)

    @patch("da_vinci_cdk.constructs.dns.DiscoverableResource.read_endpoint")
    def test_cname_with_custom_construct_id(self, mock_read_endpoint, stack):
        """Test CName with custom construct ID."""
        mock_read_endpoint.return_value = "Z1234567890ABC"

        cname = CName(
            record_name="api",
            scope=stack,
            value="target.example.com",
            domain_name="example.com",
            construct_id="custom-cname",
        )

        assert cname is not None
        template = Template.from_stack(stack)
        template.resource_count_is("AWS::Route53::RecordSet", 1)

    @patch("da_vinci_cdk.constructs.dns.DiscoverableResource.read_endpoint")
    def test_cname_with_app_name_and_deployment_id(self, mock_read_endpoint, stack):
        """Test CName with app_name and deployment_id."""
        mock_read_endpoint.return_value = "Z1234567890ABC"

        cname = CName(
            record_name="api",
            scope=stack,
            value="target.example.com",
            domain_name="example.com",
            app_name="test-app",
            deployment_id="test-deployment",
        )

        assert cname is not None
        template = Template.from_stack(stack)
        template.resource_count_is("AWS::Route53::RecordSet", 1)

    @patch("da_vinci_cdk.constructs.dns.DiscoverableResource.read_endpoint")
    def test_cname_uses_context_domain_name(self, mock_read_endpoint, app):
        """Test CName uses root_domain_name from context when not specified."""
        from aws_cdk import Stack

        app.node.set_context("root_domain_name", "context-example.com")
        stack = Stack(app, "TestStack")
        mock_read_endpoint.return_value = "Z1234567890ABC"

        cname = CName(
            record_name="api",
            scope=stack,
            value="target.example.com",
        )

        assert cname is not None
        template = Template.from_stack(stack)
        template.resource_count_is("AWS::Route53::RecordSet", 1)
