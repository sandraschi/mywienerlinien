@echo off
setlocal enabledelayedexpansion

:: Set environment variables
set PGPASSWORD=wienerlinien
set PGHOST=db
set PGUSER=wienerlinien
set PGDATABASE=wienerlinien
set PGPORT=5432

:: Wait for PostgreSQL to be ready
echo Waiting for PostgreSQL to be ready...
:check_postgres
psql -c "SELECT 1" > nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo PostgreSQL is not ready yet. Retrying in 5 seconds...
    timeout /t 5 > nul
    goto check_postgres
)

echo Creating database schema...
psql -f db\init-scripts\01_init_db.sql

:: Install Python dependencies if needed
echo Installing Python dependencies...
pip install -r requirements-db.txt

:: Load GTFS data
echo Loading GTFS data...
python scripts\load_gtfs_to_db.py scripts\gtfs_data\gtfs.zip

echo GTFS data loading completed successfully!

endlocal
