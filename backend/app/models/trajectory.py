"""
Database models for trajectory storage with advanced indexing and optimization.
"""
from sqlalchemy import (
    Column, Integer, Float, String, DateTime, Text, JSON, Index, ForeignKey
)
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

Base = declarative_base()


class Wall(Base):
    """Wall configuration model with spatial indexing."""

    __tablename__ = "walls"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(255), nullable=False, index=True)
    width = Column(Float, nullable=False)
    height = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    obstacles = relationship("Obstacle", back_populates="wall", cascade="all, delete-orphan")
    trajectories = relationship("Trajectory", back_populates="wall", cascade="all, delete-orphan")

    # Composite index for common queries
    __table_args__ = (
        Index('idx_wall_dimensions', 'width', 'height'),
        Index('idx_wall_created', 'created_at'),
    )


class Obstacle(Base):
    """Obstacle model for rectangular obstacles on walls."""

    __tablename__ = "obstacles"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    wall_id = Column(Integer, ForeignKey("walls.id", ondelete="CASCADE"), nullable=False, index=True)
    x = Column(Float, nullable=False)  # Bottom-left corner x
    y = Column(Float, nullable=False)  # Bottom-left corner y
    width = Column(Float, nullable=False)
    height = Column(Float, nullable=False)
    obstacle_type = Column(String(100), default="window", index=True)

    # Relationship
    wall = relationship("Wall", back_populates="obstacles")

    # Spatial indexing for obstacle queries
    __table_args__ = (
        Index('idx_obstacle_position', 'x', 'y'),
        Index('idx_obstacle_wall', 'wall_id', 'x', 'y'),
    )


class Trajectory(Base):
    """
    Trajectory model storing computed paths with heavy optimization.

    Optimization strategies:
    1. Separate table for waypoints to enable partial loading
    2. Indexed by wall_id for fast retrieval
    3. Metadata stored as JSON for flexible querying
    4. Timestamp indexing for time-series queries
    """

    __tablename__ = "trajectories"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    wall_id = Column(Integer, ForeignKey("walls.id", ondelete="CASCADE"), nullable=False, index=True)
    algorithm = Column(String(100), default="boustrophedon", index=True)
    tool_width = Column(Float, nullable=False)
    overlap_percentage = Column(Float, nullable=False)

    # Path statistics for quick filtering
    total_distance = Column(Float, nullable=False, index=True)
    total_waypoints = Column(Integer, nullable=False, index=True)
    estimated_time = Column(Float, nullable=False)  # seconds

    # Metadata as JSON for flexible storage
    path_metadata = Column(JSON, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    computed_in_ms = Column(Float, nullable=True)  # Computation time

    # Relationships
    wall = relationship("Wall", back_populates="trajectories")
    waypoints = relationship("Waypoint", back_populates="trajectory", cascade="all, delete-orphan", lazy="selectin")

    # Composite indexes for complex queries
    __table_args__ = (
        Index('idx_trajectory_wall_algo', 'wall_id', 'algorithm'),
        Index('idx_trajectory_performance', 'total_distance', 'estimated_time'),
        Index('idx_trajectory_created', 'created_at'),
    )


class Waypoint(Base):
    """
    Individual waypoint in a trajectory.

    Separated into its own table for:
    1. Efficient partial loading (pagination)
    2. Better indexing on sequence
    3. Reduced data duplication
    """

    __tablename__ = "waypoints"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    trajectory_id = Column(Integer, ForeignKey("trajectories.id", ondelete="CASCADE"), nullable=False, index=True)
    sequence = Column(Integer, nullable=False, index=True)  # Order in trajectory
    x = Column(Float, nullable=False)
    y = Column(Float, nullable=False)
    action = Column(String(50), default="move")  # move, paint_start, paint_end, etc.

    # Relationship
    trajectory = relationship("Trajectory", back_populates="waypoints")

    # Composite index for ordered retrieval
    __table_args__ = (
        Index('idx_waypoint_trajectory_seq', 'trajectory_id', 'sequence'),
        Index('idx_waypoint_position', 'x', 'y'),
    )
