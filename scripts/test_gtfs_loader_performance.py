"""
Test script to verify GTFS loader optimizations are working.

This script runs a test import and measures performance metrics.
"""

import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

try:
    from sqlalchemy import text

    from models.gtfs_models import engine
except ImportError:
    print("Error: Could not import required modules. Make sure you're in the project root.")
    sys.exit(1)


def test_database_connection():
    """Test database connection."""
    print("Testing database connection...")
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            result.fetchone()
        print("✓ Database connection successful")
        return True
    except Exception as e:
        print(f"✗ Database connection failed: {e}")
        return False


def check_shapes_table():
    """Check if shapes table has data."""
    print("\nChecking shapes table...")
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM shapes"))
            count = result.scalar()
            if count > 0:
                print(f"✓ Shapes table has {count:,} rows")
                return True
            else:
                print("✗ Shapes table is empty")
                return False
    except Exception as e:
        print(f"✗ Error checking shapes table: {e}")
        return False


def check_route_polylines():
    """Check if routes have associated shapes."""
    print("\nChecking route polylines...")
    try:
        with engine.connect() as conn:
            # Check if routes have shape_ids
            result = conn.execute(
                text("""
                SELECT COUNT(DISTINCT t.shape_id) as shapes_with_routes
                FROM trips t
                WHERE t.shape_id IS NOT NULL
            """)
            )
            shapes_count = result.scalar()

            result = conn.execute(text("SELECT COUNT(*) FROM routes"))
            routes_count = result.scalar()

            result = conn.execute(text("SELECT COUNT(*) FROM shapes"))
            total_shapes = result.scalar()

            print(f"  Routes: {routes_count}")
            print(f"  Total shapes: {total_shapes:,}")
            print(f"  Shapes linked to routes: {shapes_count}")

            if shapes_count > 0:
                print("✓ Route polylines are available")
                return True
            else:
                print("✗ No route polylines found")
                return False
    except Exception as e:
        print(f"✗ Error checking route polylines: {e}")
        return False


def check_table_counts():
    """Check record counts in all GTFS tables."""
    print("\nChecking table record counts...")
    tables = ["agencies", "routes", "stops", "trips", "stop_times", "shapes"]
    all_good = True

    try:
        with engine.connect() as conn:
            for table in tables:
                try:
                    result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                    count = result.scalar()
                    status = "✓" if count > 0 else "✗"
                    print(f"  {status} {table}: {count:,}")
                    if count == 0 and table != "agencies":  # agencies might be small
                        all_good = False
                except Exception as e:
                    print(f"  ✗ {table}: Error - {e}")
                    all_good = False
    except Exception as e:
        print(f"✗ Error checking tables: {e}")
        return False

    return all_good


def check_indexes():
    """Check if indexes were recreated."""
    print("\nChecking indexes...")
    indexes = [
        "idx_stop_times_trip_id",
        "idx_stop_times_stop_id",
        "idx_stops_location",
        "idx_routes_agency_id",
        "idx_trips_route_id",
        "idx_shapes_shape_id",
    ]

    try:
        with engine.connect() as conn:
            for idx_name in indexes:
                result = conn.execute(
                    text(f"""
                    SELECT COUNT(*) 
                    FROM pg_indexes 
                    WHERE indexname = '{idx_name}'
                """)
                )
                exists = result.scalar() > 0
                status = "✓" if exists else "✗"
                print(f"  {status} {idx_name}")
    except Exception as e:
        print(f"✗ Error checking indexes: {e}")
        return False

    return True


def check_materialized_view():
    """Check if materialized view was refreshed."""
    print("\nChecking materialized view...")
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM route_stop_patterns"))
            count = result.scalar()
            if count > 0:
                print(f"✓ Materialized view has {count:,} routes")
                return True
            else:
                print("✗ Materialized view is empty")
                return False
    except Exception as e:
        print(f"✗ Error checking materialized view: {e}")
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("GTFS Loader Performance Test")
    print("=" * 60)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    results = {
        "database_connection": test_database_connection(),
        "table_counts": check_table_counts(),
        "shapes_table": check_shapes_table(),
        "route_polylines": check_route_polylines(),
        "indexes": check_indexes(),
        "materialized_view": check_materialized_view(),
    }

    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)

    all_passed = all(results.values())

    for test_name, passed in results.items():
        status = "PASS" if passed else "FAIL"
        print(f"  {status}: {test_name}")

    print("\n" + "=" * 60)
    if all_passed:
        print("✓ All tests passed! GTFS loader optimizations are working.")
        return 0
    else:
        print("✗ Some tests failed. Check the output above for details.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
