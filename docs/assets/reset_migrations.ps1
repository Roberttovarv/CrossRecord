Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = (Resolve-Path (Join-Path $scriptDir "..\\..")).Path

Set-Location $projectRoot

$dbPath = Join-Path $projectRoot "src\\instance\\mi_base.db"
$migrationsPath = Join-Path $projectRoot "migrations"

Write-Host "Project root: $projectRoot"

if (Test-Path $dbPath) {
    Write-Host "Removing database: $dbPath"
    Remove-Item $dbPath -Force
} else {
    Write-Host "Database not found, skipping: $dbPath"
}

if (Test-Path $migrationsPath) {
    Write-Host "Removing migrations folder: $migrationsPath"
    Remove-Item $migrationsPath -Recurse -Force
} else {
    Write-Host "Migrations folder not found, skipping: $migrationsPath"
}

Write-Host "Recreating migrations..."
python -m flask --app manage.py db init
python -m flask --app manage.py db migrate -m "reset"
python -m flask --app manage.py db upgrade

Write-Host "Database and migrations reset completed."
