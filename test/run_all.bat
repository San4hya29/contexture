@echo off
REM run_all.bat - Start all services (Docker containers and application components)
REM Usage: run_all.bat

setlocal enabledelayedexpansion

REM Get the project root (1 level up from this script)
for %%I in ("%~dp0.") do set "PROJECT_ROOT=%%~fI"

echo.
echo Starting SODA Contexture services...
echo Project root: %PROJECT_ROOT%
echo.

REM ============================================================================
REM 0. Cleanup
REM ============================================================================
echo [0/6] Cleaning up existing containers...
for /f %%C in ('docker ps -a -q --filter name=prometheus 2^>nul') do (
    echo   Stopping %%C...
    docker stop %%C >nul 2>&1
    docker rm %%C >nul 2>&1
)
for /f %%C in ('docker ps -a -q --filter name=mongodb 2^>nul') do (
    echo   Stopping %%C...
    docker stop %%C >nul 2>&1
    docker rm %%C >nul 2>&1
)
timeout /t 2 /nobreak >nul
echo.

REM ============================================================================
REM 1. Start Docker Containers
REM ============================================================================
echo [1/6] Starting Prometheus container...

docker run -d ^
  --name prometheus ^
  -p 9090:9090 ^
  -v "%PROJECT_ROOT%\config\prometheus_run_config.yaml:/etc/prometheus/prometheus.yml" ^
  prom/prometheus:latest ^
  --config.file=/etc/prometheus/prometheus.yml ^
  --web.enable-remote-write-receiver >nul

echo Prometheus container started (accessible at http://localhost:9090)
echo.

echo [2/6] Starting MongoDB container...

docker run -d ^
  --name mongodb ^
  -e MONGO_INITDB_DATABASE=ocs ^
  -p 27017:27017 ^
  mongo:6 >nul

echo MongoDB container started (accessible at localhost:27017)
echo.

echo [3/6] Waiting for services to be ready...
timeout /t 3 /nobreak >nul

REM ============================================================================
REM 2. Open Terminal Windows for Application Components
REM ============================================================================
echo [4/6] Opening terminal windows...

echo   - Window 1: OCS Server (go run ./pkg/ocs/)
start "OCS Server" /D "%PROJECT_ROOT%" cmd /k "cd /d "%PROJECT_ROOT%" && go run ./pkg/ocs/"

echo   - Window 2: Prometheus Data Pusher
timeout /t 1 /nobreak >nul
start "Prometheus Data Pusher" /D "%PROJECT_ROOT%\pkg\utils" cmd /k "cd /d "%PROJECT_ROOT%\pkg\utils" && python prometheus_data_pusher.py --config config.json"

echo   - Window 3: FastMCP Server
timeout /t 1 /nobreak >nul
start "FastMCP Server" /D "%PROJECT_ROOT%\pkg\mcp" cmd /k "cd /d "%PROJECT_ROOT%\pkg\mcp" && fastmcp run server.py:app --transport http --port 8001"

echo   - Window 4: MCP Client
timeout /t 1 /nobreak >nul
start "MCP Client" /D "%PROJECT_ROOT%\pkg\mcp" cmd /k "cd /d "%PROJECT_ROOT%\pkg\mcp" && python client_dynamic.py"

REM ============================================================================
REM 3. Status Summary
REM ============================================================================
echo.
echo [5/6] Opening terminals complete!
echo.
echo [6/6] All services started!
echo.
echo ^===============================================================================
echo SERVICE STATUS:
echo ^===============================================================================
echo.
echo [DOCKER CONTAINERS]
echo   * Prometheus:  http://localhost:9090
echo   * MongoDB:     localhost:27017
echo.
echo [TERMINAL WINDOWS]
echo   * Window 1: OCS Server (Go)
echo   * Window 2: Prometheus Data Pusher (Python)
echo   * Window 3: FastMCP Server (Python) - http://localhost:8001
echo   * Window 4: MCP Client (Python)
echo.
echo ^===============================================================================
echo STOPPING ALL SERVICES:
echo   * Run: stop_all.bat
echo   * Or manually run: docker stop prometheus mongodb
echo ^===============================================================================
echo.
echo Press any key to exit this window...
pause >nul
