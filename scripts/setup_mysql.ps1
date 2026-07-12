param(
    [string]$User = "root",
    [string]$HostName = "localhost",
    [string]$SchemaPath = "$PSScriptRoot\..\schema.sql"
)

if (-not (Test-Path -LiteralPath $SchemaPath)) {
    Write-Error "Schema file not found: $SchemaPath"
    exit 1
}

mysql -h $HostName -u $User -p --default-character-set=utf8mb4 -e "source $SchemaPath"
