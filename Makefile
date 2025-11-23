PYTHON ?= python
PIP ?= pip

PROJECT_NAME := docops-mcp-assistant

.PHONY: help dev test mcp-servers install lint format docker-up docker-down

help:
	@echo ""
	@echo "$(PROJECT_NAME) — полезные команды:"
	@echo ""
	@echo "  make install       Установить зависимости (приложение + dev-зависимости)"
	@echo "  make dev           Запустить приложение (FastAPI + Gradio)"
	@echo "  make mcp-servers   Запустить все MCP-серверы (git, confluence, vector)"
	@echo "  make test          Запустить pytest"
	@echo "  make lint          Проверка стиля (ruff)"
	@echo "  make format        Форматирование кода (black + isort)"
	@echo "  make docker-up     Запуск через docker-compose up --build"
	@echo "  make docker-down   Остановить docker-compose"
	@echo ""

install:
	$(PIP) install --upgrade pip
	$(PIP) install ".[dev]"
	$(PIP) install -e mcp-servers/confluence-mcp-server
	$(PIP) install -e mcp-servers/git-mcp-server
	$(PIP) install -e mcp-servers/vector-mcp-server

dev:
	$(PYTHON) -m app.main

test:
	$(PYTHON) -m pytest

lint:
	$(PYTHON) -m ruff check app mcp-servers tests

format:
	$(PYTHON) -m black app mcp-servers tests
	$(PYTHON) -m isort app mcp-servers tests

mcp-servers:
	@echo "Запускаю MCP-серверы (git, confluence, vector)..."
	@echo "Они будут работать в этом же терминале. Остановить: Ctrl+C."
	$(PYTHON) -m mcp_git.server & \
	$(PYTHON) -m mcp_confluence.server & \
	$(PYTHON) -m mcp_vector.server

docker-up:
	docker compose up --build

docker-down:
	docker compose down