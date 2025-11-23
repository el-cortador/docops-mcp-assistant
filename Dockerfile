FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Системные зависимости по минимуму (при необходимости расширишь)
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
 && rm -rf /var/lib/apt/lists/*

# Скопировать манифесты и установить зависимости
COPY pyproject.toml pytest.ini ./
COPY app ./app
COPY mcp-servers ./mcp-servers

# Установка зависимостей проекта
RUN pip install --upgrade pip \
 && pip install .[dev] || pip install .

# Установка MCP-серверов в editable-режиме (опционально, но удобно)
RUN pip install -e mcp-servers/confluence-mcp-server \
 && pip install -e mcp-servers/git-mcp-server \
 && pip install -e mcp-servers/vector-mcp-server

# Папка для демо-данных
RUN mkdir -p demo_data/vector_store demo_data/demo_repos

EXPOSE 7860

CMD ["python", "-m", "app.main"]