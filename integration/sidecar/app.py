"""SideCarApplication entry point for the integration suite.

The sidecar attaches to a Da Vinci application already deployed in the same
account/region. It reuses the parent's event bus, exception trap and global
settings — exactly the scenario ``SideCarApplication`` is designed for.

Reads:
  * ``DA_VINCI_IT_APP_NAME``         — parent app name (default: da_vinci_it)
  * ``DA_VINCI_IT_DEPLOYMENT_ID``    — the shared deployment id
  * ``DA_VINCI_IT_SIDECAR_APP_NAME`` — name of this sidecar (default: sidecar)
"""

import os

import aws_cdk as cdk
import constructs
import jsii
from aws_cdk import aws_dynamodb
from stacks.echo_stack import SidecarEchoStack

from da_vinci_cdk.application import SideCarApplication


@jsii.implements(cdk.IAspect)
class _DestroyTables:
    def visit(self, node: constructs.IConstruct) -> None:
        if isinstance(node, aws_dynamodb.CfnGlobalTable):
            node.apply_removal_policy(cdk.RemovalPolicy.DESTROY)


def _required(name: str, default: str | None = None) -> str:
    value = os.environ.get(name, default)

    if not value:
        raise RuntimeError(f"{name} must be set when synthesizing the da_vinci sidecar app.")

    return value


sidecar = SideCarApplication(
    app_name=_required("DA_VINCI_IT_APP_NAME", "da-vinci-it"),
    deployment_id=_required("DA_VINCI_IT_DEPLOYMENT_ID"),
    sidecar_app_name=_required("DA_VINCI_IT_SIDECAR_APP_NAME", "sidecar"),
    app_entry=os.path.dirname(os.path.abspath(__file__)),
)

sidecar.add_uninitialized_stack(SidecarEchoStack)

cdk.Aspects.of(sidecar.cdk_app).add(_DestroyTables())

sidecar.synth()
