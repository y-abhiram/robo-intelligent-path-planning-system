"""
API endpoints for trajectory management.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from ..db.database import get_db
from ..schemas.trajectory import (
    WallCreate, WallResponse,
    TrajectoryCreate, TrajectoryResponse, TrajectoryListResponse,
    ComputeTrajectoryRequest,
    StatisticsResponse
)
from ..services.trajectory_service import TrajectoryService
from ..core.logging import logger

router = APIRouter(prefix="/api/v1", tags=["trajectories"])


@router.post("/walls", response_model=WallResponse, status_code=201)
async def create_wall(
    wall: WallCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new wall with obstacles.

    - **name**: Unique identifier for the wall
    - **width**: Wall width in meters
    - **height**: Wall height in meters
    - **obstacles**: List of rectangular obstacles
    """
    service = TrajectoryService(db)
    try:
        created_wall = await service.create_wall(wall)
        return created_wall
    except Exception as e:
        logger.error(f"Error creating wall: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/walls", response_model=List[WallResponse])
async def get_walls(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all walls with pagination.

    - **skip**: Offset for pagination
    - **limit**: Maximum number of results
    """
    service = TrajectoryService(db)
    walls = await service.get_walls(skip, limit)
    return walls


@router.get("/walls/{wall_id}", response_model=WallResponse)
async def get_wall(
    wall_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific wall by ID."""
    service = TrajectoryService(db)
    wall = await service.get_wall(wall_id)
    if not wall:
        raise HTTPException(status_code=404, detail=f"Wall {wall_id} not found")
    return wall


@router.delete("/walls/{wall_id}", status_code=204)
async def delete_wall(
    wall_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Delete a wall and all associated trajectories."""
    service = TrajectoryService(db)
    deleted = await service.delete_wall(wall_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Wall {wall_id} not found")


@router.post("/trajectories/compute", response_model=TrajectoryResponse, status_code=201)
async def compute_trajectory(
    request: ComputeTrajectoryRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Compute coverage trajectory for a wall.

    This endpoint:
    1. Creates a wall configuration
    2. Computes optimal coverage path using boustrophedon algorithm
    3. Stores trajectory and waypoints in database
    4. Returns complete trajectory with metadata

    **Example Request:**
    ```json
    {
        "wall": {
            "name": "Wall-1",
            "width": 5.0,
            "height": 5.0,
            "obstacles": [
                {"x": 2.0, "y": 2.0, "width": 0.25, "height": 0.25, "obstacle_type": "window"}
            ]
        },
        "tool_width": 0.25,
        "overlap_percentage": 0.1,
        "algorithm": "boustrophedon"
    }
    ```
    """
    service = TrajectoryService(db)
    try:
        trajectory = await service.compute_and_store_trajectory(request)
        return trajectory
    except Exception as e:
        logger.error(f"Error computing trajectory: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/trajectories", response_model=List[TrajectoryListResponse])
async def get_trajectories(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    wall_id: int = Query(None, description="Filter by wall ID"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all trajectories with pagination.

    Returns lightweight trajectory data (without waypoints) for listing.
    Use the `/trajectories/{id}` endpoint to get full details including waypoints.
    """
    service = TrajectoryService(db)
    trajectories = await service.get_trajectories(skip, limit, wall_id)
    return trajectories


@router.get("/trajectories/{trajectory_id}", response_model=TrajectoryResponse)
async def get_trajectory(
    trajectory_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific trajectory by ID with all waypoints.

    Returns complete trajectory data including all waypoints for visualization.
    """
    service = TrajectoryService(db)
    trajectory = await service.get_trajectory(trajectory_id)
    if not trajectory:
        raise HTTPException(status_code=404, detail=f"Trajectory {trajectory_id} not found")
    return trajectory


@router.delete("/trajectories/{trajectory_id}", status_code=204)
async def delete_trajectory(
    trajectory_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Delete a trajectory and all its waypoints."""
    service = TrajectoryService(db)
    deleted = await service.delete_trajectory(trajectory_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Trajectory {trajectory_id} not found")


@router.get("/statistics", response_model=StatisticsResponse)
async def get_statistics(db: AsyncSession = Depends(get_db)):
    """
    Get system statistics.

    Returns aggregated metrics about the system performance and usage.
    """
    service = TrajectoryService(db)
    stats = await service.get_statistics()
    return stats
