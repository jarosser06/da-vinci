# the base image is passed in as argument
ARG IMAGE
FROM $IMAGE

# set the pip cache location
ENV PIP_CACHE_DIR=/tmp/pip-cache

# set the poetry cache
ENV POETRY_CACHE_DIR=/tmp/poetry-cache

RUN dnf install -y gcc libxml2-devel libxslt-devel git && \
    rm -Rf /var/cache/yum && \
    pip install --upgrade pip && \
    pip install poetry


RUN poetry config virtualenvs.create false

ADD . ${LAMBDA_TASK_ROOT}/da_vinci

RUN cd ${LAMBDA_TASK_ROOT}/da_vinci/ && poetry install 
