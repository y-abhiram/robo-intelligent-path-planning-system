"""
API endpoint tests using FastAPI TestClient.
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from ..main import app
from ..db.database import get_db
from ..models.trajectory import Base


# Test database setup
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False}
)

test_session_maker = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False
)


async def override_get_db():
    """Override database dependency for testing."""
    async with test_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@pytest.fixture
async def setup_database():
    """Create test database tables."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
def client(setup_database):
    """Create test client with database override."""
    app.dependency_overrides[get_db] = override_get_db
    return AsyncClient(app=app, base_url="http://test")


class TestHealthCheck:
    """Test health check endpoint."""

    @pytest.mark.asyncio
    async def test_health_check(self, client):
        """Test health check returns 200."""
        async with client:
            response = await client.get("/health")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"


class TestWallEndpoints:
    """Test wall-related endpoints."""

    @pytest.mark.asyncio
    async def test_create_wall(self, client):
        """Test creating a wall."""
        async with client:
            wall_data = {
                "name": "Test Wall",
                "width": 5.0,
                "height": 5.0,
                "obstacles": []
            }
            response = await client.post("/api/v1/walls", json=wall_data)
            assert response.status_code == 201
            data = response.json()
            assert data["name"] == "Test Wall"
            assert data["width"] == 5.0
            assert data["height"] == 5.0

    @pytest.mark.asyncio
    async def test_create_wall_with_obstacles(self, client):
        """Test creating a wall with obstacles."""
        async with client:
            wall_data = {
                "name": "Test Wall 2",
                "width": 5.0,
                "height": 5.0,
                "obstacles": [
                    {"x": 2.0, "y": 2.0, "width": 0.25, "height": 0.25, "obstacle_type": "window"}
                ]
            }
            response = await client.post("/api/v1/walls", json=wall_data)
            assert response.status_code == 201
            data = response.json()
            assert len(data["obstacles"]) == 1
            assert data["obstacles"][0]["x"] == 2.0

    @pytest.mark.asyncio
    async def test_get_walls(self, client):
        """Test getting all walls."""
        async with client:
            # Create a wall first
            wall_data = {
                "name": "Test Wall",
                "width": 5.0,
                "height": 5.0,
                "obstacles": []
            }
            await client.post("/api/v1/walls", json=wall_data)

            # Get walls
            response = await client.get("/api/v1/walls")
            assert response.status_code == 200
            data = response.json()
            assert len(data) >= 1

    @pytest.mark.asyncio
    async def test_get_wall_by_id(self, client):
        """Test getting a specific wall."""
        async with client:
            # Create a wall
            wall_data = {
                "name": "Test Wall",
                "width": 5.0,
                "height": 5.0,
                "obstacles": []
            }
            create_response = await client.post("/api/v1/walls", json=wall_data)
            wall_id = create_response.json()["id"]

            # Get the wall
            response = await client.get(f"/api/v1/walls/{wall_id}")
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == wall_id

    @pytest.mark.asyncio
    async def test_get_nonexistent_wall(self, client):
        """Test getting a wall that doesn't exist."""
        async with client:
            response = await client.get("/api/v1/walls/999")
            assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_wall(self, client):
        """Test deleting a wall."""
        async with client:
            # Create a wall
            wall_data = {
                "name": "Test Wall",
                "width": 5.0,
                "height": 5.0,
                "obstacles": []
            }
            create_response = await client.post("/api/v1/walls", json=wall_data)
            wall_id = create_response.json()["id"]

            # Delete the wall
            response = await client.delete(f"/api/v1/walls/{wall_id}")
            assert response.status_code == 204

            # Verify it's gone
            get_response = await client.get(f"/api/v1/walls/{wall_id}")
            assert get_response.status_code == 404

    @pytest.mark.asyncio
    async def test_invalid_wall_dimensions(self, client):
        """Test creating a wall with invalid dimensions."""
        async with client:
            wall_data = {
                "name": "Invalid Wall",
                "width": -5.0,
                "height": 5.0,
                "obstacles": []
            }
            response = await client.post("/api/v1/walls", json=wall_data)
            assert response.status_code == 422  # Validation error


