# Setup Guide - Wall Finishing Robot Control System

## Quick Start (5 minutes)

### Option 1: Using the Startup Script (Recommended)

```bash
# Make the script executable (first time only)
chmod +x run.sh

# Run the application
./run.sh
```

That's it! The script will:
1. Create a virtual environment (if needed)
2. Install all dependencies
3. Start the server at http://localhost:8000

### Option 2: Manual Setup

```bash
# 1. Create virtual environment
python3 -m venv venv

# 2. Activate virtual environment
source venv/bin/activate  # On Linux/Mac
# OR
venv\Scripts\activate     # On Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Start the server
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

## Accessing the Application

Once the server is running:

1. **Web Interface**: http://localhost:8000
2. **API Documentation (Swagger)**: http://localhost:8000/docs
3. **API Documentation (ReDoc)**: http://localhost:8000/redoc

## First Steps

### 1. Try the Example Case

Use these parameters to test the system:

- **Wall Name**: Wall-1
- **Wall Width**: 5.0 m
- **Wall Height**: 5.0 m
- **Tool Width**: 0.25 m (25cm)
- **Overlap**: 10%

**Add Obstacle (Window)**:
- **X**: 2.0 m
- **Y**: 2.0 m
- **Width**: 0.25 m (25cm)
- **Height**: 0.25 m (25cm)

Click **"Compute Trajectory"** and watch the magic happen!

### 2. Explore the Visualization

- **Blue lines**: Active painting path
- **Gray dashed lines**: Travel movements (non-painting)
- **Green dots**: Paint start points
- **Red dots**: Paint end points
- **Orange dot**: Current position during playback

### 3. Use Playback Controls

- **Play**: Animate the trajectory
- **Pause**: Pause the animation
- **Reset**: Return to the beginning
- **Speed Slider**: Adjust playback speed (1-100x)

### 4. Check Statistics

View real-time metrics:
- Total distance traveled
- Paint vs travel distance
- Coverage percentage
- Estimated completion time
- Number of waypoints
- Computation time

## Testing the System

### Run All Tests

```bash
pytest
```

### Run Specific Tests

```bash
# Path planning tests
pytest backend/app/tests/test_path_planner.py -v

# API tests
pytest backend/app/tests/test_api.py -v
```

### Expected Test Results

You should see output similar to:
```
==================== test session starts ====================
collected 25 items

backend/app/tests/test_api.py::TestHealthCheck::test_health_check PASSED
backend/app/tests/test_api.py::TestWallEndpoints::test_create_wall PASSED
...
==================== 25 passed in 2.43s ====================
```

## API Usage Examples

### Using cURL

**Compute a trajectory**:
```bash
curl -X POST "http://localhost:8000/api/v1/trajectories/compute" \
  -H "Content-Type: application/json" \
  -d '{
    "wall": {
      "name": "Wall-1",
      "width": 5.0,
      "height": 5.0,
      "obstacles": [
        {"x": 2.0, "y": 2.0, "width": 0.25, "height": 0.25}
      ]
    },
    "tool_width": 0.25,
    "overlap_percentage": 0.1,
    "algorithm": "boustrophedon"
  }'
```

**Get all trajectories**:
```bash
curl "http://localhost:8000/api/v1/trajectories"
```

**Get system statistics**:
```bash
curl "http://localhost:8000/api/v1/statistics"
```

### Using Python

```python
import requests

# Compute trajectory
response = requests.post(
    "http://localhost:8000/api/v1/trajectories/compute",
    json={
        "wall": {
            "name": "Wall-1",
            "width": 5.0,
            "height": 5.0,
            "obstacles": [
                {"x": 2.0, "y": 2.0, "width": 0.25, "height": 0.25}
            ]
        },
        "tool_width": 0.25,
        "overlap_percentage": 0.1,
        "algorithm": "boustrophedon"
    }
)

