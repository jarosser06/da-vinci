"""Deploy / destroy lifecycle for the integration application + sidecar.

A single :class:`Deployment` owns one unique ``deployment_id`` (the "install
id") and drives ``cdk deploy`` for the parent app then the sidecar, exposing
the coordinates the read-side helpers need. On teardown it destroys the
sidecar first, then the parent.

The parent app and sidecar read their identity from environment variables
(see ``integration/app/app.py`` and ``integration/sidecar/app.py``), so this
manager's job is to set those variables consistently and shell out to the CDK
CLI in each project directory.
"""

from __future__ import annotations

import logging
import os
import subprocess
import uuid
from pathlib import Path

from lib.context import Context

logger = logging.getLogger("integration.deployment")

# Must match the defaults baked into the CDK entry points.
PARENT_APP_NAME = "da-vinci-it"
SIDECAR_APP_NAME = "sidecar"
DEFAULT_REGION = "us-east-1"

_INTEGRATION_ROOT = Path(__file__).resolve().parent.parent
_APP_DIR = _INTEGRATION_ROOT / "app"
_SIDECAR_DIR = _INTEGRATION_ROOT / "sidecar"

_CDK = ["npx", "--no-install", "cdk"]


class Deployment:
    """Manages one real-AWS install of the integration app + sidecar."""

    def __init__(
        self,
        install_id: str | None = None,
        region: str | None = None,
        keep: bool = False,
        reuse: bool = False,
    ) -> None:
        """
        Keyword Arguments:
            install_id: Reuse this deployment id; generated when ``None``.
            region: AWS region to deploy into (default ``us-east-1``).
            keep: Skip ``cdk destroy`` on teardown.
            reuse: Skip ``cdk deploy`` on setup (an install must already exist).
        """
        self.install_id = install_id or f"it-{uuid.uuid4().hex[:8]}"

        self.region = region or DEFAULT_REGION

        self.keep = keep

        self.reuse = reuse

    @property
    def context(self) -> Context:
        """Coordinates of the parent application."""
        return Context(
            app_name=PARENT_APP_NAME,
            deployment_id=self.install_id,
            region=self.region,
        )

    @property
    def sidecar_context(self) -> Context:
        """Coordinates of the sidecar application's own resources."""
        return Context(
            app_name=f"{PARENT_APP_NAME}-{SIDECAR_APP_NAME}",
            deployment_id=self.install_id,
            region=self.region,
        )

    def _env(self) -> dict[str, str]:
        env = dict(os.environ)

        env.update(
            {
                "DA_VINCI_IT_DEPLOYMENT_ID": self.install_id,
                "DA_VINCI_IT_APP_NAME": PARENT_APP_NAME,
                "DA_VINCI_IT_SIDECAR_APP_NAME": SIDECAR_APP_NAME,
                "AWS_REGION": self.region,
                "AWS_DEFAULT_REGION": self.region,
                "CDK_DEFAULT_REGION": self.region,
            }
        )

        return env

    def _run_cdk(self, cwd: Path, *args: str) -> None:
        command = [*_CDK, *args]

        logger.info("Running %s (cwd=%s)", " ".join(command), cwd)

        subprocess.run(command, cwd=cwd, env=self._env(), check=True)

    def deploy(self) -> None:
        """Deploy the parent app then the sidecar (unless reusing an install)."""
        if self.reuse:
            logger.info("Reusing existing deployment %s", self.install_id)
            return

        logger.info("Deploying integration install %s to %s", self.install_id, self.region)

        self._run_cdk(_APP_DIR, "deploy", "--all", "--require-approval", "never")

        self._run_cdk(_SIDECAR_DIR, "deploy", "--all", "--require-approval", "never")

    def destroy(self) -> None:
        """Destroy the sidecar then the parent (unless ``keep`` was requested)."""
        if self.keep:
            logger.info(
                "Keeping deployment %s alive (--keep). Tear down later with: "
                "DA_VINCI_IT_INSTALL_ID=%s runbook it-destroy",
                self.install_id,
                self.install_id,
            )
            return

        logger.info("Destroying integration install %s", self.install_id)

        try:
            self._run_cdk(_SIDECAR_DIR, "destroy", "--all", "--force")
        except subprocess.CalledProcessError:
            logger.exception("Sidecar destroy failed; continuing to parent destroy")

        self._run_cdk(_APP_DIR, "destroy", "--all", "--force")
