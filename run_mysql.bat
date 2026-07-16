@echo off
set PATH=C:\Program Files\Docker\Docker\resources\bin;%PATH%
REM ============================================================================
REM  SODA Contexture — MySQL Agent Stack Launcher
REM  Usage:
REM    run_mysql.bat up       Build and start all containers
REM    run_mysql.bat down     Stop and remove containers
REM    run_mysql.bat logs     Tail logs from all containers
REM    run_mysql.bat shell    Open a MySQL client shell
REM    run_mysql.bat init     Re-run the SQL init script against the running DB
REM ============================================================================

set COMPOSE=docker compose -f pkg\agents\mysql\docker-compose.yml

if "%1"=="up" (
    echo [*] Building and starting MySQL agent stack...
    %COMPOSE% up --build -d
    echo.
    echo [*] Waiting for services to be healthy...
    timeout /t 8 /nobreak >nul
    %COMPOSE% ps
    echo.
    echo [*] Stack is ready!
    echo     MySQL native port      : localhost:3306
    echo     MCP Agent SSE endpoint : http://localhost:8005/sse
    goto end
)

if "%1"=="down" (
    echo [*] Stopping MySQL agent stack...
    %COMPOSE% down -v
    goto end
)

if "%1"=="logs" (
    %COMPOSE% logs -f
    goto end
)

if "%1"=="shell" (
    echo [*] Opening MySQL client shell...
    docker exec -it contexture-mysql mysql -uroot -proot
    goto end
)

if "%1"=="init" (
    echo [*] Re-running SQL init script...
    docker exec -i contexture-mysql sh -c "mysql -uroot -proot < /init.sql"
    goto end
)

echo Usage: run_mysql.bat [up ^| down ^| logs ^| shell ^| init]
echo.
echo   up     Build and start all containers (MySQL DB + MCP agent)
echo   down   Stop and clean up all containers and volumes
echo   logs   Tail live container logs
echo   shell  Open an interactive MySQL SQL shell
echo   init   Re-seed the database with sample schema and data

:end