trajectory = response.json()
print(f"Computed {trajectory['total_waypoints']} waypoints")
print(f"Total distance: {trajectory['total_distance']:.2f}m")
print(f"Coverage: {trajectory['metadata']['coverage_percentage']:.1f}%")
```

## Understanding the Database

### Database Location
- Development: `./wall_robot.db`
- Test: In-memory SQLite database

### Database Schema

**Tables**:
1. `walls` - Wall configurations
2. `obstacles` - Obstacles on walls
3. `trajectories` - Computed trajectories
4. `waypoints` - Individual points in trajectories

### Viewing the Database

You can inspect the database using SQLite tools:

```bash
# Install sqlite3 (if not already installed)
# On Ubuntu/Debian:
sudo apt-get install sqlite3

# Open database
sqlite3 wall_robot.db

# View tables
.tables

# View schema
.schema trajectories

# Query data
SELECT id, total_waypoints, total_distance, computed_in_ms
FROM trajectories
ORDER BY created_at DESC
LIMIT 5;

# Exit
.quit
```

## Performance Tuning

### For Large Walls

If computing trajectories for very large walls (>20m × 20m):

1. **Increase tool width** to reduce waypoint count
2. **Reduce overlap percentage** to speed up computation
3. **Monitor computation time** in statistics

### For Production Use

Update `backend/app/core/config.py`:

```python
# Increase cache size for better performance
PRAGMA cache_size=-128000  # 128MB instead of 64MB

# Adjust log level
LOG_LEVEL: str = "WARNING"  # Instead of "INFO"
```

## Troubleshooting

### Issue: "ModuleNotFoundError"

**Solution**: Make sure virtual environment is activated and dependencies are installed
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### Issue: "Address already in use"

**Solution**: Port 8000 is in use. Either:
1. Kill the process: `lsof -ti:8000 | xargs kill -9`
2. Use a different port: `uvicorn backend.app.main:app --port 8001`

### Issue: "Database is locked"

**Solution**:
1. Close other connections to the database
2. Delete `wall_robot.db` and restart (data will be lost)
3. WAL mode should prevent this (it's enabled by default)

### Issue: Canvas not showing

**Solution**:
1. Check browser console for errors (F12)
2. Ensure JavaScript is enabled
3. Try clearing browser cache
4. Verify static files are being served: http://localhost:8000/static/js/app.js

### Issue: Tests failing

**Solution**:
1. Make sure pytest is installed: `pip install pytest pytest-asyncio httpx`
2. Run from project root: `cd /path/to/origin && pytest`
3. Check for port conflicts during tests

## Development Tips

### Enable Debug Mode

Edit `backend/app/core/config.py`:
```python
DATABASE_ECHO: bool = True  # Show SQL queries
LOG_LEVEL: str = "DEBUG"    # Verbose logging
```

### Watch Logs

Logs are written to:
- Console output (stdout)
- `robot_control.log` file

Tail the log file:
```bash
tail -f robot_control.log
```

### Hot Reload

The server runs with `--reload` flag, so any code changes automatically restart the server.

### Database Migrations

For schema changes:
1. Delete `wall_robot.db`
2. Restart server (tables will be recreated)

For production, consider using Alembic for migrations.

## Advanced Configuration

### Environment Variables

Create a `.env` file:
```env
DATABASE_URL=sqlite+aiosqlite:///./wall_robot.db
LOG_LEVEL=INFO
API_TITLE=Wall Finishing Robot Control System
API_VERSION=1.0.0
DEFAULT_TOOL_WIDTH=0.25
OVERLAP_PERCENTAGE=0.1
DEFAULT_SPEED=0.5
```

### Custom Port

```bash
uvicorn backend.app.main:app --reload --port 8080
```

### Multiple Workers (Production)

```bash
uvicorn backend.app.main:app --workers 4 --host 0.0.0.0 --port 8000
```

## Next Steps

1. ✅ Complete the setup
2. ✅ Test with the example case
3. ✅ Explore the API documentation
4. ✅ Run the test suite
5. ✅ Try different wall sizes and obstacle configurations
6. ✅ Review the code and implementation

## Support

For issues or questions:
1. Check this guide first
2. Review the main README.md
3. Check the API documentation at /docs
4. Review the code comments

Happy robot path planning! 🤖
