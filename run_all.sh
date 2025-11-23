#!/usr/bin/env bash
set -euo pipefail

# -------------------------------------------------------------
#  Определяем корень проекта
# -------------------------------------------------------------
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOGFILE="${ROOT}/run_all.log"

# -------------------------------------------------------------
#  Стартуем логирование
# -------------------------------------------------------------
echo "============================================" > "$LOGFILE"
echo "DocOps MCP Assistant — RUN LOG" >> "$LOGFILE"
echo "Started at $(date)" >> "$LOGFILE"
echo "ROOT = ${ROOT}" >> "$LOGFILE"
echo "============================================" >> "$LOGFILE"
echo >> "$LOGFILE"

log() {
  echo "$1"
  echo "$1" >> "$LOGFILE"
}

log "============================================"
log "  DocOps MCP Assistant — FULL START"
log "  ROOT = ${ROOT}"
log "  LOG  = ${LOGFILE}"
log "============================================"

# -------------------------------------------------------------
#  1. Проверяем наличие Python
# -------------------------------------------------------------
if ! command -v python3 >/dev/null 2>&1; then
  if ! command -v python >/dev/null 2>&1; then
    log "[ERROR] Python 3 не найден в системе."
    exit 1
  else
    PYTHON_BIN="python"
  fi
else
  PYTHON_BIN="python3"
fi

log "[INFO] Using global python: ${PYTHON_BIN}"

# -------------------------------------------------------------
#  2. Создаем venv
# -------------------------------------------------------------
if [ ! -f "${ROOT}/.venv/bin/python" ]; then
  log "[1/6] Creating virtual environment..."
  "${PYTHON_BIN}" -m venv "${ROOT}/.venv" >> "$LOGFILE" 2>&1
else
  log "[1/6] Virtual environment already exists"
fi

# Активируем venv
source "${ROOT}/.venv/bin/activate"
PY=python

log "[INFO] Using venv python: $(which python)"

# -------------------------------------------------------------
#  3. Устанавливаем зависимости
# -------------------------------------------------------------
log "[2/6] Installing dependencies..."
$PY -m pip install --upgrade pip >> "$LOGFILE" 2>&1
$PY -m pip install -r "${ROOT}/requirements.txt" >> "$LOGFILE" 2>&1

# -------------------------------------------------------------
#  4. Устанавливаем MCP-серверы (editable)
# -------------------------------------------------------------
log "[3/6] Installing MCP servers (editable)..."

$PY -m pip install -e "${ROOT}/mcp-servers/git-mcp-server" >> "$LOGFILE" 2>&1 || \
  log "[WARN] Failed to install git-mcp-server"

$PY -m pip install -e "${ROOT}/mcp-servers/confluence-mcp-server" >> "$LOGFILE" 2>&1 || \
  log "[WARN] Failed to install confluence-mcp-server"

$PY -m pip install -e "${ROOT}/mcp-servers/vector-mcp-server" >> "$LOGFILE" 2>&1 || \
  log "[WARN] Failed to install vector-mcp-server"

# -------------------------------------------------------------
#  5. Загружаем .env
#     Убираем кавычки вокруг значений
# -------------------------------------------------------------
if [ -f "${ROOT}/.env" ]; then
  log "[4/6] Loading .env..."

  while IFS='=' read -r key val; do
    [[ "$key" =~ ^#.*$ ]] && continue
    [[ -z "$key" ]] && continue

    clean_val=$(echo "$val" | sed 's/^"//; s/"$//; s/^'\''//; s/'\''$//')
    export "$key=$clean_val"
    echo "[ENV] $key=$clean_val" >> "$LOGFILE"
  done < "${ROOT}/.env"

else
  log "[4/6] .env not found, skipping..."
fi

# -------------------------------------------------------------
#  6. Генерация демо-данных
# -------------------------------------------------------------
log "[5/6] Seeding demo data..."
$PY -m scripts.seed_demo_data >> "$LOGFILE" 2>&1 || {
  log "[ERROR] seed_demo_data failed."
  exit 1
}

# -------------------------------------------------------------
#  7. Старт MCP-серверов (в фоне)
# -------------------------------------------------------------
log ""
log "============================================"
log "  Starting MCP servers (background)"
log "============================================"

# Git
$PY -m mcp_git.server >> "$LOGFILE" 2>&1 &

# Confluence
$PY -m mcp_confluence.server >> "$LOGFILE" 2>&1 &

# Vector
$PY -m mcp_vector.server >> "$LOGFILE" 2>&1 &

log "[INFO] MCP servers started."

# -------------------------------------------------------------
#  8. Запускаем UI
# -------------------------------------------------------------
log ""
log "========================================================================"
log "  Starting Gradio UI"
log "  Available at: http://localhost:${DOCOPS_GRADIO_PORT:-7860}"
log "  Log: ${LOGFILE}"
log "========================================================================"

cd "$ROOT"
$PY -m app.main >> "$LOGFILE" 2>&1

log "[INFO] app.main exited."