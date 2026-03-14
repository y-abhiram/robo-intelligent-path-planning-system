#!/usr/bin/env python3
"""
Quick test script to verify the system works end-to-end.
Run this to ensure everything is set up correctly.
"""

import sys
import asyncio
from backend.app.services.path_planner import plan_trajectory
from backend.app.schemas.trajectory import ComputeTrajectoryRequest, WallCreate, ObstacleCreate

print("🤖 Wall Finishing Robot - Quick Test")
print("=" * 50)

# Test 1: Path Planning Algorithm
print("\n[Test 1] Path Planning Algorithm")
print("-" * 50)

try:
    # Test case from assignment
    obstacles = [
        {'x': 2.0, 'y': 2.0, 'width': 0.25, 'height': 0.25}
    ]

    waypoints, metadata = plan_trajectory(
        wall_width=5.0,
        wall_height=5.0,
        obstacles=obstacles,
        tool_width=0.25,
        overlap_percentage=0.1
    )

    print(f"✅ Path computed successfully!")
    print(f"   • Waypoints: {len(waypoints)}")
    print(f"   • Total Distance: {metadata['total_distance']:.2f}m")
    print(f"   • Paint Distance: {metadata['paint_distance']:.2f}m")
    print(f"   • Travel Distance: {metadata['travel_distance']:.2f}m")
    print(f"   • Coverage: {metadata['coverage_percentage']:.1f}%")
    print(f"   • Segments: {metadata['num_segments']}")
    print(f"   • Efficiency: {(metadata['paint_distance']/metadata['total_distance']*100):.1f}%")

except Exception as e:
    print(f"❌ Path planning failed: {e}")
    sys.exit(1)

# Test 2: Database Connection
print("\n[Test 2] Database Connection")
print("-" * 50)

try:
    from backend.app.db.database import engine
    print("✅ Database engine created successfully!")
    print(f"   • URL: {engine.url}")

except Exception as e:
    print(f"❌ Database connection failed: {e}")
    sys.exit(1)

# Test 3: Pydantic Validation
print("\n[Test 3] Request Validation")
print("-" * 50)

try:
    wall = WallCreate(
        name="Test Wall",
        width=5.0,
        height=5.0,
        obstacles=[
            ObstacleCreate(x=2.0, y=2.0, width=0.25, height=0.25, obstacle_type="window")
        ]
    )

    request = ComputeTrajectoryRequest(
        wall=wall,
        tool_width=0.25,
        overlap_percentage=0.1,
        algorithm="boustrophedon"
    )

    print("✅ Request validation passed!")
    print(f"   • Wall: {request.wall.name} ({request.wall.width}x{request.wall.height}m)")
    print(f"   • Obstacles: {len(request.wall.obstacles)}")
    print(f"   • Tool Width: {request.tool_width}m")
    print(f"   • Overlap: {request.overlap_percentage*100:.0f}%")

except Exception as e:
    print(f"❌ Validation failed: {e}")
    sys.exit(1)

# Test 4: Edge Cases
print("\n[Test 4] Edge Cases")
print("-" * 50)

try:
    # Small wall
    waypoints1, _ = plan_trajectory(1.0, 1.0, [], 0.1, 0.1)
    print(f"✅ Small wall (1x1m): {len(waypoints1)} waypoints")

    # Large wall
    waypoints2, _ = plan_trajectory(10.0, 10.0, [], 0.25, 0.1)
    print(f"✅ Large wall (10x10m): {len(waypoints2)} waypoints")

    # Multiple obstacles
    multi_obstacles = [
        {'x': 1.0, 'y': 1.0, 'width': 0.5, 'height': 0.5},
        {'x': 3.0, 'y': 3.0, 'width': 0.5, 'height': 0.5},
        {'x': 5.0, 'y': 5.0, 'width': 0.5, 'height': 0.5},
    ]
    waypoints3, _ = plan_trajectory(10.0, 10.0, multi_obstacles, 0.25, 0.1)
    print(f"✅ Multiple obstacles (3): {len(waypoints3)} waypoints")

except Exception as e:
    print(f"❌ Edge case failed: {e}")
    sys.exit(1)

# Summary
print("\n" + "=" * 50)
print("🎉 All Tests Passed!")
print("=" * 50)
print("\nSystem is ready to use!")
print("\nNext steps:")
print("1. Start the server: ./run.sh")
print("2. Open browser: http://localhost:8000")
print("3. Try the example from the assignment")
print("\nAPI Documentation: http://localhost:8000/docs")
print("\n✨ Happy path planning! 🤖")
