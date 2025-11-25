#!/usr/bin/env bash
set -euo pipefail

# --- Определяем корень проекта ---
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# --- Лог-файл ---
LOGFILE="${ROOT}/run_all.log"

# --- Перезаписываем лог при каждом запуске ---
echo "============================================" > "$LOGFILE"
echo "DocOps MCP Assistant — RUN LOG" >> "$LOGFILE"
echo "Started at $(date)" >> "$LOGFILE"
echo "ROOT = ${ROOT}" >> "$LOGFILE"
echo "============================================" >> "$LOGFILE"
echo >> "$LOGFILE"

# --- Функция логирования: пишем и в консоль, и в лог ---
log() {
  echo "$1"
  echo "$1" >> "$LOGFILE"
}

log "============================================"
log "  DocOps MCP Assistant — FULL START"
log "  ROOT = ${ROOT}"
log "  LOG  = ${LOGFILE}"
log "============================================"

# --- Проверяем, доступен ли python3/python ---
if ! command -v python3 >/dev/null 2>&1; then
  if ! command -v python >/dev/null 2>&1; then
    log "[ERROR] 'python3' or 'python' is not found in PATH."
    log "Install Python 3 and make 'Add to PATH'."
    exit 1
  else
    GLOBAL_PY="python"
  fi
else
  GLOBAL_PY="python3"
fi

log "[INFO] Let's use global interpreter: ${GLOBAL_PY}"

# --- Создаем venv, если его еще нет ---
if [ ! -f "${ROOT}/.venv/bin/python" ]; then
  log "[1/6] Creating virtual environment using ${GLOBAL_PY} ..."
  "${GLOBAL_PY}" -m venv "${ROOT}/.venv" >> "$LOGFILE" 2>&1
else
  log "[1/6] Virtual environment already exists, skipping creation."
fi

# --- Путь до python в venv ---
PY="${ROOT}/.venv/bin/python"

if [ ! -f "$PY" ]; then
  log "[ERROR] ${PY} is not found"
  log "Virtual environment wasn't created or was deleted"
  log "Try to execute this command:   ${GLOBAL_PY} -m venv .venv"
  exit 1
fi

log "[INFO] Using venv python: ${PY}"

# --- Установка зависимостей ---
log "[2/6] Installing dependencies from requirements.txt ..."
"$PY" -m pip install --upgrade pip >> "$LOGFILE" 2>&1
if [ $? -ne 0 ]; then
  log "[ERROR] pip upgrade failed. See more in ${LOGFILE}"
  exit 1
fi

"$PY" -m pip install -r "${ROOT}/requirements.txt" >> "$LOGFILE" 2>&1
if [ $? -ne 0 ]; then
  log "[ERROR] Installing root dependencies failed. See more in ${LOGFILE}"
  exit 1
fi

# --- Установка MCP-серверов (editable) ---
log "[3/6] Installing MCP servers (editable)..."
"$PY" -m pip install -e "${ROOT}/mcp-servers/git-mcp-server" >> "$LOGFILE" 2>&1
if [ $? -ne 0 ]; then
  log "[WARN] Failed to install git-mcp-server in editable mode. See more in ${LOGFILE}"
fi

"$PY" -m pip install -e "${ROOT}/mcp-servers/confluence-mcp-server" >> "$LOGFILE" 2>&1
if [ $? -ne 0 ]; then
  log "[WARN] Failed to install confluence-mcp-server in editable mode. See more in ${LOGFILE}"
fi

"$PY" -m pip install -e "${ROOT}/mcp-servers/vector-mcp-server" >> "$LOGFILE" 2>&1
if [ $? -ne 0 ]; then
  log "[WARN] Failed to install vector-mcp-server in editable mode. See more in ${LOGFILE}"
fi

# --- Подхватываем .env (формат: KEY=VAL, без пробелов вокруг '=') ---
if [ -f "${ROOT}/.env" ]; then
  log "[4/6] Loading .env ..."
  while IFS='=' read -r key val; do
    # Пропускаем комментарии и пустые строки
    [[ "$key" =~ ^#.*$ ]] && continue
    [[ -z "$key" ]] && continue

    export "$key=$val"
    echo "[ENV] $key=$val" >> "$LOGFILE"
  done < "${ROOT}/.env"
else
  log "[4/6] .env not found, skipping..."
fi

# --- Генерим демо-данные ---
log "[5/6] Seeding demo data..."
"$PY" -m scripts.seed_demo_data >> "$LOGFILE" 2>&1
if [ $? -ne 0 ]; then
  log "[ERROR] seed_demo_data failed. См. ${LOGFILE}"
  exit 1
fi

log ""
log "============================================"
log "  Starting MCP servers in separate windows"
log "============================================"

# --- Запускаем MCP-сервера в отдельных окнах (в фоне) ---
"$PY" -m mcp_git.server >> "$LOGFILE" 2>&1 &
"$PY" -m mcp_confluence.server >> "$LOGFILE" 2>&1 &
"$PY" -m mcp_vector.server >> "$LOGFILE" 2>&1 &

log ""
log "============================================"
log "  Starting Gradio UI (main app)"
log "  Open: http://localhost:${DOCOPS_GRADIO_PORT:-7860}"
log "  Log:  ${LOGFILE}"
log "============================================"

cd "$ROOT"
"$PY" -m app.main >> "$LOGFILE" 2>&1

log "[INFO] app.main exited. See more in logs."