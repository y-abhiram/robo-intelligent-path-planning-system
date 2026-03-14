// Wall Finishing Robot - Interactive Frontend
const API_BASE = '/api/v1';

// State
let currentTrajectory = null;
let obstacles = [];
let playbackState = {
    playing: false,
    currentIndex: 0,
    speed: 9,
    animationFrame: null
};

// Canvas setup
const canvas = document.getElementById('canvas');
const ctx = canvas.getContext('2d');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    loadSavedTrajectories();
    addObstacle(); // Add one default obstacle
    renderCanvas();
});

// Add obstacle to the form
function addObstacle() {
    const obstaclesList = document.getElementById('obstaclesList');
    const obstacleId = obstacles.length;

    const obstacleDiv = document.createElement('div');
    obstacleDiv.className = 'obstacle-item';
    obstacleDiv.id = `obstacle-${obstacleId}`;

    obstacleDiv.innerHTML = `
        <div class="obstacle-header">
            <h4>Obstacle ${obstacleId + 1}</h4>
            <button class="btn btn-danger" onclick="removeObstacle(${obstacleId})">Remove</button>
        </div>
        <div class="form-row">
            <div class="form-group">
                <label>X (m):</label>
                <input type="number" id="obs-x-${obstacleId}" value="${obstacleId === 0 ? '2.0' : '0'}" step="0.01" min="0">
            </div>
            <div class="form-group">
                <label>Y (m):</label>
                <input type="number" id="obs-y-${obstacleId}" value="${obstacleId === 0 ? '2.0' : '0'}" step="0.01" min="0">
            </div>
        </div>
        <div class="form-row">
            <div class="form-group">
                <label>Width (m):</label>
                <input type="number" id="obs-w-${obstacleId}" value="0.25" step="0.01" min="0.01">
            </div>
            <div class="form-group">
                <label>Height (m):</label>
                <input type="number" id="obs-h-${obstacleId}" value="0.25" step="0.01" min="0.01">
            </div>
        </div>
    `;

    obstaclesList.appendChild(obstacleDiv);
    obstacles.push(obstacleId);
}

function removeObstacle(obstacleId) {
    const obstacleDiv = document.getElementById(`obstacle-${obstacleId}`);
    if (obstacleDiv) {
        obstacleDiv.remove();
        obstacles = obstacles.filter(id => id !== obstacleId);
    }
}

function getObstacles() {
    return obstacles.map(id => {
        const x = parseFloat(document.getElementById(`obs-x-${id}`).value) || 0;
        const y = parseFloat(document.getElementById(`obs-y-${id}`).value) || 0;
        const width = parseFloat(document.getElementById(`obs-w-${id}`).value) || 0;
        const height = parseFloat(document.getElementById(`obs-h-${id}`).value) || 0;
        return { x, y, width, height, obstacle_type: 'window' };
    });
}

async function computeTrajectory() {
    const loadingIndicator = document.getElementById('loadingIndicator');
    loadingIndicator.style.display = 'block';

    try {
        const wallName = document.getElementById('wallName').value;
        const wallWidth = parseFloat(document.getElementById('wallWidth').value);
        const wallHeight = parseFloat(document.getElementById('wallHeight').value);
        const toolWidth = parseFloat(document.getElementById('toolWidth').value);
        const overlap = parseFloat(document.getElementById('overlap').value) / 100;

        const requestBody = {
            wall: {
                name: wallName,
                width: wallWidth,
                height: wallHeight,
                obstacles: getObstacles()
            },
            tool_width: toolWidth,
            overlap_percentage: overlap,
            algorithm: 'boustrophedon'
        };

        const response = await fetch(`${API_BASE}/trajectories/compute`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(requestBody)
        });

        if (!response.ok) {
            const error = await response.json();
            console.error('API Error:', error);
            const errorMsg = Array.isArray(error.detail)
                ? error.detail.map(e => `${e.loc.join('.')}: ${e.msg}`).join(', ')
                : (typeof error.detail === 'string' ? error.detail : JSON.stringify(error.detail));
            throw new Error(errorMsg || 'Failed to compute trajectory');
        }

        currentTrajectory = await response.json();

        // Store obstacles directly in the trajectory object for easy access
        currentTrajectory.obstacles = requestBody.wall.obstacles;
        currentTrajectory.wallWidth = wallWidth;
        currentTrajectory.wallHeight = wallHeight;

        displayTrajectory(currentTrajectory);
        displayStatistics(currentTrajectory);
        displayPathExplanation(currentTrajectory);
        loadSavedTrajectories();

        showMessage('Trajectory computed successfully!', 'success');
    } catch (error) {
        console.error('Error:', error);
        showMessage(`Error: ${error.message}`, 'error');
    } finally {
        loadingIndicator.style.display = 'none';
    }
}

