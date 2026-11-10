$env:PGUSER = if ($env:PGUSER) { $env:PGUSER } else { "postgres" }
$env:PGPASSWORD = if ($env:PGPASSWORD) { $env:PGPASSWORD } else { "postgres" }
$env:PGHOST = if ($env:PGHOST) { $env:PGHOST } else { "localhost" }
$env:PGPORT = if ($env:PGPORT) { $env:PGPORT } else { "5432" }
$env:PGDATABASE = if ($env:PGDATABASE) { $env:PGDATABASE } else { "perpustakaan_digital" }
$mongoUri = if ($env:MONGO_URI) { $env:MONGO_URI } else { "mongodb://localhost:27017/perpustakaan_digital" }

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

psql -h $env:PGHOST -p $env:PGPORT -U $env:PGUSER -f "$scriptDir\postgresql_schema.sql"

mongosh "$mongoUri" "$scriptDir\mongodb_schema.js"
