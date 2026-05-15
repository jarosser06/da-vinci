ARG IMAGE=public.ecr.aws/lambda/python:3.12
FROM $IMAGE
ARG DA_VINCI_VERSION
# DA_VINCI_SRC_HASH is consumed as a CDK DockerImage.from_build build arg so
# CDK's asset hash invalidates whenever the da_vinci source tree changes —
# without this the image tag is stable and source edits never redeploy.
ARG DA_VINCI_SRC_HASH

# set the pip cache location
ENV PIP_CACHE_DIR=/tmp/pip-cache

# Install system dependencies needed by da-vinci
RUN dnf install -y gcc libxml2-devel libxslt-devel git && \
    rm -Rf /var/cache/yum && \
    pip install --upgrade pip uv

ADD . ${LAMBDA_TASK_ROOT}/da_vinci
RUN if [ -f ${LAMBDA_TASK_ROOT}/da_vinci/pyproject.toml ]; then \
        # Local source distribution (pyproject.toml shipped alongside the
        # package). Used when the lib build context is the package root.
        pip install poetry && \
        poetry config virtualenvs.create false && \
        cd ${LAMBDA_TASK_ROOT}/da_vinci/ && \
        poetry install; \
    elif [ -d ${LAMBDA_TASK_ROOT}/da_vinci/core ]; then \
        # Default workspace path: the build context is the ``da_vinci`` Python
        # package itself (no pyproject.toml here). The package is already on
        # ``${LAMBDA_TASK_ROOT}`` so it imports without pip-install; we just
        # install the runtime dependencies it declares.
        uv pip install --system boto3 requests "requests-auth-aws-sigv4==0.7"; \
    else \
        # Fallback: published wheel from the da_vinci PyPI index.
        uv pip install --system --extra-index-url https://packages.davinciproject.dev/simple/ "da-vinci==${DA_VINCI_VERSION}"; \
    fi
