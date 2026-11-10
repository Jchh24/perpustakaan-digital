@echo off
set PGUSER=postgres
set PGPASSWORD=postgres
set PGHOST=localhost
set PGPORT=5432
set PGDATABASE=perpustakaan_digital
set MONGO_URI=mongodb://localhost:27017/perpustakaan_digital

psql -h %PGHOST% -p %PGPORT% -U %PGUSER% -f "%~dp0postgresql_schema.sql"

mongosh "%MONGO_URI%" "%~dp0mongodb_schema.js"
