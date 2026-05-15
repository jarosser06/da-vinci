"""GlobalSetting fixtures the integration tests assert against."""

from constructs import Construct

from da_vinci_cdk.constructs.global_setting import GlobalSetting
from da_vinci_cdk.stack import Stack


class SettingsStack(Stack):
    """Seed a known GlobalSetting that the REST service exposes for round-trip validation."""

    def __init__(
        self,
        app_name: str,
        architecture: str,
        deployment_id: str,
        scope: Construct,
        stack_name: str,
        library_base_image: str | None = None,
    ) -> None:
        super().__init__(
            app_name=app_name,
            architecture=architecture,
            deployment_id=deployment_id,
            scope=scope,
            stack_name=stack_name,
            library_base_image=library_base_image,
        )

        self.greeting = GlobalSetting(
            description="Greeting value exposed via the integration test REST service.",
            namespace="it::config",
            setting_key="greeting",
            setting_value="hello",
            scope=self,
        )
