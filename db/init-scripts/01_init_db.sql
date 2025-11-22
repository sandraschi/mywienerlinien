-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "postgis";

DO $$
BEGIN
    CREATE TYPE transport_type AS ENUM (
        'tram', 'subway', 'rail', 'bus', 'ferry', 'cable_car', 'gondola', 'funicular'
    );
EXCEPTION
    WHEN duplicate_object THEN
        NULL;
END;
$$;

-- Create tables
CREATE TABLE IF NOT EXISTS agencies (
    agency_id TEXT PRIMARY KEY,
    agency_name TEXT NOT NULL,
    agency_url TEXT,
    agency_timezone TEXT DEFAULT 'Europe/Vienna',
    agency_lang TEXT DEFAULT 'de',
    agency_phone TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS routes (
    route_id TEXT PRIMARY KEY,
    agency_id TEXT REFERENCES agencies(agency_id) ON DELETE CASCADE,
    route_short_name TEXT,
    route_long_name TEXT,
    route_desc TEXT,
    route_type INTEGER NOT NULL,
    route_url TEXT,
    route_color CHAR(6) DEFAULT 'FFFFFF',
    route_text_color CHAR(6) DEFAULT '000000',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS stops (
    stop_id TEXT PRIMARY KEY,
    stop_code TEXT,
    stop_name TEXT NOT NULL,
    stop_desc TEXT,
    stop_lat DOUBLE PRECISION,
    stop_lon DOUBLE PRECISION,
    zone_id TEXT,
    stop_url TEXT,
    location_type INTEGER DEFAULT 0,
    parent_station TEXT REFERENCES stops(stop_id) ON DELETE CASCADE,
    wheelchair_boarding INTEGER,
    platform_code TEXT,
    platform_name TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS trips (
    trip_id TEXT PRIMARY KEY,
    route_id TEXT NOT NULL REFERENCES routes(route_id) ON DELETE CASCADE,
    service_id TEXT NOT NULL,
    trip_headsign TEXT,
    trip_short_name TEXT,
    direction_id INTEGER,
    block_id TEXT,
    shape_id TEXT,
    wheelchair_accessible INTEGER DEFAULT 0,
    bikes_allowed INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS stop_times (
    id SERIAL PRIMARY KEY,
    trip_id TEXT NOT NULL REFERENCES trips(trip_id) ON DELETE CASCADE,
    arrival_time TEXT,
    departure_time TEXT,
    stop_id TEXT NOT NULL REFERENCES stops(stop_id) ON DELETE CASCADE,
    stop_sequence INTEGER NOT NULL,
    stop_headsign TEXT,
    pickup_type INTEGER DEFAULT 0,
    drop_off_type INTEGER DEFAULT 0,
    shape_dist_traveled DOUBLE PRECISION,
    timepoint INTEGER DEFAULT 1,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(trip_id, stop_sequence)
);

CREATE TABLE IF NOT EXISTS shapes (
    shape_id TEXT NOT NULL,
    shape_pt_lat DOUBLE PRECISION NOT NULL,
    shape_pt_lon DOUBLE PRECISION NOT NULL,
    shape_pt_sequence INTEGER NOT NULL,
    shape_dist_traveled DOUBLE PRECISION,
    PRIMARY KEY (shape_id, shape_pt_sequence)
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_stop_times_trip_id ON stop_times(trip_id);
CREATE INDEX IF NOT EXISTS idx_stop_times_stop_id ON stop_times(stop_id);
CREATE INDEX IF NOT EXISTS idx_stops_location ON stops(stop_lat, stop_lon);
CREATE INDEX IF NOT EXISTS idx_routes_agency_id ON routes(agency_id);
CREATE INDEX IF NOT EXISTS idx_trips_route_id ON trips(route_id);
CREATE INDEX IF NOT EXISTS idx_shapes_shape_id ON shapes(shape_id);

-- Add spatial index for stops
CREATE INDEX IF NOT EXISTS idx_stops_geom ON stops USING GIST (
    ST_SetSRID(ST_MakePoint(stop_lon, stop_lat), 4326)
);

-- Create a materialized view for stop patterns
CREATE MATERIALIZED VIEW IF NOT EXISTS route_stop_patterns AS
SELECT 
    r.route_id,
    r.route_short_name,
    r.route_long_name,
    r.route_type,
    array_agg(st.stop_id ORDER BY st.stop_sequence) AS stop_sequence,
    array_agg(s.stop_name ORDER BY st.stop_sequence) AS stop_names,
    COUNT(DISTINCT st.stop_id) AS stop_count
FROM 
    routes r
JOIN 
    trips t ON r.route_id = t.route_id
JOIN 
    stop_times st ON t.trip_id = st.trip_id
JOIN 
    stops s ON st.stop_id = s.stop_id
GROUP BY 
    r.route_id, r.route_short_name, r.route_long_name, r.route_type;

CREATE UNIQUE INDEX IF NOT EXISTS idx_route_stop_patterns_route_id
    ON route_stop_patterns(route_id);

-- Create a function to refresh the materialized view
CREATE OR REPLACE FUNCTION refresh_route_stop_patterns()
RETURNS TRIGGER AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY route_stop_patterns;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS refresh_route_stop_patterns_routes ON routes;
CREATE TRIGGER refresh_route_stop_patterns_routes
AFTER INSERT OR UPDATE OR DELETE OR TRUNCATE
ON routes
FOR EACH STATEMENT
EXECUTE FUNCTION refresh_route_stop_patterns();

DROP TRIGGER IF EXISTS refresh_route_stop_patterns_trips ON trips;
CREATE TRIGGER refresh_route_stop_patterns_trips
AFTER INSERT OR UPDATE OR DELETE OR TRUNCATE
ON trips
FOR EACH STATEMENT
EXECUTE FUNCTION refresh_route_stop_patterns();

DROP TRIGGER IF EXISTS refresh_route_stop_patterns_stop_times ON stop_times;
CREATE TRIGGER refresh_route_stop_patterns_stop_times
AFTER INSERT OR UPDATE OR DELETE OR TRUNCATE
ON stop_times
FOR EACH STATEMENT
EXECUTE FUNCTION refresh_route_stop_patterns();

DROP TRIGGER IF EXISTS refresh_route_stop_patterns_stops ON stops;
CREATE TRIGGER refresh_route_stop_patterns_stops
AFTER INSERT OR UPDATE OR DELETE OR TRUNCATE
ON stops
FOR EACH STATEMENT
EXECUTE FUNCTION refresh_route_stop_patterns();

-- Add comments to tables and columns
COMMENT ON TABLE agencies IS 'Transit agencies that provide the data in this feed.';
COMMENT ON TABLE routes IS 'Transit routes. A route is a group of trips that are displayed to riders as a single service.';
COMMENT ON TABLE stops IS 'Stops where vehicles pick up or drop off passengers.';
COMMENT ON TABLE trips IS 'Trips for each route. A trip is a sequence of two or more stops that occurs at specific time.';
COMMENT ON TABLE stop_times IS 'Times that a vehicle arrives at and departs from individual stops for each trip.';

-- Create a function to update the updated_at column
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create triggers to update updated_at columns
DROP TRIGGER IF EXISTS update_agencies_updated_at ON agencies;
CREATE TRIGGER update_agencies_updated_at
BEFORE UPDATE ON agencies
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_routes_updated_at ON routes;
CREATE TRIGGER update_routes_updated_at
BEFORE UPDATE ON routes
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_stops_updated_at ON stops;
CREATE TRIGGER update_stops_updated_at
BEFORE UPDATE ON stops
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_trips_updated_at ON trips;
CREATE TRIGGER update_trips_updated_at
BEFORE UPDATE ON trips
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_stop_times_updated_at ON stop_times;
CREATE TRIGGER update_stop_times_updated_at
BEFORE UPDATE ON stop_times
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Create a function to search stops by name
CREATE OR REPLACE FUNCTION search_stops(search_term TEXT)
RETURNS TABLE (
    stop_id TEXT,
    stop_name TEXT,
    stop_lat DOUBLE PRECISION,
    stop_lon DOUBLE PRECISION,
    route_count BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        s.stop_id,
        s.stop_name,
        s.stop_lat,
        s.stop_lon,
        COUNT(DISTINCT t.route_id) AS route_count
    FROM 
        stops s
    LEFT JOIN 
        stop_times st ON s.stop_id = st.stop_id
    LEFT JOIN 
        trips t ON st.trip_id = t.trip_id
    WHERE 
        s.stop_name ILIKE '%' || search_term || '%'
    GROUP BY 
        s.stop_id, s.stop_name, s.stop_lat, s.stop_lon
    ORDER BY 
        route_count DESC, s.stop_name;
END;
$$ LANGUAGE plpgsql;
