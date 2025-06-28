@echo off
setlocal enabledelayedexpansion

echo Starting GTFS processor...
set PYTHONUNBUFFERED=1

python -u scripts/process_gtfs.py > scripts\gtfs_processor.log 2>&1

echo Script execution completed. Check scripts\gtfs_processor.log for details.
pause
