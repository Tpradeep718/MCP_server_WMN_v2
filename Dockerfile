FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    iw \
    iproute2 \
    wireless-tools \
    net-tools \
    batctl \
    iputils-ping \
    sudo \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

COPY src/ ./src/
COPY config.yaml .

EXPOSE 8000

ENTRYPOINT ["python3", "src/server.py", "--transport", "http", "--port", "8000"]
