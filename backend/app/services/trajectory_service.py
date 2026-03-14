"""
Service layer for trajectory management with database operations.
"""
import time
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from sqlalchemy.orm import selectinload

from ..models.trajectory import Wall, Obstacle, Trajectory, Waypoint
from ..schemas.trajectory import (
    WallCreate, TrajectoryCreate, ComputeTrajectoryRequest
)
from .path_planner import plan_trajectory
from ..core.logging import logger, PerformanceLogger
from ..core.config import settings


class TrajectoryService:
    """Service for trajectory computation and storage."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_wall(self, wall_data: WallCreate) -> Wall:
        """Create a wall with obstacles."""
        with PerformanceLogger("Create wall"):
            wall = Wall(
                name=wall_data.name,
                width=wall_data.width,
                height=wall_data.height
            )

            # Add obstacles
            for obs_data in wall_data.obstacles:
                obstacle = Obstacle(
                    x=obs_data.x,
                    y=obs_data.y,
                    width=obs_data.width,
                    height=obs_data.height,
                    obstacle_type=obs_data.obstacle_type
                )
                wall.obstacles.append(obstacle)

            self.db.add(wall)
            await self.db.commit()
            await self.db.refresh(wall, attribute_names=['obstacles'])

            logger.info(f"Created wall {wall.id}: {wall.name} ({wall.width}x{wall.height}m) with {len(wall.obstacles)} obstacles")
            return wall

    async def get_wall(self, wall_id: int) -> Optional[Wall]:
        """Get a wall by ID with obstacles."""
        result = await self.db.execute(
            select(Wall)
            .options(selectinload(Wall.obstacles))
            .where(Wall.id == wall_id)
        )
        return result.scalar_one_or_none()

    async def get_walls(self, skip: int = 0, limit: int = 100) -> List[Wall]:
        """Get all walls with pagination."""
        result = await self.db.execute(
            select(Wall)
            .options(selectinload(Wall.obstacles))
            .offset(skip)
            .limit(limit)
            .order_by(desc(Wall.created_at))
        )
        return list(result.scalars().all())

    async def delete_wall(self, wall_id: int) -> bool:
        """Delete a wall and all associated data."""
        wall = await self.get_wall(wall_id)
        if not wall:
            return False

        await self.db.delete(wall)
        await self.db.commit()
        logger.info(f"Deleted wall {wall_id}")
        return True

    async def compute_and_store_trajectory(
        self, request: ComputeTrajectoryRequest
    ) -> Trajectory:
        """
        Compute trajectory and store in database.

        This is the main operation that:
        1. Creates/reuses wall configuration
        2. Computes optimal path
        3. Stores trajectory and waypoints
        """
        with PerformanceLogger("Compute and store trajectory"):
            start_time = time.time()

            # Create wall
            wall = await self.create_wall(request.wall)

            # Prepare obstacles for path planner (from request data, not from DB)
            obstacles = [
                {"x": obs.x, "y": obs.y, "width": obs.width, "height": obs.height}
                for obs in request.wall.obstacles
            ]

            # Compute path
            waypoints_data, metadata = plan_trajectory(
                wall.width,
                wall.height,
                obstacles,
                request.tool_width,
                request.overlap_percentage
            )

            computation_time_ms = (time.time() - start_time) * 1000

            # Calculate estimated time (assuming constant speed)
            estimated_time = metadata['total_distance'] / settings.DEFAULT_SPEED

            # Create trajectory record
            trajectory = Trajectory(
                wall_id=wall.id,
                algorithm=request.algorithm,
                tool_width=request.tool_width,
                overlap_percentage=request.overlap_percentage,
                total_distance=metadata['total_distance'],
                total_waypoints=len(waypoints_data),
                estimated_time=estimated_time,
                path_metadata=metadata,
                computed_in_ms=computation_time_ms
            )

            # Create waypoint records
            for idx, (x, y, action) in enumerate(waypoints_data):
                waypoint = Waypoint(
                    sequence=idx,
                    x=x,
                    y=y,
                    action=action
                )
                trajectory.waypoints.append(waypoint)

            self.db.add(trajectory)
            await self.db.commit()
            await self.db.refresh(trajectory)

            logger.info(
                f"Stored trajectory {trajectory.id}: "
                f"{trajectory.total_waypoints} waypoints, "
                f"{trajectory.total_distance:.2f}m total distance, "
                f"computed in {computation_time_ms:.2f}ms"
            )

            return trajectory

    async def get_trajectory(self, trajectory_id: int) -> Optional[Trajectory]:
        """Get a trajectory by ID with all waypoints."""
        result = await self.db.execute(
            select(Trajectory)
            .options(selectinload(Trajectory.waypoints))
            .where(Trajectory.id == trajectory_id)
        )
        return result.scalar_one_or_none()

    async def get_trajectories(
        self, skip: int = 0, limit: int = 100, wall_id: Optional[int] = None
    ) -> List[Trajectory]:
        """Get trajectories with optional filtering by wall."""
        query = select(Trajectory).order_by(desc(Trajectory.created_at))

        if wall_id is not None:
            query = query.where(Trajectory.wall_id == wall_id)

        query = query.offset(skip).limit(limit)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def delete_trajectory(self, trajectory_id: int) -> bool:
        """Delete a trajectory."""
        trajectory = await self.get_trajectory(trajectory_id)
        if not trajectory:
            return False

        await self.db.delete(trajectory)
        await self.db.commit()
        logger.info(f"Deleted trajectory {trajectory_id}")
        return True

    async def get_statistics(self) -> dict:
        """Get system statistics."""
        # Count walls
        wall_count = await self.db.execute(select(func.count(Wall.id)))
        total_walls = wall_count.scalar()

        # Count trajectories
        traj_count = await self.db.execute(select(func.count(Trajectory.id)))
        total_trajectories = traj_count.scalar()

        # Count waypoints
        waypoint_count = await self.db.execute(select(func.count(Waypoint.id)))
        total_waypoints = waypoint_count.scalar()

        # Average computation time
        avg_comp_time = await self.db.execute(
            select(func.avg(Trajectory.computed_in_ms))
        )
        avg_computation_time_ms = avg_comp_time.scalar()

        # Average trajectory distance
        avg_dist = await self.db.execute(
            select(func.avg(Trajectory.total_distance))
        )
        avg_trajectory_distance = avg_dist.scalar()

        return {
            "total_walls": total_walls,
            "total_trajectories": total_trajectories,
            "total_waypoints": total_waypoints,
            "avg_computation_time_ms": float(avg_computation_time_ms) if avg_computation_time_ms else None,
            "avg_trajectory_distance": float(avg_trajectory_distance) if avg_trajectory_distance else None
        }
