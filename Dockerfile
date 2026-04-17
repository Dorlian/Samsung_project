# Образ для Фотоассистента: Python + Tkinter + зависимости OpenCV/MediaPipe/PyTorch (CPU).
# База: Debian bookworm (Python 3.11) с пакетом python3-tk — официальный slim-образ Python
# не собирает tkinter для /usr/local/bin/python, из-за чего GUI в контейнере не заводится.

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
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# PyTorch из PyPI на Linux тянет CUDA и раздувает образ; для контейнера — только CPU-сборка.
COPY requirements-docker.txt .
RUN python3 -m venv /opt/venv \
    && pip install --upgrade pip \
    && pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu \
    && pip install -r requirements-docker.txt

COPY . .

# GUI: на хосте нужен DISPLAY и (на Linux) сокет X11 — см. README.
# По умолчанию в compose включён виртуальный дисплей (xvfb), чтобы контейнер запускался без настройки X11.
CMD ["bash", "/app/docker/entrypoint.sh"]
