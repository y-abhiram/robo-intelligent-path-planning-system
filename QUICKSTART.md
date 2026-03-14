# Quick Start Guide - Wall Finishing Robot Control System

## Step-by-Step Instructions to Run Locally

### Step 1: Open Terminal
Navigate to the project directory:
```bash
cd /home/jony/Desktop/origin
```

### Step 2: Create Python Virtual Environment
```bash
python3 -m venv venv
```

### Step 3: Activate Virtual Environment
```bash
source venv/bin/activate
```
You should see `(venv)` appear in your terminal prompt.

### Step 4: Install Dependencies
```bash
pip install -r requirements.txt
```
This will install FastAPI, SQLAlchemy, Shapely, and all other required packages.

### Step 5: Start the Server
```bash
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

You should see:
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Step 6: Open in Browser
Open your web browser and go to:
```
http://localhost:8000
```

### Step 7: Test the System
1. **Configure Wall**:
   - Wall Width: 5.0 m
   - Wall Height: 5.0 m
   - Tool Width: 0.25 m
   - Overlap: 10%

2. **Add Obstacle**:
   - Click "+ Add Obstacle"
   - X: 2.0 m
   - Y: 2.0 m
   - Width: 0.25 m
   - Height: 0.25 m

3. **Compute Trajectory**:
   - Click "Compute Trajectory"
   - You should see the blue path lines and light blue coverage areas
   - Obstacle should appear as a red square
   - Coverage should be 100%

4. **Test Playback**:
   - Click "Play" button
   - Adjust speed with slider (try 9x for smooth playback)
   - Watch the orange dot move along the path

### Step 8: View API Documentation
Open in browser:
```
http://localhost:8000/docs
```

This shows all available API endpoints with interactive testing.

---

## Alternative: One-Command Startup

We also provide a convenience script:
```bash
./run.sh
```

This automatically:
- Creates virtual environment (if needed)
- Activates it
- Installs dependencies
- Starts the server

---

## To Stop the Server

Press `Ctrl+C` in the terminal where the server is running.

---

## To Deactivate Virtual Environment

When you're done:
```bash
deactivate
```

---

## Troubleshooting

### Port Already in Use
If you see "Address already in use", kill the existing process:
```bash
pkill -f "uvicorn backend.app.main:app"
```
Then start again.

### Module Not Found Error
Make sure you activated the virtual environment:
```bash
source venv/bin/activate
```

### Database Issues
Delete the database and restart:
```bash
rm backend/wall_robot.db
uvicorn backend.app.main:app --reload
```

---

## Running Tests

### Quick Test (No ROS conflicts)
```bash
python3 quick_test.py
```

### Full Test Suite
```bash
source venv/bin/activate
pytest -v
```

### Specific Test File
```bash
pytest backend/app/tests/test_path_planner.py -v
```

---

## What You Should See

### Main Interface
- **Configuration Panel** (left): Input wall dimensions, obstacles, tool settings
- **Visualization Panel** (right): Canvas showing wall, obstacles, and path
- **Legend**: Explains colors and symbols
- **Statistics Panel**: Shows waypoint count, distance, coverage percentage
- **Path Explanation**: Describes the algorithm and strategy

### Visualization Elements
- **Light Blue Rectangles**: Tool coverage area (0.25m width)
- **Dark Blue Lines**: Tool center path
- **Gray Dashed Lines**: Travel movements (no painting)
- **Green Dots**: Paint start points
- **Red Dots**: Paint end points
- **Red Rectangles**: Obstacles
- **Orange Dot**: Current position during playback

### Expected Performance
- **Computation Time**: 30-50ms for 5m × 5m wall
- **Waypoints**: ~75 for the example case
- **Coverage**: >99%
- **API Response**: <100ms

---

## Example API Usage

### Compute Trajectory via API
```bash
curl -X POST "http://localhost:8000/api/v1/trajectories/compute" \
  -H "Content-Type: application/json" \
  -d '{
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
  }'
```

### Get All Trajectories
```bash
curl "http://localhost:8000/api/v1/trajectories"
```

### Get Statistics
```bash
curl "http://localhost:8000/api/v1/statistics"
```

---

## Success Checklist

When everything is working correctly, you should have:
- ✅ Server running without errors
- ✅ Web interface loads at http://localhost:8000
- ✅ Can compute trajectory for test case
- ✅ Visualization shows complete coverage (light blue rectangles reach edges)
- ✅ Obstacle appears in red
- ✅ Playback animation works
- ✅ Statistics show 100% coverage
- ✅ API docs accessible at /docs

---

## Need Help?

Check the following files:
- [README.md](README.md) - Complete system documentation
- [SETUP.md](SETUP.md) - Detailed setup and configuration guide
- [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) - Technical details and benchmarks
- [FINAL_SUMMARY.txt](FINAL_SUMMARY.txt) - Project completion summary

For issues, check server logs in the terminal where uvicorn is running.
