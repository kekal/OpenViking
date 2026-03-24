@echo off
REM ============================================================
REM  down.bat — Stop Ollama + OpenViking stack (Windows)
REM ============================================================

echo === Stopping OpenViking Stack ===

REM --- Stop OpenViking server ---
echo [1/2] Stopping OpenViking...
taskkill /f /im openviking-server.exe >nul 2>&1
for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":1933.*LISTENING" 2^>nul') do (
    taskkill /f /pid %%p >nul 2>&1
)
curl -s http://localhost:1933/health >nul 2>&1
if %errorlevel%==0 (
    echo       WARNING: OpenViking still running!
) else (
    echo       OpenViking stopped.
)

REM --- Stop Ollama (kill tray app first so it doesn't respawn) ---
echo [2/2] Stopping Ollama...
taskkill /f /im "ollama app.exe" >nul 2>&1
timeout /t 1 /nobreak >nul
taskkill /f /im ollama.exe >nul 2>&1
curl -s http://localhost:11434/ >nul 2>&1
if %errorlevel%==0 (
    echo       WARNING: Ollama still running!
) else (
    echo       Ollama stopped.
)

echo.
echo === Stack is DOWN ===
