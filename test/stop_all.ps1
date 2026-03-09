# stop_all.ps1 - Stop all services (Docker containers and applications)
# Usage: ./stop_all.ps1

$ErrorActionPreference = "Continue"

Write-Host "Stopping SODA Contexture services..." -ForegroundColor Cyan

Write-Host "`nStopping Docker containers..." -ForegroundColor Yellow

# Stop containers
$containers = @("prometheus", "mongodb")

foreach ($container in $containers) {
    $exists = & docker ps -a -q -f "name=$container" 2>$null
    if ($exists) {
        Write-Host "  Stopping $container..." -ForegroundColor Cyan
        & docker stop $container 2>$null | Out-Null
        & docker rm $container 2>$null | Out-Null
        Write-Host "  Removed $container." -ForegroundColor Green
    }
}

Write-Host "`nDocker containers stopped." -ForegroundColor Green
Write-Host "Note: Terminal tabs remain open. Close them manually or type 'exit'" -ForegroundColor Gray
Write-Host ""
