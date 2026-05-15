"""Deployment context shared across the validation library.

A :class:`Context` carries the three coordinates every lookup needs: the
application name, the deployment id, and the AWS region. Resource names follow
the framework convention ``{app_name}-{deployment_id}-{resource}`` and SSM
service-discovery parameters are namespaced by app + deployment id, so these
three values are sufficient to address every deployed resource.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Context:
    """Addresses a single deployed da_vinci application.

    ``resource_discovery_storage`` defaults to ``"ssm"`` because the
    integration application deploys with the framework default; reads from
    outside a Lambda must state it explicitly since there is no
    ``DA_VINCI_RESOURCE_DISCOVERY_STORAGE`` env var to fall back to.
    """

    app_name: str
    deployment_id: str
    region: str
    resource_discovery_storage: str = "ssm"
