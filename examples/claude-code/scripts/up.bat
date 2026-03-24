@echo off
REM ============================================================
REM  up.bat — Start Ollama + OpenViking stack (Windows)
REM
REM  Prerequisites:
REM    - Ollama installed (https://ollama.com)
REM    - OpenViking installed (pip install openviking)
REM    - nomic-embed-text model pulled (ollama pull nomic-embed-text)
REM    - Config files in %USERPROFILE%\.openviking\
REM    - start-server.vbs in the same directory as this script
REM ============================================================

echo === Starting OpenViking Stack ===

REM --- Start Ollama ---
echo [1/3] Starting Ollama...
tasklist /fi "imagename eq ollama.exe" 2>nul | find /i "ollama.exe" >nul
if %errorlevel%==0 (
    echo       Ollama already running.
) else (
    start "" "%LOCALAPPDATA%\Programs\Ollama\ollama app.exe"
    echo       Waiting for Ollama...
    :wait_ollama
    curl -s http://localhost:11434/ >nul 2>&1
    if %errorlevel% neq 0 (
        timeout /t 1 /nobreak >nul
        goto wait_ollama
    )
    echo       Ollama is ready.
)

REM --- Start OpenViking server (background, hidden window) ---
echo [2/3] Starting OpenViking server...
curl -s http://localhost:1933/health >nul 2>&1
if %errorlevel%==0 (
    echo       OpenViking already running.
    goto :done
)
wscript //nologo "%~dp0start-server.vbs"
echo       Waiting for OpenViking...
set /a attempts=0
:wait_viking
set /a attempts+=1
if %attempts% gtr 30 (
    echo       ERROR: OpenViking failed to start after 60s.
    echo       Check %USERPROFILE%\.openviking\server.log
    goto :done
)
curl -s http://localhost:1933/health >nul 2>&1
if %errorlevel% neq 0 (
    timeout /t 2 /nobreak >nul
    goto wait_viking
)
echo       OpenViking is ready.

:done
echo.
echo [3/3] Setting Ollama to low priority...
:: Trigger model load with a dummy embedding, then set priority on ALL ollama processes
curl -s -X POST http://localhost:11434/v1/embeddings -H "Content-Type: application/json" -d "{\"model\":\"nomic-embed-text\",\"input\":\"warmup\"}" >nul 2>&1
timeout /t 2 /nobreak >nul
powershell -NoProfile -Command "Get-Process -Name 'ollama*','ollama app*' -ErrorAction SilentlyContinue | ForEach-Object { $_.PriorityClass = 'Idle' }"
echo       Ollama priority set to idle.

echo.
echo === Stack is UP ===
echo   Ollama:     http://localhost:11434
echo   OpenViking: http://localhost:1933
echo   Logs:       %USERPROFILE%\.openviking\server.log
