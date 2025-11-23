@echo off
chcp 65001 >nul
setlocal ENABLEDELAYEDEXPANSION

REM --- Определяем корень проекта ---
set ROOT=%~dp0
set ROOT=%ROOT:"=%

REM --- Лог-файл ---
set LOGFILE=%ROOT%run_all.log

REM --- Перезаписываем лог при каждом запуске ---
echo ============================================ > "%LOGFILE%"
echo DocOps MCP Assistant — RUN LOG >> "%LOGFILE%"
echo Started at %DATE% %TIME% >> "%LOGFILE%"
echo ROOT = %ROOT% >> "%LOGFILE%"
echo ============================================ >> "%LOGFILE%"
echo. >> "%LOGFILE%"

REM --- Сразу уходим в main, чтобы не провалиться в :log ---
goto :main


:log
REM --- Пишем и в консоль, и в лог ---
echo %*
echo %*>> "%LOGFILE%"
goto :eof


:main
call :log "============================================"
call :log "  DocOps MCP Assistant — FULL START"
call :log "  ROOT = %ROOT%"
call :log "  LOG  = %LOGFILE%"
call :log "============================================"

REM --- Проверяем, доступен ли py/python ---
where py >nul 2>nul
if %ERRORLEVEL% neq 0 (
    where python >nul 2>nul
    if %ERRORLEVEL% neq 0 (
        call :log "[ERROR] 'py' or 'python' is not found in PATH."
        call :log "УInstall Python 3 and make 'Add to PATH'."
        pause
        exit /b 1
    ) else (
        set GLOBAL_PY=python
    )
) else (
    set GLOBAL_PY=py -3
)

call :log "[INFO] Let's use global interpreter: %GLOBAL_PY%"

REM --- Создаем venv, если его еще нет ---
if not exist "%ROOT%.venv\Scripts\python.exe" (
    call :log "[1/6] Creating virtual environment using %GLOBAL_PY% ..."
    %GLOBAL_PY% -m venv "%ROOT%.venv" >> "%LOGFILE%" 2>&1
) else (
    call :log "[1/6] Virtual environment already exists, skipping creation."
)

REM --- Путь до python в venv ---
set PY=%ROOT%.venv\Scripts\python.exe

if not exist "%PY%" (
    call :log "[ERROR] %PY% is not found"
    call :log "Virtual environment wasn't created or was deleted"
    call :log "Try to execute this command:   %GLOBAL_PY% -m venv .venv"
    pause
    exit /b 1
)

call :log "[INFO] Using venv python: %PY%"

REM --- Установка зависимостей ---
call :log "[2/6] Installing dependencies from requirements.txt ..."
"%PY%" -m pip install --upgrade pip >> "%LOGFILE%" 2>&1
if %ERRORLEVEL% neq 0 (
    call :log "[ERROR] pip upgrade failed. See more in %LOGFILE%"
    pause
    exit /b 1
)

"%PY%" -m pip install -r "%ROOT%requirements.txt" >> "%LOGFILE%" 2>&1
if %ERRORLEVEL% neq 0 (
    call :log "[ERROR] Installing root dependencies failed. See more in %LOGFILE%"
    pause
    exit /b 1
)

REM --- Установка MCP-серверов (editable) ---
call :log "[3/6] Installing MCP servers (editable)..."
"%PY%" -m pip install -e "%ROOT%mcp-servers\git-mcp-server" >> "%LOGFILE%" 2>&1
if %ERRORLEVEL% neq 0 (
    call :log "[WARN] Failed to install git-mcp-server in editable mode. See more in %LOGFILE%"
)

"%PY%" -m pip install -e "%ROOT%mcp-servers\confluence-mcp-server" >> "%LOGFILE%" 2>&1
if %ERRORLEVEL% neq 0 (
    call :log "[WARN] Failed to install confluence-mcp-server in editable mode. See more in %LOGFILE%"
)

"%PY%" -m pip install -e "%ROOT%mcp-servers\vector-mcp-server" >> "%LOGFILE%" 2>&1
if %ERRORLEVEL% neq 0 (
    call :log "[WARN] Failed to install vector-mcp-server in editable mode. See more in %LOGFILE%"
)

REM --- Подхватываем .env (формат: KEY=VAL, без пробелов вокруг '=') ---
if exist "%ROOT%.env" (
    call :log "[4/6] Loading .env ..."
    for /f "usebackq tokens=1,* delims==" %%a in ("%ROOT%.env") do (
        if NOT "%%a"=="" (
            if NOT "%%a"=="#" (
                set "%%a=%%b"
                echo [ENV] %%a=%%b>> "%LOGFILE%"
            )
        )
    )
) else (
    call :log "[4/6] .env not found, skipping..."
)

REM --- Генерим демо-данные ---
call :log "[5/6] Seeding demo data..."
"%PY%" -m scripts.seed_demo_data >> "%LOGFILE%" 2>&1
if %ERRORLEVEL% neq 0 (
    call :log "[ERROR] seed_demo_data failed. См. %LOGFILE%"
    pause
    exit /b 1
)

call :log ""
call :log "============================================"
call :log "  Starting MCP servers in separate windows"
call :log "============================================"


REM --- Запускаем MCP-сервера в отдельных окнах ---
start "MCP-GIT" "%PY%" -m mcp_git.server
start "MCP-CONFLUENCE" "%PY%" -m mcp_confluence.server
start "MCP-VECTOR" "%PY%" -m mcp_vector.server

call :log ""
call :log "============================================"
call :log "  Starting Gradio UI (main app)"
call :log "  Open: http://localhost:%DOCOPS_GRADIO_PORT%"
call :log "  Log:  %LOGFILE%"
call :log "============================================"

cd /d "%ROOT%"
"%PY%" -m app.main >> "%LOGFILE%" 2>&1

call :log "[INFO] app.main exited. See more in logs."
pause

endlocal