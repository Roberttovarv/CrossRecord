[CmdletBinding()]
param(
    [ValidateSet('catalog', 'demo', 'all')]
    [string]$Action = 'all'
)

$ErrorActionPreference = 'Stop'
$env:MONGO_URI = 'mongodb://127.0.0.1:27017/?replicaSet=rs0'
$env:MONGO_DATABASE = 'crossrecord_local'

function Invoke-PythonScript([string]$script, [string[]]$arguments = @()) {
    & pipenv run python $script @arguments
    if ($LASTEXITCODE -ne 0) { throw "$script failed with exit code $LASTEXITCODE" }
}

function Seed-Catalog {
    Invoke-PythonScript 'scripts/seed_crossfit_catalog.py'
}

function Ensure-LocalRobert {
    if (-not $env:CROSSRECORD_LOCAL_ROBERT_PASSWORD) {
        throw 'Set CROSSRECORD_LOCAL_ROBERT_PASSWORD before running a demo seed. This is a local-only password for the premium robert account.'
    }
    $env:CROSSRECORD_PROVISION_PASSWORD = $env:CROSSRECORD_LOCAL_ROBERT_PASSWORD
    Invoke-PythonScript 'scripts/provision_premium_user.py' @(
        '--email', 'roberttovarv@gmail.com',
        '--username', 'robert',
        '--name', 'Robert',
        '--last-name', 'Tovar'
    )
    Remove-Item Env:CROSSRECORD_PROVISION_PASSWORD -ErrorAction SilentlyContinue
}

switch ($Action) {
    'catalog' { Seed-Catalog }
    'demo' {
        Seed-Catalog
        Ensure-LocalRobert
        Invoke-PythonScript 'scripts/seed_demo_data.py'
    }
    'all' {
        Seed-Catalog
        Ensure-LocalRobert
        Invoke-PythonScript 'scripts/seed_demo_data.py'
    }
}

Write-Host "Seed completed in local database '$env:MONGO_DATABASE'."
