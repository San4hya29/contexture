# run_all.ps1 - Start all services (Docker containers and application components)
# Usage: ./run_all.ps1

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot

Write-Host "Starting SODA Contexture services..." -ForegroundColor Cyan
Write-Host "Project root: $projectRoot" -ForegroundColor Gray

# ============================================================================
# 0. Pre-flight checks
# ============================================================================
Write-Host "`n[0/6] Running pre-flight checks..." -ForegroundColor Yellow

# Check if prometheus config exists
$prometheusConfig = "$projectRoot\config\prometheus_run_config.yaml"
if (-not (Test-Path $prometheusConfig)) {
    Write-Host "ERROR: Prometheus config not found at: $prometheusConfig" -ForegroundColor Red
    Write-Host "Please ensure the config file exists before running this script." -ForegroundColor Red
    exit 1
}
Write-Host "  ✓ Prometheus config found" -ForegroundColor Green

# Check if Docker is running
$dockerCheck = & docker ps 2>&1
if ($dockerCheck -like "*error*" -or $dockerCheck -like "*Cannot*" -or $dockerCheck -like "*refused*") {
    Write-Host "ERROR: Docker is not running. Please start Docker Desktop." -ForegroundColor Red
    exit 1
}
Write-Host "  ✓ Docker is running" -ForegroundColor Green

# ============================================================================
# 1. Start Docker Containers
# ============================================================================
Write-Host "`n[1/6] Cleaning up existing containers..." -ForegroundColor Yellow

# Stop all containers that might be using our ports
Write-Host "  Stopping any existing Prometheus and MongoDB containers..." -ForegroundColor Gray
@("prometheus", "mongodb") | ForEach-Object {
    & docker ps -a -q --filter "name=$_" 2>$null | ForEach-Object { 
        & docker stop $_ 2>$null | Out-Null
        & docker rm $_ 2>$null | Out-Null
    }
}

# Also try to kill anything on our specific ports
Write-Host "  Freeing ports 9090 and 27017..." -ForegroundColor Gray
Get-NetTCPConnection -LocalPort 9090 -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Get-NetTCPConnection -LocalPort 27017 -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue

# Wait for cleanup
Start-Sleep -Seconds 3

Write-Host "`n[2/6] Starting Prometheus container..." -ForegroundColor Yellow

$prometheusArgs = @(
    "run",
    "-d",
    "--name", "prometheus",
    "-p", "9090:9090",
    "-v", "`"$prometheusConfig`":/etc/prometheus/prometheus.yml",
    "prom/prometheus:latest",
    "--config.file=/etc/prometheus/prometheus.yml",
    "--web.enable-remote-write-receiver"
)

$prometheusResult = & docker @prometheusArgs 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "Prometheus container started (accessible at http://localhost:9090)" -ForegroundColor Green
} else {
    Write-Host "ERROR starting Prometheus: $prometheusResult" -ForegroundColor Red
}

Write-Host "`n[3/6] Starting MongoDB container..." -ForegroundColor Yellow

$mongoArgs = @(
    "run",
    "-d",
    "--name", "mongodb",
    "-e", "MONGO_INITDB_DATABASE=ocs",
    "-p", "27017:27017",
    "mongo:6"
)

$mongoResult = & docker @mongoArgs 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "MongoDB container started (accessible at localhost:27017)" -ForegroundColor Green
} else {
    Write-Host "ERROR starting MongoDB: $mongoResult" -ForegroundColor Red
}

Write-Host "`n[4/6] Waiting for services to be ready..." -ForegroundColor Yellow
Start-Sleep -Seconds 3

# ============================================================================
# 2. Open Terminal Windows for Application Components
# ============================================================================

Write-Host "`n[5/6] Opening terminal tabs..." -ForegroundColor Yellow

# Tab 1: OCS Server (Go)
Write-Host "  - Tab 1: OCS Server (go run ./pkg/ocs/)" -ForegroundColor Cyan
$cmd1 = "cd /d `"$projectRoot`" && title OCS Server && go run ./pkg/ocs/ && pause"
Start-Process cmd.exe -ArgumentList "/k", $cmd1

# Tab 2: Prometheus Data Pusher (Python)
Write-Host "  - Tab 2: Prometheus Data Pusher (python prometheus_data_pusher.py)" -ForegroundColor Cyan
$cmd2 = "cd /d `"$projectRoot\pkg\utils`" && title Prometheus Data Pusher && python prometheus_data_pusher.py --config config.json && pause"
Start-Process cmd.exe -ArgumentList "/k", $cmd2

# Tab 3: FastMCP Server (Python)
Write-Host "  - Tab 3: FastMCP Server (fastmcp run server.py:app)" -ForegroundColor Cyan
$cmd3 = "cd /d `"$projectRoot\pkg\mcp`" && title FastMCP Server && fastmcp run server.py:app --transport http --port 8001 && pause"
Start-Process cmd.exe -ArgumentList "/k", $cmd3

# Tab 4: MCP Client (Python)
Write-Host "  - Tab 4: MCP Client (python client_dynamic.py)" -ForegroundColor Cyan
$cmd4 = "cd /d `"$projectRoot\pkg\mcp`" && title MCP Client && python client_dynamic.py && pause"
Start-Process cmd.exe -ArgumentList "/k", $cmd4

# ============================================================================
# 3. Status Summary
# ============================================================================
Write-Host "`n[6/6] All services started!" -ForegroundColor Green
Write-Host "`n" + ("=" * 70) -ForegroundColor Cyan
Write-Host "SERVICE STATUS:" -ForegroundColor Cyan
Write-Host ("=" * 70) -ForegroundColor Cyan

Write-Host "`n[DOCKER CONTAINERS]" -ForegroundColor Yellow
Write-Host "  • Prometheus:  http://localhost:9090" -ForegroundColor Green
Write-Host "  • MongoDB:     localhost:27017" -ForegroundColor Green

Write-Host "`n[TERMINAL TABS]" -ForegroundColor Yellow
Write-Host "  • Tab 1: OCS Server (Go)" -ForegroundColor Green
Write-Host "  • Tab 2: Prometheus Data Pusher (Python)" -ForegroundColor Green
Write-Host "  • Tab 3: FastMCP Server (Python) - http://localhost:8001" -ForegroundColor Green
Write-Host "  • Tab 4: MCP Client (Python)" -ForegroundColor Green

Write-Host "`n" + ("=" * 70) -ForegroundColor Cyan
Write-Host "STOPPING ALL SERVICES:" -ForegroundColor Yellow
Write-Host "  • Run: stop_all.ps1" -ForegroundColor Cyan
Write-Host "  • Or manually run: docker stop prometheus-contexture mongodb-contexture" -ForegroundColor Cyan
Write-Host ("=" * 70) -ForegroundColor Cyan
Write-Host ""

Write-Host "Press Ctrl+C to stop." -ForegroundColor Gray