class TestTrajectoryEndpoints:
    """Test trajectory-related endpoints."""

    @pytest.mark.asyncio
    async def test_compute_trajectory(self, client):
        """Test computing a trajectory."""
        async with client:
            request_data = {
                "wall": {
                    "name": "Test Wall",
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
            response = await client.post("/api/v1/trajectories/compute", json=request_data)
            assert response.status_code == 201
            data = response.json()
            assert "id" in data
            assert "waypoints" in data
            assert data["total_distance"] > 0
            assert data["total_waypoints"] > 0
            assert len(data["waypoints"]) == data["total_waypoints"]

    @pytest.mark.asyncio
    async def test_get_trajectories(self, client):
        """Test getting all trajectories."""
        async with client:
            # Compute a trajectory first
            request_data = {
                "wall": {
                    "name": "Test Wall",
                    "width": 5.0,
                    "height": 5.0,
                    "obstacles": []
                },
                "tool_width": 0.25,
                "overlap_percentage": 0.1,
                "algorithm": "boustrophedon"
            }
            await client.post("/api/v1/trajectories/compute", json=request_data)

            # Get trajectories
            response = await client.get("/api/v1/trajectories")
            assert response.status_code == 200
            data = response.json()
            assert len(data) >= 1

    @pytest.mark.asyncio
    async def test_get_trajectory_by_id(self, client):
        """Test getting a specific trajectory."""
        async with client:
            # Compute a trajectory
            request_data = {
                "wall": {
                    "name": "Test Wall",
                    "width": 5.0,
                    "height": 5.0,
                    "obstacles": []
                },
                "tool_width": 0.25,
                "overlap_percentage": 0.1,
                "algorithm": "boustrophedon"
            }
            create_response = await client.post("/api/v1/trajectories/compute", json=request_data)
            trajectory_id = create_response.json()["id"]

            # Get the trajectory
            response = await client.get(f"/api/v1/trajectories/{trajectory_id}")
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == trajectory_id
            assert "waypoints" in data

    @pytest.mark.asyncio
    async def test_delete_trajectory(self, client):
        """Test deleting a trajectory."""
        async with client:
            # Compute a trajectory
            request_data = {
                "wall": {
                    "name": "Test Wall",
                    "width": 5.0,
                    "height": 5.0,
                    "obstacles": []
                },
                "tool_width": 0.25,
                "overlap_percentage": 0.1,
                "algorithm": "boustrophedon"
            }
            create_response = await client.post("/api/v1/trajectories/compute", json=request_data)
            trajectory_id = create_response.json()["id"]

            # Delete the trajectory
            response = await client.delete(f"/api/v1/trajectories/{trajectory_id}")
            assert response.status_code == 204

            # Verify it's gone
            get_response = await client.get(f"/api/v1/trajectories/{trajectory_id}")
            assert get_response.status_code == 404

    @pytest.mark.asyncio
    async def test_trajectory_with_pagination(self, client):
        """Test trajectory pagination."""
        async with client:
            # Create multiple trajectories
            for i in range(5):
                request_data = {
                    "wall": {
                        "name": f"Test Wall {i}",
                        "width": 5.0,
                        "height": 5.0,
                        "obstacles": []
                    },
                    "tool_width": 0.25,
                    "overlap_percentage": 0.1,
                    "algorithm": "boustrophedon"
                }
                await client.post("/api/v1/trajectories/compute", json=request_data)

            # Test pagination
            response = await client.get("/api/v1/trajectories?skip=0&limit=2")
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 2


class TestStatistics:
    """Test statistics endpoint."""

    @pytest.mark.asyncio
    async def test_get_statistics(self, client):
        """Test getting system statistics."""
        async with client:
            # Compute a trajectory first
            request_data = {
                "wall": {
                    "name": "Test Wall",
                    "width": 5.0,
                    "height": 5.0,
                    "obstacles": []
                },
                "tool_width": 0.25,
                "overlap_percentage": 0.1,
                "algorithm": "boustrophedon"
            }
            await client.post("/api/v1/trajectories/compute", json=request_data)

            # Get statistics
            response = await client.get("/api/v1/statistics")
            assert response.status_code == 200
            data = response.json()
            assert "total_walls" in data
            assert "total_trajectories" in data
            assert "total_waypoints" in data
            assert data["total_trajectories"] >= 1


class TestPerformance:
    """Test API performance and response times."""

    @pytest.mark.asyncio
    async def test_compute_trajectory_performance(self, client):
        """Test that trajectory computation is reasonably fast."""
        import time
        async with client:
            request_data = {
                "wall": {
                    "name": "Performance Test",
                    "width": 10.0,
                    "height": 10.0,
                    "obstacles": [
                        {"x": 2.0, "y": 2.0, "width": 0.5, "height": 0.5, "obstacle_type": "window"}
                    ]
                },
                "tool_width": 0.25,
                "overlap_percentage": 0.1,
                "algorithm": "boustrophedon"
            }

            start_time = time.time()
            response = await client.post("/api/v1/trajectories/compute", json=request_data)
            end_time = time.time()

            assert response.status_code == 201
            elapsed_time = (end_time - start_time) * 1000  # Convert to ms
            assert elapsed_time < 5000  # Should complete in under 5 seconds

            # Check that computation time is recorded
            data = response.json()
            assert data["computed_in_ms"] is not None
            assert data["computed_in_ms"] > 0
