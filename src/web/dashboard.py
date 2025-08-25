"""
Step 11: Web Dashboard
Flask-based web interface for monitoring and control
"""

from flask import Flask, render_template_string, jsonify, request
import json
from datetime import datetime

app = Flask(__name__)

# Simple HTML template
DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>LinkedIn Scraper Dashboard</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; }
        .card { background: white; padding: 20px; margin: 20px 0; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; }
        .stat { text-align: center; }
        .stat-number { font-size: 2em; font-weight: bold; color: #0066cc; }
        .stat-label { color: #666; }
        .status-active { color: #28a745; }
        .status-inactive { color: #dc3545; }
        button { background: #0066cc; color: white; border: none; padding: 10px 20px; border-radius: 4px; cursor: pointer; }
        button:hover { background: #0052a3; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔗 LinkedIn Scraper Dashboard</h1>
        
        <div class="card">
            <h2>System Status</h2>
            <div class="stats">
                <div class="stat">
                    <div class="stat-number status-active" id="status">Active</div>
                    <div class="stat-label">Scraper Status</div>
                </div>
                <div class="stat">
                    <div class="stat-number" id="profiles-count">0</div>
                    <div class="stat-label">Profiles Scraped</div>
                </div>
                <div class="stat">
                    <div class="stat-number" id="success-rate">0%</div>
                    <div class="stat-label">Success Rate</div>
                </div>
                <div class="stat">
                    <div class="stat-number" id="avg-quality">0.0</div>
                    <div class="stat-label">Avg Quality Score</div>
                </div>
            </div>
        </div>
        
        <div class="card">
            <h2>Quick Actions</h2>
            <button onclick="startScraping()">Start Scraping</button>
            <button onclick="stopScraping()">Stop Scraping</button>
            <button onclick="refreshStats()">Refresh Stats</button>
        </div>
        
        <div class="card">
            <h2>Recent Activity</h2>
            <div id="activity-log">
                <p>No recent activity</p>
            </div>
        </div>
    </div>
    
    <script>
        function refreshStats() {
            fetch('/api/stats')
                .then(response => response.json())
                .then(data => {
                    document.getElementById('profiles-count').textContent = data.profiles_count || 0;
                    document.getElementById('success-rate').textContent = (data.success_rate || 0) + '%';
                    document.getElementById('avg-quality').textContent = (data.avg_quality || 0).toFixed(1);
                });
        }
        
        function startScraping() {
            alert('Scraping started! (Demo)');
        }
        
        function stopScraping() {
            alert('Scraping stopped! (Demo)');
        }
        
        // Auto-refresh every 30 seconds
        setInterval(refreshStats, 30000);
        refreshStats();
    </script>
</body>
</html>
"""

@app.route('/')
def dashboard():
    """Main dashboard page"""
    return render_template_string(DASHBOARD_HTML)

@app.route('/api/stats')
def get_stats():
    """API endpoint for statistics"""
    return jsonify({
        'profiles_count': 42,
        'success_rate': 95,
        'avg_quality': 0.85,
        'status': 'active',
        'last_updated': datetime.now().isoformat()
    })

@app.route('/api/start', methods=['POST'])
def start_scraping():
    """API endpoint to start scraping"""
    return jsonify({'status': 'started', 'message': 'Scraping started successfully'})

@app.route('/api/stop', methods=['POST'])
def stop_scraping():
    """API endpoint to stop scraping"""
    return jsonify({'status': 'stopped', 'message': 'Scraping stopped successfully'})

def run_dashboard(host='127.0.0.1', port=5000, debug=False):
    """Run the dashboard server"""
    app.run(host=host, port=port, debug=debug)

if __name__ == '__main__':
    run_dashboard(debug=True) 