[CmdletBinding()]
param(
    [ValidateSet('up', 'down', 'status')]
    [string]$Action = 'up'
)

$ErrorActionPreference = 'Stop'
$port = 27018
$replicaSet = 'rs0'
$storageRoot = Join-Path $env:LOCALAPPDATA 'CrossRecord\mongodb'
$dataPath = Join-Path $storageRoot 'data'
$logPath = Join-Path $storageRoot 'mongod.log'
$pidPath = Join-Path $storageRoot 'mongod.pid'

function Get-MongodPath {
    if ($env:MONGOD_PATH -and (Test-Path -LiteralPath $env:MONGOD_PATH)) {
        return (Resolve-Path -LiteralPath $env:MONGOD_PATH).Path
    }
    $command = Get-Command mongod -ErrorAction SilentlyContinue
    if ($command) { return $command.Source }
    $installed = Get-ChildItem -Path (Join-Path $env:ProgramFiles 'MongoDB\Server\*\bin\mongod.exe') -ErrorAction SilentlyContinue |
        Sort-Object FullName -Descending | Select-Object -First 1
    if ($installed) { return $installed.FullName }
    throw "MongoDB Server is not installed or not on PATH. Install MongoDB Community Server, then reopen PowerShell. You can also set MONGOD_PATH to mongod.exe."
}

function Get-MongoshPath {
    $command = Get-Command mongosh -ErrorAction SilentlyContinue
    if ($command) { return $command.Source }
    $installed = Get-ChildItem -Path (Join-Path $env:ProgramFiles 'MongoDB\mongosh\*\bin\mongosh.exe') -ErrorAction SilentlyContinue |
        Sort-Object FullName -Descending | Select-Object -First 1
    if ($installed) { return $installed.FullName }
    throw "MongoDB Shell (mongosh) is required to initialise the local replica set. Install it, then reopen PowerShell."
}

function Test-MongoPort {
    return (Test-NetConnection -ComputerName '127.0.0.1' -Port $port -InformationLevel Quiet -WarningAction SilentlyContinue)
}

function Start-LocalMongo {
    # Validate both executables before spawning a background server.
    $mongosh = Get-MongoshPath
    if (Test-MongoPort) {
        Write-Host "MongoDB is already listening on 127.0.0.1:$port."
    } else {
        $mongod = Get-MongodPath
        New-Item -ItemType Directory -Force -Path $dataPath | Out-Null
        New-Item -ItemType Directory -Force -Path $storageRoot | Out-Null
        $process = Start-Process -FilePath $mongod -ArgumentList @(
            '--dbpath', $dataPath,
            '--replSet', $replicaSet,
            '--bind_ip', '127.0.0.1',
            '--port', "$port",
            '--logpath', $logPath,
            '--logappend'
        ) -WindowStyle Hidden -PassThru
        Set-Content -LiteralPath $pidPath -Value $process.Id -NoNewline
        for ($attempt = 0; $attempt -lt 20 -and -not (Test-MongoPort); $attempt++) {
            Start-Sleep -Seconds 1
        }
        if (-not (Test-MongoPort)) {
            throw "MongoDB did not start. Review the log at $logPath"
        }
        Write-Host "MongoDB started (PID $($process.Id))."
    }

    $initialise = "try { rs.status().ok } catch (error) { rs.initiate({_id:'$replicaSet',members:[{_id:0,host:'127.0.0.1:$port'}]}) }"
    & $mongosh --quiet --host 127.0.0.1 --port $port --eval $initialise | Out-Null
    for ($attempt = 0; $attempt -lt 20; $attempt++) {
        $primary = & $mongosh --quiet --host 127.0.0.1 --port $port --eval "db.hello().isWritablePrimary" 2>$null
        if ($primary.Trim() -eq 'true') {
            Write-Host "Local MongoDB replica set '$replicaSet' is ready."
            Write-Host "URI: mongodb://127.0.0.1:$port/?replicaSet=$replicaSet"
            return
        }
        Start-Sleep -Seconds 1
    }
    throw "MongoDB started but did not become primary. Review the log at $logPath"
}

function Stop-LocalMongo {
    if (-not (Test-Path -LiteralPath $pidPath)) {
        Write-Host 'No CrossRecord local MongoDB PID file was found; nothing was stopped.'
        return
    }
    $processId = [int](Get-Content -LiteralPath $pidPath -Raw)
    $process = Get-Process -Id $processId -ErrorAction SilentlyContinue
    if ($process -and $process.ProcessName -eq 'mongod') {
        Stop-Process -Id $processId
        Write-Host "Stopped CrossRecord local MongoDB (PID $processId)."
    } else {
        Write-Host 'The recorded MongoDB process is no longer running; removed the stale PID file.'
    }
    Remove-Item -LiteralPath $pidPath -Force
}

switch ($Action) {
    'up' { Start-LocalMongo }
    'down' { Stop-LocalMongo }
    'status' {
        if (Test-MongoPort) {
            Write-Host "MongoDB is listening on 127.0.0.1:$port."
        } else {
            Write-Host "MongoDB is not listening on 127.0.0.1:$port."
            exit 1
        }
    }
}
