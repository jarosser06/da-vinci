ARG IMAGE=public.ecr.aws/lambda/python:3.12
FROM $IMAGE

# set the pip cache location
ENV PIP_CACHE_DIR=/tmp/pip-cache

# Install system dependencies needed by da-vinci
RUN dnf install -y gcc libxml2-devel libxslt-devel git && \
    rm -Rf /var/cache/yum && \
    pip install --upgrade pip

ADD . ${LAMBDA_TASK_ROOT}/da_vinci
RUN if [ -f ${LAMBDA_TASK_ROOT}/da_vinci/pyproject.toml ]; then \
        pip install poetry && \
        poetry config virtualenvs.create false && \
        cd ${LAMBDA_TASK_ROOT}/da_vinci/ && \
        poetry install; \
    fi 
