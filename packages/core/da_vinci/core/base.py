def standard_aws_resource_name(app_name: str, deployment_id: str, name: str) -> str:
    """
    Standardize the naming convention for AWS resources

    Keyword Arguments:
        app_name: Name of the application
        deployment_id: Unique identifier for the installation
        name: Name of the resource
    """
    return f"{app_name}-{deployment_id}-{name}"
