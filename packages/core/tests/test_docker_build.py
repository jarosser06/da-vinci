"""Integration tests for Docker image builds."""

from pathlib import Path

import docker
import pytest

import da_vinci


def _docker_client() -> "docker.DockerClient | None":
    """Return a connected Docker client, or None if Docker is unavailable."""
    socket_paths = [
        "unix:///var/run/docker.sock",  # Standard Linux
        f"unix://{Path.home()}/.docker/run/docker.sock",  # Docker Desktop Mac
        f"unix://{Path.home()}/.colima/default/docker.sock",  # Colima
    ]

    for socket in socket_paths:
        try:
            client = docker.DockerClient(base_url=socket)
            client.ping()
        except docker.errors.DockerException:
            continue
        else:
            return client

    return None


def _run(client: "docker.DockerClient", command: str) -> tuple[int, str]:
    """Run a command in the built image and return (exit_code, decoded_stdout)."""
    container = client.containers.run(
        "test-davinci:latest",
        command=command,
        entrypoint="",  # Override the Lambda entrypoint.
        detach=True,
    )
    try:
        result = container.wait()
        exit_code = result["StatusCode"]
        output = container.logs(stdout=True, stderr=True).decode("utf-8")
        return exit_code, output
    finally:
        container.remove(force=True)


@pytest.mark.integration
def test_library_base_image_has_davinci():
    """The built image imports da_vinci and reports the packaged version."""
    client = _docker_client()
    if client is None:
        pytest.skip("Docker is not available")

    expected_version = da_vinci.__version__

    client.images.build(
        path="packages/core/da_vinci",
        dockerfile="Dockerfile",
        buildargs={"DA_VINCI_VERSION": expected_version},
        tag="test-davinci:latest",
    )

    try:
        # da_vinci is importable and reports the exact packaged version.
        exit_code, output = _run(
            client,
            "python -c 'import da_vinci; print(da_vinci.__version__)'",
        )
        assert exit_code == 0, output
        assert output.strip() == expected_version

        # requests is available and prints a non-empty version on a clean exit.
        exit_code, output = _run(
            client,
            "python -c 'import requests; print(requests.__version__)'",
        )
        assert exit_code == 0, output
        assert output.strip() != ""

        # The event bus client (the historically failing import) loads cleanly.
        exit_code, output = _run(
            client,
            "python -c 'from da_vinci.event_bus.client import EventResponder; " 'print("OK")\'',
        )
        assert exit_code == 0, output
        assert output.strip() == "OK"
    finally:
        client.images.remove("test-davinci:latest", force=True)
