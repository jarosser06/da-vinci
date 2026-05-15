"""CDK entry point for the da_vinci integration test application.

Wires up the full feature surface area in a single Application:
  * GlobalSetting    (SettingsStack)
  * DynamoDB ORM     (OrmStack — PersonTable)
  * Event bus + four subscribers (EventHandlersStack)
  * SimpleRESTService over the ORM (RestStack)
  * Implicit: event_bus + exception_trap framework stacks

``deployment_id`` is read from ``DA_VINCI_IT_DEPLOYMENT_ID`` so the lifecycle
manager in ``lib/deployment.py`` can issue unique installs per run.
"""

import os

import aws_cdk as cdk
import constructs
import jsii
from aws_cdk import aws_dynamodb
from stacks.event_handlers_stack import EventHandlersStack
from stacks.orm_stack import OrmStack
from stacks.rest_stack import RestStack
from stacks.settings_stack import SettingsStack

from da_vinci_cdk.application import Application


@jsii.implements(cdk.IAspect)
class _DestroyTables:
    """Force RemovalPolicy.DESTROY on every DynamoDB table in the integration app.

    The framework defaults to RETAIN (correct for production). For the
    integration test app we always want tables deleted with the stack so
    we don't accumulate orphaned tables across test runs.
    """

    def visit(self, node: constructs.IConstruct) -> None:
        if isinstance(node, aws_dynamodb.CfnGlobalTable):
            node.apply_removal_policy(cdk.RemovalPolicy.DESTROY)


def _deployment_id() -> str:
    value = os.environ.get("DA_VINCI_IT_DEPLOYMENT_ID")

    if not value:
        raise RuntimeError(
            "DA_VINCI_IT_DEPLOYMENT_ID must be set when synthesizing the "
            "da_vinci integration test application."
        )

    return value


def _app_name() -> str:
    # Stack names propagate this directly to CloudFormation, which only
    # allows ``[A-Za-z][A-Za-z0-9-]*`` — no underscores.
    return os.environ.get("DA_VINCI_IT_APP_NAME", "da-vinci-it")


app = Application(
    app_name=_app_name(),
    deployment_id=_deployment_id(),
    app_entry=os.path.dirname(os.path.abspath(__file__)),
    enable_event_bus=True,
    enable_exception_trap=True,
)

app.add_uninitialized_stack(SettingsStack)
app.add_uninitialized_stack(OrmStack)
app.add_uninitialized_stack(EventHandlersStack)
app.add_uninitialized_stack(RestStack)

cdk.Aspects.of(app.cdk_app).add(_DestroyTables())

app.synth()
