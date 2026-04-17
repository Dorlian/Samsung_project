# Образ для Фотоассистента: Python + Tkinter + OpenCV/MediaPipe/PyTorch (CPU).
FROM debian:bookworm-slim

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    PATH="/opt/venv/bin:${PATH}"

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    python3 \
    python3-venv \
    python3-pip \
    python3-tk \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libgomp1 \
    xvfb \
    xauth \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements/requirements-docker.txt /tmp/requirements-docker.txt
RUN python3 -m venv /opt/venv \
    && pip install --upgrade pip \
    && pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu \
    && pip install -r /tmp/requirements-docker.txt

# Скрипт вне /app: при run том ../:/app подменяет весь проект с Windows, иначе CRLF в entrypoint с диска ломает «pipefail».
COPY deploy/docker/entrypoint.sh /entrypoint.sh
RUN sed -i 's/\r$//' /entrypoint.sh && chmod +x /entrypoint.sh

COPY . .

CMD ["bash", "/entrypoint.sh"]
