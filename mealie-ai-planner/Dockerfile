ARG BUILD_FROM
FROM ${BUILD_FROM}

RUN apk add --no-cache python3 py3-pip

RUN pip3 install --no-cache-dir --break-system-packages flask requests openai

COPY rootfs /
COPY app /app

RUN chmod a+x /etc/services.d/mealie-ai-planner/run

EXPOSE 8099
