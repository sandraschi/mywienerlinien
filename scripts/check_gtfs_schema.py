"""
Check GTFS Database Schema

This script examines the GTFS database schema to help diagnose issues with the markdown generator.
"""

import sqlite3
from pathlib import Path
import logging
from typing import Dict, List, Any

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('gtfs_schema_check.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def get_table_info(db_path: str) -> Dict[str, List[Dict[str, Any]]]:
    """Get schema information for all tables."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Get list of tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row['name'] for row in cursor.fetchall()]
    
    schema_info = {}
    
    for table in tables:
        # Get table info
        cursor.execute(f"PRAGMA table_info({table})")
        columns = [dict(row) for row in cursor.fetchall()]
        
        # Get primary key info
        cursor.execute(f"PRAGMA index_list({table})")
        indexes = cursor.fetchall()
        
        # Get foreign key info
        cursor.execute(f"PRAGMA foreign_key_list({table})")
        foreign_keys = cursor.fetchall()
        
        schema_info[table] = {
            'columns': columns,
            'indexes': [dict(row) for row in indexes],
            'foreign_keys': [dict(row) for row in foreign_keys]
        }
    
    conn.close()
    return schema_info

def check_trips_structure(schema_info: Dict[str, Any]) -> None:
    """Check the structure of the trips table."""
    if 'trips' not in schema_info:
        logger.error("No 'trips' table found in the database")
        return
    
    logger.info("\nTrips Table Structure:")
    logger.info("-" * 50)
    
    # Check columns
    columns = schema_info['trips']['columns']
    logger.info("Columns:")
    for col in columns:
        pk = "PRIMARY KEY" if col['pk'] > 0 else ""
        logger.info(f"  - {col['name']} ({col['type']}) {pk}")
    
    # Check primary key
    pk_columns = [col['name'] for col in columns if col['pk'] > 0]
    if pk_columns:
        logger.info("\nPrimary Key Columns:")
        logger.info(f"  - {', '.join(pk_columns)}")
    
    # Check indexes
    indexes = schema_info['trips']['indexes']
    if indexes:
        logger.info("\nIndexes:")
        for idx in indexes:
            logger.info(f"  - {idx['name']} (unique: {idx['unique']})")
    
    # Check foreign keys
    fks = schema_info['trips']['foreign_keys']
    if fks:
        logger.info("\nForeign Keys:")
        for fk in fks:
            logger.info(f"  - {fk['from']} -> {fk['table']}.{fk['to']}")

def main():
    db_path = Path("gtfs_data/gtfs.sqlite")
    
    if not db_path.exists():
        logger.error(f"Database file not found: {db_path}")
        return
    
    logger.info(f"Analyzing GTFS database: {db_path}")
    
    try:
        schema_info = get_table_info(str(db_path))
        check_trips_structure(schema_info)
        
        # Log all tables for reference
        logger.info("\nAll Tables:")
        for table_name in sorted(schema_info.keys()):
            logger.info(f"- {table_name}")
            
    except Exception as e:
        logger.error(f"Error analyzing database: {e}", exc_info=True)

if __name__ == "__main__":
    main()
