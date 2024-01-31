ARG IMAGE=public.ecr.aws/lambda/python:3.11.2023.11.18.02
FROM $IMAGE

# set the pip cache location
ENV PIP_CACHE_DIR=/tmp/pip-cache

# set the poetry cache
ENV POETRY_CACHE_DIR=/tmp/poetry-cache

RUN yum install -y gcc libxml2-devel libxslt-devel git && \
    rm -Rf /var/cache/yum && \
    pip install --upgrade pip && \
    pip install poetry


RUN poetry config virtualenvs.create false

ADD . ${LAMBDA_TASK_ROOT}/da_vinci

RUN cd ${LAMBDA_TASK_ROOT}/da_vinci/ && poetry install 