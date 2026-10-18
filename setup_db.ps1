# setup_db.ps1
# PowerShell script to download, configure, and run portable PostgreSQL 16 + pgvector on Windows

$baseDir = "C:\Users\nafee\.gemini\antigravity\postgresql"
$pgsqlDir = "$baseDir\pgsql"
$dataDir = "$baseDir\data"
$logFile = "$baseDir\pgsql.log"

$pgUrl = "https://get.enterprisedb.com/postgresql/postgresql-16.1-1-windows-x64-binaries.zip"
$vectorUrl = "https://github.com/andreiramani/pgvector_pgsql_windows/releases/download/0.8.1_16/vector.v0.8.1-pg16.zip"

$pgZip = "$baseDir\postgresql-16.1-1-windows-x64-binaries.zip"
$vectorZip = "$baseDir\vector.v0.8.1-pg16.zip"

# Ensure base directory exists
if (!(Test-Path $baseDir)) {
    Write-Host "Creating base directory: $baseDir" -ForegroundColor Cyan
    New-Item -ItemType Directory -Path $baseDir | Out-Null
}

# 1. Download and extract PostgreSQL
if (!(Test-Path "$pgsqlDir\bin\pg_ctl.exe")) {
    Write-Host "Downloading PostgreSQL 16.1 using curl with retries..." -ForegroundColor Cyan
    # Added retry options to handle transient connection resets
    & curl.exe -L --retry 5 --retry-delay 3 --retry-max-time 120 -o $pgZip $pgUrl
    if ($LASTEXITCODE -ne 0 -or !(Test-Path $pgZip)) {
        Write-Error "Failed to download PostgreSQL zip."
        exit 1
    }
    
    Write-Host "Extracting PostgreSQL using tar..." -ForegroundColor Cyan
    & tar.exe -xf $pgZip -C $baseDir
    if ($LASTEXITCODE -ne 0 -or !(Test-Path "$pgsqlDir\bin\pg_ctl.exe")) {
        Write-Error "Failed to extract PostgreSQL binaries."
        exit 1
    }
    
    # Clean up zip
    Remove-Item $pgZip
    Write-Host "PostgreSQL extracted successfully." -ForegroundColor Green
} else {
    Write-Host "PostgreSQL binaries already present." -ForegroundColor Green
}

# 2. Download and install pgvector
if (!(Test-Path "$pgsqlDir\lib\vector.dll")) {
    Write-Host "Downloading precompiled pgvector v0.8.1 using curl with retries..." -ForegroundColor Cyan
    & curl.exe -L --retry 5 --retry-delay 3 -o $vectorZip $vectorUrl
    if ($LASTEXITCODE -ne 0 -or !(Test-Path $vectorZip)) {
        Write-Error "Failed to download pgvector zip."
        exit 1
    }
    
    Write-Host "Extracting pgvector..." -ForegroundColor Cyan
    $tempVectorDir = "$baseDir\temp_vector"
    if (Test-Path $tempVectorDir) { Remove-Item -Recurse -Force $tempVectorDir }
    New-Item -ItemType Directory -Path $tempVectorDir | Out-Null
    
    & tar.exe -xf $vectorZip -C $tempVectorDir
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to extract pgvector."
        exit 1
    }
    
    Write-Host "Copying pgvector files..." -ForegroundColor Cyan
    # Ensure destination paths exist
    if (!(Test-Path "$pgsqlDir\lib")) { New-Item -ItemType Directory -Path "$pgsqlDir\lib" | Out-Null }
    if (!(Test-Path "$pgsqlDir\share\extension")) { New-Item -ItemType Directory -Path "$pgsqlDir\share\extension" | Out-Null }
    
    $dllSource = Get-ChildItem -Path $tempVectorDir -Filter "vector.dll" -Recurse | Select-Object -First 1
    if ($dllSource) {
        Copy-Item -Path $dllSource.FullName -Destination "$pgsqlDir\lib\" -Force
    } else {
        Write-Error "Could not find vector.dll in extracted files."
        exit 1
    }
    
    $extensionFiles = Get-ChildItem -Path $tempVectorDir -Filter "vector*" -Recurse | Where-Object { $_.Extension -eq ".control" -or $_.Extension -eq ".sql" }
    foreach ($file in $extensionFiles) {
        Copy-Item -Path $file.FullName -Destination "$pgsqlDir\share\extension\" -Force
    }
    
    # Clean up temp files
    Remove-Item -Recurse -Force $tempVectorDir
    Remove-Item $vectorZip
    Write-Host "pgvector installed successfully." -ForegroundColor Green
} else {
    Write-Host "pgvector binaries already present." -ForegroundColor Green
}

# 3. Initialize Database Cluster if data directory does not exist
if (!(Test-Path "$dataDir\PG_VERSION")) {
    Write-Host "Initializing PostgreSQL database cluster..." -ForegroundColor Cyan
    & "$pgsqlDir\bin\initdb.exe" -D $dataDir -U postgres -A trust
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to initialize database cluster."
        exit 1
    }
} else {
    Write-Host "Database cluster is already initialized." -ForegroundColor Green
}

# 4. Start PostgreSQL server
$isRunning = Get-Process -Name postgres -ErrorAction SilentlyContinue
if (!$isRunning) {
    Write-Host "Starting PostgreSQL server on port 5432..." -ForegroundColor Cyan
    & "$pgsqlDir\bin\pg_ctl.exe" -D $dataDir -l $logFile start
    Start-Sleep -Seconds 3
} else {
    Write-Host "PostgreSQL server is already running." -ForegroundColor Green
}

# Verify it is running
$checkRunning = Get-Process -Name postgres -ErrorAction SilentlyContinue
if (!$checkRunning) {
    Write-Error "PostgreSQL failed to start. Check logs at $logFile"
    exit 1
}

# 5. Create 'studyplan' database if it doesn't exist
Write-Host "Checking studyplan database..." -ForegroundColor Cyan
$dbExists = & "$pgsqlDir\bin\psql.exe" -U postgres -d postgres -t -c "SELECT 1 FROM pg_database WHERE datname='studyplan';"
if ($dbExists -notmatch "1") {
    Write-Host "Creating studyplan database..." -ForegroundColor Cyan
    & "$pgsqlDir\bin\createdb.exe" -U postgres studyplan
} else {
    Write-Host "Database studyplan already exists." -ForegroundColor Green
}

# 6. Enable pgvector extension
Write-Host "Enabling pgvector extension in studyplan database..." -ForegroundColor Cyan
& "$pgsqlDir\bin\psql.exe" -U postgres -d studyplan -c "CREATE EXTENSION IF NOT EXISTS vector;"
if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to enable pgvector extension in studyplan database."
    exit 1
}

Write-Host "PostgreSQL database and pgvector are ready and running!" -ForegroundColor Green