function displayTrajectory(trajectory) {
    resetTrajectory();
    renderCanvas();
}

function renderCanvas() {
    if (!currentTrajectory) {
        // Draw empty canvas with grid
        drawEmptyCanvas();
        return;
    }

    const wallWidth = currentTrajectory.wallWidth ||
        (currentTrajectory.path_metadata.wall_area ? Math.sqrt(currentTrajectory.path_metadata.wall_area) : 5);
    const wallHeight = currentTrajectory.wallHeight || wallWidth;

    // Clear canvas
    ctx.fillStyle = '#fafafa';
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    // Calculate scale
    const padding = 50;
    const scale = Math.min(
        (canvas.width - 2 * padding) / wallWidth,
        (canvas.height - 2 * padding) / wallHeight
    );

    // Transform: origin at bottom-left
    ctx.save();
    ctx.translate(padding, canvas.height - padding);
    ctx.scale(scale, -scale);

    // Draw grid
    drawGrid(wallWidth, wallHeight, scale);

    // Draw wall boundary
    ctx.strokeStyle = '#1e293b';
    ctx.lineWidth = 2 / scale;
    ctx.strokeRect(0, 0, wallWidth, wallHeight);

    // Draw obstacles directly from stored data
    if (currentTrajectory.obstacles && currentTrajectory.obstacles.length > 0) {
        ctx.fillStyle = 'rgba(239, 68, 68, 0.3)';
        ctx.strokeStyle = '#ef4444';
        ctx.lineWidth = 2 / scale;

        currentTrajectory.obstacles.forEach(obs => {
            ctx.fillRect(obs.x, obs.y, obs.width, obs.height);
            ctx.strokeRect(obs.x, obs.y, obs.width, obs.height);
        });
    }

    // Draw complete path
    drawPath(currentTrajectory.waypoints, scale, playbackState.currentIndex);

    ctx.restore();
}

function drawEmptyCanvas() {
    ctx.fillStyle = '#fafafa';
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    ctx.save();
    ctx.translate(canvas.width / 2, canvas.height / 2);
    ctx.fillStyle = '#94a3b8';
    ctx.font = '16px sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText('Configure wall and compute trajectory to see visualization', 0, 0);
    ctx.restore();
}

function drawGrid(width, height, scale) {
    ctx.strokeStyle = '#e2e8f0';
    ctx.lineWidth = 0.5 / scale;

    // Vertical lines
    for (let x = 0; x <= width; x += 0.5) {
        ctx.beginPath();
        ctx.moveTo(x, 0);
        ctx.lineTo(x, height);
        ctx.stroke();
    }

    // Horizontal lines
    for (let y = 0; y <= height; y += 0.5) {
        ctx.beginPath();
        ctx.moveTo(0, y);
        ctx.lineTo(width, y);
        ctx.stroke();
    }
}

function drawPath(waypoints, scale, currentIndex = -1) {
    if (!waypoints || waypoints.length === 0) return;

    const displayWaypoints = currentIndex >= 0 ?
        waypoints.slice(0, currentIndex + 1) : waypoints;

    // Draw travel lines (move)
    ctx.strokeStyle = '#94a3b8';
    ctx.lineWidth = 1 / scale;
    ctx.setLineDash([0.05, 0.05]);

    for (let i = 1; i < displayWaypoints.length; i++) {
        const prev = displayWaypoints[i - 1];
        const curr = displayWaypoints[i];

        if (prev.action === 'move' || prev.action === 'paint_end') {
            ctx.beginPath();
            ctx.moveTo(prev.x, prev.y);
            ctx.lineTo(curr.x, curr.y);
            ctx.stroke();
        }
    }

    // Draw paint coverage areas and center lines
    ctx.setLineDash([]);

    let painting = false;
    let paintStart = null;

    // Get tool width from trajectory
    const toolWidth = currentTrajectory.tool_width || 0.25;

    for (let i = 0; i < displayWaypoints.length; i++) {
        const wp = displayWaypoints[i];

        if (wp.action === 'paint_start') {
            painting = true;
            paintStart = wp;
        } else if (wp.action === 'paint_end' && paintStart) {
            // Draw the coverage area (semi-transparent rectangle showing painted area)
            ctx.fillStyle = 'rgba(37, 99, 235, 0.15)';
            const x1 = paintStart.x - toolWidth / 2;
            const y1 = Math.min(paintStart.y, wp.y);
            const width = toolWidth;
            const height = Math.abs(wp.y - paintStart.y);
            ctx.fillRect(x1, y1, width, height);

            // Draw center line
            ctx.strokeStyle = '#2563eb';
            ctx.lineWidth = 2 / scale;
            ctx.beginPath();
            ctx.moveTo(paintStart.x, paintStart.y);
            ctx.lineTo(wp.x, wp.y);
            ctx.stroke();

            painting = false;
        }
    }

    // Draw current position
    if (currentIndex >= 0 && currentIndex < waypoints.length) {
        const curr = waypoints[currentIndex];
        ctx.fillStyle = '#f59e0b';
        ctx.beginPath();
        ctx.arc(curr.x, curr.y, 0.08, 0, 2 * Math.PI);
        ctx.fill();
    }

    // Draw waypoint markers
    displayWaypoints.forEach((wp, i) => {
        if (wp.action === 'paint_start' || wp.action === 'paint_end') {
            ctx.fillStyle = wp.action === 'paint_start' ? '#10b981' : '#ef4444';
            ctx.beginPath();
            ctx.arc(wp.x, wp.y, 0.06, 0, 2 * Math.PI);
            ctx.fill();
        }
    });
}

