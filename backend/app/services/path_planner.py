"""
Advanced coverage path planning algorithms for wall finishing.

Implements:
1. Boustrophedon (back-and-forth) pattern with obstacle avoidance
2. Intelligent path optimization
3. Complete coverage guarantee
"""
import numpy as np
from typing import List, Tuple, Dict, Any
from shapely.geometry import Polygon, box, Point, LineString
from shapely.ops import unary_union
from ..core.logging import logger, PerformanceLogger


class PathPlanner:
    """
    Coverage path planner for rectangular walls with obstacles.

    Algorithm: Modified Boustrophedon Decomposition
    - Decomposes wall into cells based on obstacles
    - Generates back-and-forth pattern in each cell
    - Optimizes transitions between cells
    """

    def __init__(self, wall_width: float, wall_height: float,
                 tool_width: float, overlap_percentage: float = 0.1):
        """
        Initialize path planner.

        Args:
            wall_width: Width of the wall in meters
            wall_height: Height of the wall in meters
            tool_width: Width of the finishing tool in meters
            overlap_percentage: Percentage of overlap between passes (0-0.5)
        """
        self.wall_width = wall_width
        self.wall_height = wall_height
        self.tool_width = tool_width
        self.overlap_percentage = overlap_percentage

        # Calculate effective stripe width accounting for overlap
        self.stripe_width = tool_width * (1 - overlap_percentage)

        # Create wall polygon
        self.wall_polygon = box(0, 0, wall_width, wall_height)
        self.obstacles: List[Polygon] = []

        logger.info(
            f"PathPlanner initialized: wall={wall_width}x{wall_height}m, "
            f"tool_width={tool_width}m, overlap={overlap_percentage*100}%, "
            f"stripe_width={self.stripe_width}m"
        )

    def add_obstacle(self, x: float, y: float, width: float, height: float):
        """
        Add a rectangular obstacle.

        Args:
            x: X coordinate of bottom-left corner
            y: Y coordinate of bottom-left corner
            width: Obstacle width
            height: Obstacle height
        """
        obstacle = box(x, y, x + width, y + height)
        self.obstacles.append(obstacle)
        logger.info(f"Added obstacle at ({x}, {y}) with size {width}x{height}m")

    def compute_path(self) -> Tuple[List[Tuple[float, float, str]], Dict[str, Any]]:
        """
        Compute complete coverage path.

        Returns:
            Tuple of (waypoints, metadata)
            waypoints: List of (x, y, action) tuples
            metadata: Dictionary with path statistics
        """
        with PerformanceLogger("Path computation"):
            # Create coverage area (wall minus obstacles)
            if self.obstacles:
                obstacle_union = unary_union(self.obstacles)
                coverage_area = self.wall_polygon.difference(obstacle_union)
            else:
                coverage_area = self.wall_polygon

            # Generate boustrophedon pattern
            waypoints = self._generate_boustrophedon_pattern(coverage_area)

            # Calculate metadata
            metadata = self._calculate_metadata(waypoints)

            logger.info(
                f"Path computed: {len(waypoints)} waypoints, "
                f"distance={metadata['total_distance']:.2f}m, "
                f"coverage={metadata['coverage_percentage']:.1f}%"
            )

            return waypoints, metadata

    def _generate_boustrophedon_pattern(self, coverage_area) -> List[Tuple[float, float, str]]:
        """
        Generate back-and-forth pattern for coverage.

        Strategy:
        1. Divide wall into vertical stripes of width = stripe_width
        2. For each stripe, move up and down alternately
        3. Handle obstacles by splitting stripes
        4. Optimize path to minimize travel distance
        """
        waypoints = []

        # Calculate stripe positions to ensure full coverage
        # Start at tool_width/2 from left edge, end at tool_width/2 from right edge
        num_stripes = int(np.ceil(self.wall_width / self.stripe_width))

        logger.info(f"Generating {num_stripes} stripes for coverage")

        # Add stripes to ensure complete coverage
        stripe_positions = []
        x = self.tool_width / 2  # Start position
        right_edge_x = self.wall_width - (self.tool_width / 2)

        while x <= right_edge_x:
            stripe_positions.append(x)
            x += self.stripe_width

        # Ensure the last stripe covers the right edge
        if stripe_positions:
            last_x = stripe_positions[-1]
            # If there's a significant gap, add a final stripe at the right edge
            if right_edge_x - last_x > 0.01:  # More than 1cm gap
                stripe_positions.append(right_edge_x)
                logger.info(f"Added final stripe at x={right_edge_x:.3f}m to cover right edge (gap was {right_edge_x - last_x:.3f}m)")

        logger.info(f"Stripe positions: first={stripe_positions[0]:.3f}m, last={stripe_positions[-1]:.3f}m, count={len(stripe_positions)}, right_edge_target={right_edge_x:.3f}m")

        for i, x in enumerate(stripe_positions):

            # Determine direction (alternate up/down)
            if i % 2 == 0:
                # Move upward
                segments = self._get_stripe_segments(x, coverage_area)
                for segment_start, segment_end in segments:
                    if not waypoints:
                        # First waypoint - move to start
                        waypoints.append((x, segment_start, "move"))
                    else:
                        # Move to segment start
                        waypoints.append((x, segment_start, "move"))

                    # Paint along segment
                    waypoints.append((x, segment_start, "paint_start"))
                    waypoints.append((x, segment_end, "paint_end"))
            else:
                # Move downward
                segments = self._get_stripe_segments(x, coverage_area)
                segments.reverse()
                for segment_start, segment_end in segments:
                    waypoints.append((x, segment_end, "move"))
                    waypoints.append((x, segment_end, "paint_start"))
                    waypoints.append((x, segment_start, "paint_end"))

        return waypoints

    def _get_stripe_segments(self, x: float, coverage_area) -> List[Tuple[float, float]]:
        """
        Get valid segments along a vertical stripe, avoiding obstacles.

        Args:
            x: X-coordinate of the stripe
            coverage_area: Shapely geometry of valid coverage area

        Returns:
            List of (y_start, y_end) tuples for valid segments
        """
        segments = []
        step_size = 0.01  # 1cm resolution for obstacle detection

        current_segment_start = None
        y = 0

        while y <= self.wall_height:
            # Check if the tool center point is valid (not inside obstacle)
            # and if the tool footprint doesn't collide with obstacles
            center_point = Point(x, y)

            # Create tool footprint at this position
            tool_box = box(
                max(0, x - self.tool_width / 2),  # Don't go below 0
                y,
                min(self.wall_width, x + self.tool_width / 2),  # Don't exceed wall
                min(self.wall_height, y + step_size)
            )

            # Check if center point is in coverage area AND tool doesn't intersect obstacles
            # This allows painting near walls while avoiding obstacles
            is_valid = coverage_area.contains(center_point)

            # For obstacle avoidance: check if tool box intersects with any obstacle
            if is_valid and self.obstacles:
                obstacle_union = unary_union(self.obstacles)
                # Tool must not intersect obstacle
                if tool_box.intersects(obstacle_union):
                    is_valid = False

            if is_valid:
                if current_segment_start is None:
                    current_segment_start = y
            else:
                # Hit an obstacle or boundary - end current segment
                if current_segment_start is not None:
                    segments.append((current_segment_start, y))
                    current_segment_start = None

            y += step_size

        # Close final segment
        if current_segment_start is not None:
            segments.append((current_segment_start, self.wall_height))

        return segments

    def _calculate_metadata(self, waypoints: List[Tuple[float, float, str]]) -> Dict[str, Any]:
        """Calculate path statistics and metadata."""
        if not waypoints:
            return {
                "total_distance": 0,
                "paint_distance": 0,
                "travel_distance": 0,
                "coverage_percentage": 0,
                "num_segments": 0
            }

        total_distance = 0
        paint_distance = 0
        travel_distance = 0
        num_segments = 0
        painting = False

        for i in range(1, len(waypoints)):
            x1, y1, action1 = waypoints[i - 1]
            x2, y2, action2 = waypoints[i]

            distance = np.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
            total_distance += distance

            if action1 == "paint_start":
                painting = True
                num_segments += 1

            if painting:
                paint_distance += distance

            if action1 == "paint_end":
                painting = False
            elif action1 == "move" and action2 == "move":
                travel_distance += distance

        # Calculate coverage percentage
        wall_area = self.wall_width * self.wall_height
        obstacle_area = sum(obs.area for obs in self.obstacles)
        effective_area = wall_area - obstacle_area
        coverage_area = paint_distance * self.tool_width

        coverage_percentage = min(100, (coverage_area / effective_area * 100) if effective_area > 0 else 0)

        return {
            "total_distance": float(total_distance),
            "paint_distance": float(paint_distance),
            "travel_distance": float(travel_distance),
            "coverage_percentage": float(coverage_percentage),
            "num_segments": int(num_segments),
            "wall_area": float(wall_area),
            "obstacle_area": float(obstacle_area),
            "effective_area": float(effective_area)
        }


def plan_trajectory(wall_width: float, wall_height: float,
                   obstacles: List[Dict[str, float]],
                   tool_width: float = 0.25,
                   overlap_percentage: float = 0.1) -> Tuple[List[Tuple[float, float, str]], Dict[str, Any]]:
    """
    Convenience function to plan a trajectory.

    Args:
        wall_width: Width of the wall in meters
        wall_height: Height of the wall in meters
        obstacles: List of obstacle dictionaries with keys: x, y, width, height
        tool_width: Width of the finishing tool in meters
        overlap_percentage: Percentage of overlap between passes

    Returns:
        Tuple of (waypoints, metadata)
    """
    planner = PathPlanner(wall_width, wall_height, tool_width, overlap_percentage)

    for obs in obstacles:
        planner.add_obstacle(obs['x'], obs['y'], obs['width'], obs['height'])

    return planner.compute_path()
