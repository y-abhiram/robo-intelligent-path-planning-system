"""
Pydantic schemas for request/response validation.
"""
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict, Any
from datetime import datetime


# Obstacle Schemas
class ObstacleBase(BaseModel):
    """Base schema for obstacle data."""
    x: float = Field(..., ge=0, description="X coordinate of bottom-left corner (meters)")
    y: float = Field(..., ge=0, description="Y coordinate of bottom-left corner (meters)")
    width: float = Field(..., gt=0, description="Obstacle width (meters)")
    height: float = Field(..., gt=0, description="Obstacle height (meters)")
    obstacle_type: str = Field(default="window", description="Type of obstacle")


class ObstacleCreate(ObstacleBase):
    """Schema for creating an obstacle."""
    pass


class ObstacleResponse(ObstacleBase):
    """Schema for obstacle response."""
    id: int
    wall_id: int

    class Config:
        from_attributes = True


# Wall Schemas
class WallBase(BaseModel):
    """Base schema for wall data."""
    name: str = Field(..., min_length=1, max_length=255, description="Wall identifier")
    width: float = Field(..., gt=0, le=100, description="Wall width (meters)")
    height: float = Field(..., gt=0, le=100, description="Wall height (meters)")


class WallCreate(WallBase):
    """Schema for creating a wall with obstacles."""
    obstacles: List[ObstacleCreate] = Field(default_factory=list, description="List of obstacles on the wall")

    @field_validator('obstacles')
    @classmethod
    def validate_obstacles(cls, v, info):
        """Validate that obstacles are within wall bounds."""
        if 'width' in info.data and 'height' in info.data:
            wall_width = info.data['width']
            wall_height = info.data['height']
            for obs in v:
                if obs.x + obs.width > wall_width:
                    raise ValueError(f"Obstacle extends beyond wall width: {obs.x + obs.width} > {wall_width}")
                if obs.y + obs.height > wall_height:
                    raise ValueError(f"Obstacle extends beyond wall height: {obs.y + obs.height} > {wall_height}")
        return v


class WallResponse(WallBase):
    """Schema for wall response."""
    id: int
    created_at: datetime
    updated_at: datetime
    obstacles: List[ObstacleResponse] = []

    class Config:
        from_attributes = True


# Waypoint Schemas
class WaypointBase(BaseModel):
    """Base schema for waypoint data."""
    x: float = Field(..., description="X coordinate (meters)")
    y: float = Field(..., description="Y coordinate (meters)")
    sequence: int = Field(..., ge=0, description="Order in trajectory")
    action: str = Field(default="move", description="Action type at this waypoint")


class WaypointResponse(WaypointBase):
    """Schema for waypoint response."""
    id: int
    trajectory_id: int

    class Config:
        from_attributes = True


# Trajectory Schemas
class TrajectoryBase(BaseModel):
    """Base schema for trajectory data."""
    algorithm: str = Field(default="boustrophedon", description="Path planning algorithm")
    tool_width: float = Field(default=0.25, gt=0, description="Tool width (meters)")
    overlap_percentage: float = Field(default=0.1, ge=0, le=0.5, description="Overlap percentage")


class TrajectoryCreate(TrajectoryBase):
    """Schema for creating a trajectory."""
    wall_id: int = Field(..., gt=0, description="ID of the wall")


class TrajectoryResponse(TrajectoryBase):
    """Schema for trajectory response."""
    id: int
    wall_id: int
    total_distance: float
    total_waypoints: int
    estimated_time: float
    path_metadata: Optional[Dict[str, Any]] = None
    created_at: datetime
    computed_in_ms: Optional[float] = None
    waypoints: List[WaypointResponse] = []

    class Config:
        from_attributes = True


class TrajectoryListResponse(TrajectoryBase):
    """Lightweight schema for trajectory list (without waypoints)."""
    id: int
    wall_id: int
    total_distance: float
    total_waypoints: int
    estimated_time: float
    created_at: datetime
    computed_in_ms: Optional[float] = None

    class Config:
        from_attributes = True


# Compute Request Schema
class ComputeTrajectoryRequest(BaseModel):
    """Schema for trajectory computation request."""
    wall: WallCreate
    tool_width: float = Field(default=0.25, gt=0, description="Tool width (meters)")
    overlap_percentage: float = Field(default=0.1, ge=0, le=0.5, description="Overlap percentage")
    algorithm: str = Field(default="boustrophedon", description="Path planning algorithm")


# Statistics Schema
class StatisticsResponse(BaseModel):
    """Schema for system statistics."""
    total_walls: int
    total_trajectories: int
    total_waypoints: int
    avg_computation_time_ms: Optional[float]
    avg_trajectory_distance: Optional[float]