function displayStatistics(trajectory) {
    const stats = document.getElementById('statistics');
    const metadata = trajectory.path_metadata;

    stats.innerHTML = `
        <div class="stat-card">
            <div class="label">Total Distance</div>
            <div class="value">${trajectory.total_distance.toFixed(2)} <span class="unit">m</span></div>
        </div>
        <div class="stat-card">
            <div class="label">Paint Distance</div>
            <div class="value">${metadata.paint_distance.toFixed(2)} <span class="unit">m</span></div>
        </div>
        <div class="stat-card">
            <div class="label">Travel Distance</div>
            <div class="value">${metadata.travel_distance.toFixed(2)} <span class="unit">m</span></div>
        </div>
        <div class="stat-card">
            <div class="label">Waypoints</div>
            <div class="value">${trajectory.total_waypoints}</div>
        </div>
        <div class="stat-card">
            <div class="label">Coverage</div>
            <div class="value">${metadata.coverage_percentage.toFixed(1)} <span class="unit">%</span></div>
        </div>
        <div class="stat-card">
            <div class="label">Est. Time</div>
            <div class="value">${trajectory.estimated_time.toFixed(1)} <span class="unit">s</span></div>
        </div>
        <div class="stat-card">
            <div class="label">Segments</div>
            <div class="value">${metadata.num_segments}</div>
        </div>
        <div class="stat-card">
            <div class="label">Computation Time</div>
            <div class="value">${trajectory.computed_in_ms.toFixed(1)} <span class="unit">ms</span></div>
        </div>
    `;
}

function displayPathExplanation(trajectory) {
    const explanation = document.getElementById('pathExplanation');
    const metadata = trajectory.path_metadata;

    explanation.innerHTML = `
        <h4>Path Planning Explanation</h4>
        <p><strong>Algorithm:</strong> Boustrophedon (Back-and-Forth) Decomposition</p>
        <ul>
            <li><strong>Strategy:</strong> Divides the wall into vertical stripes and covers each stripe with alternating up-down motion</li>
            <li><strong>Tool Width:</strong> ${trajectory.tool_width}m with ${(trajectory.overlap_percentage * 100).toFixed(0)}% overlap</li>
            <li><strong>Effective Stripe Width:</strong> ${(trajectory.tool_width * (1 - trajectory.overlap_percentage)).toFixed(3)}m</li>
            <li><strong>Obstacle Handling:</strong> Automatically splits stripes around obstacles to ensure complete coverage</li>
            <li><strong>Efficiency:</strong> ${((metadata.paint_distance / metadata.total_distance) * 100).toFixed(1)}% of movement is productive painting</li>
            <li><strong>Coverage Area:</strong> ${metadata.effective_area.toFixed(2)}m² (${metadata.wall_area.toFixed(2)}m² wall - ${metadata.obstacle_area.toFixed(2)}m² obstacles)</li>
        </ul>
        <p><strong>Why this works:</strong> The boustrophedon pattern ensures complete coverage while minimizing turns and transitions.
        Obstacles are detected and avoided by segmenting the vertical stripes, ensuring no area is missed.</p>
    `;
}

