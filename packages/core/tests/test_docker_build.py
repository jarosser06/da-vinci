"""Integration tests for Docker image builds"""

import docker
import pytest


def test_library_base_image_has_davinci():
    """Test that da-vinci package is installed in the library base image"""
    # Try common Docker socket locations
    import os
    from pathlib import Path

    socket_paths = [
        "unix:///var/run/docker.sock",  # Standard Linux
        f"unix://{Path.home()}/.docker/run/docker.sock",  # Docker Desktop Mac
        f"unix://{Path.home()}/.colima/default/docker.sock",  # Colima
    ]

    client = None
    for socket in socket_paths:
        try:
            client = docker.DockerClient(base_url=socket)
            client.ping()  # Test connection
            break
        except (docker.errors.DockerException, Exception):
            continue

    if not client:
        pytest.skip("Docker is not available")

    # Build the image
    image, logs = client.images.build(
        path="packages/core/da_vinci",
        dockerfile="Dockerfile",
        buildargs={"DA_VINCI_VERSION": "3.0.4"},
        tag="test-davinci:latest",
    )

    # Test 1: da-vinci package is importable
    result = client.containers.run(
        "test-davinci:latest",
        command="python -c 'import da_vinci; print(da_vinci.__version__)'",
        entrypoint="",  # Override Lambda entrypoint
        remove=True,
    )
    assert b"3.0.4" in result

    # Test 2: requests is available
    result = client.containers.run(
        "test-davinci:latest",
        command="python -c 'import requests; print(requests.__version__)'",
        entrypoint="",  # Override Lambda entrypoint
        remove=True,
    )
    assert result  # Should not error

    # Test 3: Can import event bus client (the failing import)
    result = client.containers.run(
        "test-davinci:latest",
        command="python -c 'from da_vinci.event_bus.client import EventResponder; print(\"OK\")'",
        entrypoint="",  # Override Lambda entrypoint
        remove=True,
    )
    assert b"OK" in result

    # Cleanup
    client.images.remove("test-davinci:latest", force=True)
