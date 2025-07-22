#!/bin/bash

# Exit on error
set -e

# Set environment variables
export PGPASSWORD=wienerlinien

# Wait for PostgreSQL to be ready
echo "Waiting for PostgreSQL to be ready..."
until psql -h db -U wienerlinien -d wienerlinien -c "SELECT 1" > /dev/null 2>&1; do
  echo "PostgreSQL is not ready yet. Retrying in 5 seconds..."
  sleep 5
done

# Create database schema
echo "Creating database schema..."
psql -h db -U wienerlinien -d wienerlinien -f /app/db/init-scripts/01_init_db.sql

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -r /app/requirements-db.txt

# Load GTFS data
echo "Loading GTFS data..."
python /app/scripts/load_gtfs_to_db.py /app/scripts/gtfs_data/gtfs.zip

echo "GTFS data loading completed successfully!"
