@echo off
REM stop_all.bat - Stop all services (Docker containers)
REM Usage: stop_all.bat

setlocal enabledelayedexpansion

echo.
echo Stopping SODA Contexture services...
echo.
echo Stopping Docker containers...

set "containers=prometheus" "mongodb"

for %%C in (%containers%) do (
    echo   Stopping %%C...
    docker stop %%C >nul 2>&1
    docker rm %%C >nul 2>&1
)

echo.
echo Docker containers stopped.
echo Note: Terminal windows remain open. Close them manually or press Ctrl+C
echo.
pause
