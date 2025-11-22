# GTFS Loader Performance Fix

## Problem

The GTFS loader was experiencing severe performance issues, with 5-9 minute delays between data chunks during bulk loading. Analysis of logs revealed:

- **Root Cause**: Database triggers were refreshing a materialized view (`route_stop_patterns`) after every commit
- **Impact**: With 294 chunks, this meant 294 view refreshes, each taking several minutes
- **Total Time**: Full import took ~13 hours (47,495 seconds) instead of expected 1-2 hours

## Solution

Modified `scripts/load_gtfs_to_db.py` to:

1. **Disable triggers** before bulk loading starts
2. **Load all data** without trigger overhead
3. **Re-enable triggers** after loading completes
4. **Refresh materialized view once** at the end (instead of 294 times)

### Changes Made

- Added `disable_materialized_view_triggers()` function
- Added `enable_materialized_view_triggers()` function  
- Modified `load_gtfs_to_db()` to disable/enable triggers around bulk operations
- Added error handling to ensure triggers are re-enabled even on failure

## Optimizations Applied

### Phase 1: Trigger Optimization
- Disable materialized view refresh triggers during bulk load
- Refresh view once at end instead of 294 times
- **Speedup**: ~6-13x

### Phase 2: Index & Insert Optimizations
- **Disable indexes** during bulk load (recreate at end)
- **Use `bulk_insert_mappings`** instead of `bulk_save_objects` (skips ORM overhead)
- **Increase default chunk size** from 1000 to 5000 (fewer commits)
- **Speedup**: Additional 2-5x

### Combined Expected Performance

- **Before**: ~13 hours (with 5-9 minute delays between chunks)
- **After Phase 1**: ~1-2 hours (single view refresh at end)
- **After Phase 2**: ~15-30 minutes (with all optimizations)
- **Total Speedup**: ~25-50x faster

## Testing

To test the fix:

```powershell
# Test with limited data first
python scripts\load_gtfs_to_db.py scripts\gtfs_data\wienerlinien-gtfs.zip --test-mode

# Full import
python scripts\load_gtfs_to_db.py scripts\gtfs_data\wienerlinien-gtfs.zip
```

Monitor the logs - you should see:
- "Disabling materialized view refresh triggers..." at start
- Consistent chunk commit times (seconds, not minutes)
- "Refreshing materialized view route_stop_patterns..." at the end
- "Enabled X materialized view refresh triggers" at completion

## Technical Details

### Trigger Optimization
The materialized view `route_stop_patterns` aggregates route/stop relationships. The triggers fire on:
- `routes` table changes
- `trips` table changes  
- `stop_times` table changes
- `stops` table changes

Each trigger calls `REFRESH MATERIALIZED VIEW CONCURRENTLY`, which requires exclusive locks and can take minutes with large datasets.

By disabling triggers during bulk load and refreshing once at the end, we eliminate 293 unnecessary refreshes.

### Index Optimization
Indexes are expensive to maintain during bulk inserts. By:
1. Dropping indexes before load
2. Inserting all data
3. Recreating indexes at end

We avoid index maintenance overhead during inserts, which can be 2-5x faster.

### Insert Method Optimization
- `bulk_save_objects()`: Full ORM overhead, slower
- `bulk_insert_mappings()`: Direct SQL generation, ~1.5-2x faster

### Chunk Size Optimization
- Smaller chunks (1000): More commits, more overhead
- Larger chunks (5000): Fewer commits, less overhead, better throughput

For very large datasets, you can increase chunk size further:
```powershell
python scripts\load_gtfs_to_db.py scripts\gtfs_data\wienerlinien-gtfs.zip --chunk-size 10000
```

Note: Larger chunks use more memory but are faster.

## Date Fixed

2025-01-XX

