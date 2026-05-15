ARG IMAGE
FROM ${IMAGE}

ARG FUNCTION_INDEX
ARG FUNCTION_HANDLER

# Copy the entire app directory so handlers can import shared modules
COPY . ${LAMBDA_TASK_ROOT}/

CMD ["${FUNCTION_INDEX}.${FUNCTION_HANDLER}"]
