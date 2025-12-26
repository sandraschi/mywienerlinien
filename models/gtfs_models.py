import logging
import os

from dotenv import load_dotenv
from sqlalchemy import (
    Column,
    Float,
    ForeignKey,
    Integer,
    PrimaryKeyConstraint,
    String,
    Table,
    create_engine,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

# Load environment variables
load_dotenv()

# Database connection string
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost/wienerlinien")

logger = logging.getLogger(__name__)

# Create engine and session
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Association tables
route_stops = Table(
    "route_stops",
    Base.metadata,
    Column("route_id", String, ForeignKey("routes.route_id")),
    Column("stop_id", String, ForeignKey("stops.stop_id")),
    Column("stop_sequence", Integer),
)


class Agency(Base):
    __tablename__ = "agencies"

    agency_id = Column(String, primary_key=True)
    agency_name = Column(String, nullable=False)
    agency_url = Column(String)
    agency_timezone = Column(String, default="Europe/Vienna")
    agency_lang = Column(String, default="de")
    agency_phone = Column(String)

    routes = relationship("Route", back_populates="agency")


class Route(Base):
    __tablename__ = "routes"

    route_id = Column(String, primary_key=True)
    agency_id = Column(String, ForeignKey("agencies.agency_id"))
    route_short_name = Column(String)
    route_long_name = Column(String)
    route_desc = Column(String)
    route_type = Column(Integer)  # 0=Tram, 1=Subway, 2=Rail, 3=Bus, etc.
    route_url = Column(String)
    route_color = Column(String)
    route_text_color = Column(String)

    # Relationships
    agency = relationship("Agency", back_populates="routes")
    trips = relationship("Trip", back_populates="route")
    stops = relationship("Stop", secondary=route_stops, back_populates="routes")


class Stop(Base):
    __tablename__ = "stops"

    stop_id = Column(String, primary_key=True)
    stop_code = Column(String)
    stop_name = Column(String, nullable=False)
    stop_desc = Column(String)
    stop_lat = Column(Float)
    stop_lon = Column(Float)
    zone_id = Column(String)
    stop_url = Column(String)
    location_type = Column(Integer)  # 0=Stop, 1=Station
    parent_station = Column(String, ForeignKey("stops.stop_id"))
    wheelchair_boarding = Column(Integer)

    # Relationships
    child_stops = relationship("Stop", back_populates="parent")
    parent = relationship("Stop", back_populates="child_stops", remote_side=[stop_id])
    routes = relationship("Route", secondary=route_stops, back_populates="stops")
    stop_times = relationship("StopTime", back_populates="stop")


class Trip(Base):
    __tablename__ = "trips"

    trip_id = Column(String, primary_key=True)
    route_id = Column(String, ForeignKey("routes.route_id"))
    service_id = Column(String)
    trip_headsign = Column(String)
    trip_short_name = Column(String)
    direction_id = Column(Integer)  # 0=One direction, 1=Other direction
    block_id = Column(String)
    shape_id = Column(String)
    wheelchair_accessible = Column(Integer)
    bikes_allowed = Column(Integer)

    # Relationships
    route = relationship("Route", back_populates="trips")
    stop_times = relationship("StopTime", back_populates="trip")


class StopTime(Base):
    __tablename__ = "stop_times"

    id = Column(Integer, primary_key=True)
    trip_id = Column(String, ForeignKey("trips.trip_id"))
    arrival_time = Column(String)
    departure_time = Column(String)
    stop_id = Column(String, ForeignKey("stops.stop_id"))
    stop_sequence = Column(Integer)
    stop_headsign = Column(String)
    pickup_type = Column(Integer)
    drop_off_type = Column(Integer)
    shape_dist_traveled = Column(Float)
    timepoint = Column(Integer)

    # Relationships
    trip = relationship("Trip", back_populates="stop_times")
    stop = relationship("Stop", back_populates="stop_times")


class Shape(Base):
    __tablename__ = "shapes"
    __table_args__ = (PrimaryKeyConstraint("shape_id", "shape_pt_sequence"),)

    shape_id = Column(String, nullable=False)
    shape_pt_lat = Column(Float, nullable=False)
    shape_pt_lon = Column(Float, nullable=False)
    shape_pt_sequence = Column(Integer, nullable=False)
    shape_dist_traveled = Column(Float)


def get_db():
    """Dependency to get DB session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create all GTFS tables in the configured database."""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully.")
    except Exception as exc:
        logger.exception("Failed to create database tables: %s", exc)
        raise


if __name__ == "__main__":
    init_db()
