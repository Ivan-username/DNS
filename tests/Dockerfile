FROM alpine:3.20

COPY requirements.txt /tmp/requirements.txt

RUN apk add --no-cache bash bind-tools python3 py3-pip \
    && python3 -m venv /opt/venv \
    && /opt/venv/bin/pip install --no-cache-dir -r /tmp/requirements.txt

ENV PATH="/opt/venv/bin:${PATH}"

CMD ["sleep", "infinity"]