// Playback controls
function playTrajectory() {
    if (!currentTrajectory || playbackState.playing) return;

    playbackState.playing = true;
    document.getElementById('playBtn').disabled = true;

    function animate() {
        if (!playbackState.playing) return;

        playbackState.currentIndex += playbackState.speed;

        if (playbackState.currentIndex >= currentTrajectory.waypoints.length) {
            playbackState.currentIndex = currentTrajectory.waypoints.length - 1;
            playbackState.playing = false;
            document.getElementById('playBtn').disabled = false;
            return;
        }

        renderCanvas();
        playbackState.animationFrame = requestAnimationFrame(animate);
    }

    animate();
}

function pauseTrajectory() {
    playbackState.playing = false;
    document.getElementById('playBtn').disabled = false;
    if (playbackState.animationFrame) {
        cancelAnimationFrame(playbackState.animationFrame);
    }
}

function resetTrajectory() {
    pauseTrajectory();
    playbackState.currentIndex = 0;
    renderCanvas();
}

function updateSpeed() {
    const speed = document.getElementById('speedControl').value;
    playbackState.speed = parseInt(speed);
    document.getElementById('speedLabel').textContent = speed;
}

function clearCanvas() {
    currentTrajectory = null;
    resetTrajectory();
    renderCanvas();
    document.getElementById('statistics').innerHTML = '';
    document.getElementById('pathExplanation').innerHTML = '';
}

// Load saved trajectories
async function loadSavedTrajectories() {
    try {
        const response = await fetch(`${API_BASE}/trajectories?limit=10`);
        const trajectories = await response.json();

        const container = document.getElementById('savedTrajectories');

        if (trajectories.length === 0) {
            container.innerHTML = '<p style="color: #64748b;">No saved trajectories yet. Compute one to get started!</p>';
            return;
        }

        container.innerHTML = trajectories.map(t => `
            <div class="trajectory-item" onclick="loadTrajectory(${t.id})">
                <div class="trajectory-header">
                    <span class="trajectory-title">Trajectory #${t.id}</span>
                    <span style="font-size: 0.85rem; color: #64748b;">${new Date(t.created_at).toLocaleString()}</span>
                </div>
                <div class="trajectory-meta">
                    <div>Distance: ${t.total_distance.toFixed(2)}m</div>
                    <div>Waypoints: ${t.total_waypoints}</div>
                    <div>Time: ${t.estimated_time.toFixed(1)}s</div>
                </div>
                <div class="trajectory-actions">
                    <button class="btn btn-small btn-primary" onclick="event.stopPropagation(); loadTrajectory(${t.id})">Load</button>
                    <button class="btn btn-small btn-danger" onclick="event.stopPropagation(); deleteTrajectory(${t.id})">Delete</button>
                </div>
            </div>
        `).join('');
    } catch (error) {
        console.error('Error loading trajectories:', error);
    }
}

async function loadTrajectory(id) {
    try {
        // Fetch trajectory
        const response = await fetch(`${API_BASE}/trajectories/${id}`);
        currentTrajectory = await response.json();

        // Fetch wall data to get obstacles
        const wallResponse = await fetch(`${API_BASE}/walls/${currentTrajectory.wall_id}`);
        const wall = await wallResponse.json();

        // Store obstacles and wall dimensions in trajectory
        currentTrajectory.obstacles = wall.obstacles || [];
        currentTrajectory.wallWidth = wall.width;
        currentTrajectory.wallHeight = wall.height;

        displayTrajectory(currentTrajectory);
        displayStatistics(currentTrajectory);
        displayPathExplanation(currentTrajectory);
        showMessage(`Loaded trajectory #${id}`, 'success');
    } catch (error) {
        console.error('Error loading trajectory:', error);
        showMessage(`Error loading trajectory: ${error.message}`, 'error');
    }
}

async function deleteTrajectory(id) {
    if (!confirm(`Delete trajectory #${id}?`)) return;

    try {
        await fetch(`${API_BASE}/trajectories/${id}`, { method: 'DELETE' });
        loadSavedTrajectories();
        showMessage(`Deleted trajectory #${id}`, 'success');
    } catch (error) {
        console.error('Error deleting trajectory:', error);
        showMessage(`Error deleting trajectory: ${error.message}`, 'error');
    }
}

function showMessage(message, type) {
    const container = document.querySelector('.input-panel');
    const messageDiv = document.createElement('div');
    messageDiv.className = type === 'error' ? 'error-message' : 'success-message';
    messageDiv.textContent = message;

    container.insertBefore(messageDiv, container.firstChild);

    setTimeout(() => messageDiv.remove(), 5000);
}
