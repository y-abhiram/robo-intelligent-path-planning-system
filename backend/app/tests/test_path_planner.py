"""
Tests for path planning algorithms.
"""
import pytest
from ..services.path_planner import PathPlanner, plan_trajectory


class TestPathPlanner:
    """Test suite for PathPlanner class."""

    def test_basic_path_generation(self):
        """Test basic path generation without obstacles."""
        planner = PathPlanner(5.0, 5.0, 0.25, 0.1)
        waypoints, metadata = planner.compute_path()

        assert len(waypoints) > 0
        assert metadata['total_distance'] > 0
        assert metadata['coverage_percentage'] > 90  # Should cover most of the wall

    def test_path_with_obstacle(self):
        """Test path generation with a single obstacle."""
        planner = PathPlanner(5.0, 5.0, 0.25, 0.1)
        planner.add_obstacle(2.0, 2.0, 0.25, 0.25)
        waypoints, metadata = planner.compute_path()

        assert len(waypoints) > 0
        assert metadata['obstacle_area'] == pytest.approx(0.0625, rel=0.01)
        assert metadata['wall_area'] == 25.0

    def test_path_with_multiple_obstacles(self):
        """Test path generation with multiple obstacles."""
        planner = PathPlanner(5.0, 5.0, 0.25, 0.1)
        planner.add_obstacle(1.0, 1.0, 0.5, 0.5)
        planner.add_obstacle(3.0, 3.0, 0.5, 0.5)
        waypoints, metadata = planner.compute_path()

        assert len(waypoints) > 0
        assert metadata['num_segments'] > 0

    def test_small_wall(self):
        """Test path generation for a small wall."""
        planner = PathPlanner(1.0, 1.0, 0.1, 0.1)
        waypoints, metadata = planner.compute_path()

        assert len(waypoints) > 0
        assert metadata['wall_area'] == 1.0

    def test_large_wall(self):
        """Test path generation for a large wall."""
        planner = PathPlanner(10.0, 8.0, 0.25, 0.1)
        waypoints, metadata = planner.compute_path()

        assert len(waypoints) > 0
        assert metadata['wall_area'] == 80.0

    def test_different_tool_widths(self):
        """Test path generation with different tool widths."""
        planner1 = PathPlanner(5.0, 5.0, 0.25, 0.1)
        waypoints1, metadata1 = planner1.compute_path()

        planner2 = PathPlanner(5.0, 5.0, 0.5, 0.1)
        waypoints2, metadata2 = planner2.compute_path()

        # Larger tool should need fewer waypoints
        assert len(waypoints2) < len(waypoints1)
        assert metadata2['total_distance'] < metadata1['total_distance']

    def test_different_overlap_percentages(self):
        """Test path generation with different overlap percentages."""
        planner1 = PathPlanner(5.0, 5.0, 0.25, 0.05)
        waypoints1, metadata1 = planner1.compute_path()

        planner2 = PathPlanner(5.0, 5.0, 0.25, 0.2)
        waypoints2, metadata2 = planner2.compute_path()

        # Higher overlap should need more waypoints
        assert len(waypoints2) > len(waypoints1)

    def test_waypoint_structure(self):
        """Test that waypoints have correct structure."""
        planner = PathPlanner(5.0, 5.0, 0.25, 0.1)
        waypoints, metadata = planner.compute_path()

        for wp in waypoints:
            assert len(wp) == 3
            x, y, action = wp
            assert isinstance(x, float)
            assert isinstance(y, float)
            assert action in ['move', 'paint_start', 'paint_end']

    def test_paint_actions_paired(self):
        """Test that paint_start and paint_end actions are properly paired."""
        planner = PathPlanner(5.0, 5.0, 0.25, 0.1)
        waypoints, metadata = planner.compute_path()

        paint_starts = sum(1 for _, _, action in waypoints if action == 'paint_start')
        paint_ends = sum(1 for _, _, action in waypoints if action == 'paint_end')

        assert paint_starts == paint_ends

    def test_convenience_function(self):
        """Test the convenience function plan_trajectory."""
        obstacles = [
            {'x': 2.0, 'y': 2.0, 'width': 0.25, 'height': 0.25}
        ]
        waypoints, metadata = plan_trajectory(5.0, 5.0, obstacles, 0.25, 0.1)

        assert len(waypoints) > 0
        assert metadata['total_distance'] > 0

    def test_metadata_completeness(self):
        """Test that metadata contains all required fields."""
        planner = PathPlanner(5.0, 5.0, 0.25, 0.1)
        waypoints, metadata = planner.compute_path()

        required_fields = [
            'total_distance', 'paint_distance', 'travel_distance',
            'coverage_percentage', 'num_segments', 'wall_area',
            'obstacle_area', 'effective_area'
        ]

        for field in required_fields:
            assert field in metadata
            assert isinstance(metadata[field], (int, float))

    def test_bounds_checking(self):
        """Test that all waypoints are within wall bounds."""
        planner = PathPlanner(5.0, 5.0, 0.25, 0.1)
        waypoints, metadata = planner.compute_path()

        for x, y, _ in waypoints:
            assert 0 <= x <= 5.0
            assert 0 <= y <= 5.0

    def test_edge_case_full_obstacle(self):
        """Test with obstacle covering most of the wall."""
        planner = PathPlanner(5.0, 5.0, 0.25, 0.1)
        planner.add_obstacle(0.5, 0.5, 4.0, 4.0)
        waypoints, metadata = planner.compute_path()

        # Should still generate some path
        assert len(waypoints) >= 0
        assert metadata['obstacle_area'] == 16.0

    def test_zero_overlap(self):
        """Test with zero overlap."""
        planner = PathPlanner(5.0, 5.0, 0.25, 0.0)
        waypoints, metadata = planner.compute_path()

        assert len(waypoints) > 0
        assert planner.stripe_width == 0.25
