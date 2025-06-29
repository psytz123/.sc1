"""
Zen-MCP Automation Dashboard

Real-time monitoring dashboard for the automated code management system.
"""

import asyncio
import os
from utils.logger import get_logger

logger = get_logger(__name__)
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List

import aiohttp
import plotext as plt
from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv is optional


class AutomationDashboard:
    """
    Real-time monitoring dashboard for zen-mcp automation
    
    Features:
    - Live metrics display
    - Task queue monitoring
    - Performance graphs
    - Error tracking
    - File change history
    """
    
    def __init__(self):
        self.console = Console()
        self.zen_url = os.getenv("ZEN_SERVER_URL", "http://localhost:5000")
        self.metrics_file = Path(os.getenv("METRICS_FILE", "logs/automation_metrics.json"))
        self.reports_dir = Path(os.getenv("REPORTS_DIR", "reports"))
        self.refresh_interval = int(os.getenv("DASHBOARD_REFRESH_INTERVAL", "5"))
        self.host = os.getenv("DASHBOARD_HOST", "localhost")
        self.port = int(os.getenv("DASHBOARD_PORT", "8080"))
        self.max_reports = int(os.getenv("MAX_RECENT_REPORTS", "5"))
        self.timeout = int(os.getenv("ZEN_SERVER_TIMEOUT", "5"))
        
    def load_metrics(self) -> Dict[str, Any]:
        """Load current metrics from file"""
        if self.metrics_file.exists():
            with open(self.metrics_file, 'r') as f:
                return json.load(f)
        return {
            "total_runs": 0,
            "successful_runs": 0,
            "failed_runs": 0,
            "total_tasks_completed": 0,
            "average_run_time": 0,
            "last_run": None,
            "error_count": 0,
            "uptime_hours": 0
        }
    
    def load_recent_reports(self, limit: int = None) -> List[Dict[str, Any]]:
        """Load recent improvement reports"""
        if limit is None:
            limit = self.max_reports
        
        reports = []
        
        if self.reports_dir.exists():
            report_files = sorted(
                self.reports_dir.glob("improvement_report_*.json"),
                key=lambda p: p.stat().st_mtime,
                reverse=True
            )[:limit]
            
            for report_file in report_files:
                with open(report_file, 'r') as f:
                    reports.append(json.load(f))
        
        return reports
    
    async def check_zen_server_status(self) -> bool:
        """Check if zen-mcp-server is running"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.zen_url}/version",
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as response:
                    return response.status == 200
        except:
            return False
    
    def create_metrics_table(self, metrics: Dict[str, Any]) -> Table:
        """Create metrics summary table"""
        table = Table(title="📊 Automation Metrics", show_header=True)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        
        # Calculate success rate
        success_rate = 0
        if metrics["total_runs"] > 0:
            success_rate = (metrics["successful_runs"] / metrics["total_runs"]) * 100
        
        # Add rows
        table.add_row("Total Runs", str(metrics["total_runs"]))
        table.add_row("Successful Runs", str(metrics["successful_runs"]))
        table.add_row("Failed Runs", str(metrics["failed_runs"]))
        table.add_row("Success Rate", f"{success_rate:.1f}%")
        table.add_row("Tasks Completed", str(metrics["total_tasks_completed"]))
        table.add_row("Avg Run Time", f"{metrics['average_run_time']:.2f}s")
        table.add_row("Current Errors", str(metrics["error_count"]))
        table.add_row("Uptime", f"{metrics['uptime_hours']:.1f} hours")
        
        if metrics["last_run"]:
            last_run = datetime.fromisoformat(metrics["last_run"])
            time_ago = datetime.now() - last_run
            table.add_row("Last Run", f"{self._format_time_ago(time_ago)} ago")
        
        return table
    
    def create_recent_tasks_table(self, reports: List[Dict[str, Any]]) -> Table:
        """Create table of recent tasks"""
        table = Table(title="🔧 Recent Improvements", show_header=True)
        table.add_column("Time", style="cyan", width=20)
        table.add_column("Type", style="yellow")
        table.add_column("File", style="blue")
        table.add_column("Description", style="white")
        
        for report in reports:
            if "improvements" in report:
                for improvement in report["improvements"][:3]:  # Show top 3 per report
                    time_str = improvement.get("completed_at", report.get("timestamp", ""))
                    if time_str:
                        time_obj = datetime.fromisoformat(time_str)
                        time_ago = self._format_time_ago(datetime.now() - time_obj)
                    else:
                        time_ago = "Unknown"
                    
                    file_path = Path(improvement.get("file", "Unknown"))
                    table.add_row(
                        time_ago,
                        improvement.get("type", "Unknown"),
                        file_path.name,
                        improvement.get("description", "")[:50] + "..."
                    )
        
        return table
    
    def create_performance_graph(self, reports: List[Dict[str, Any]]) -> str:
        """Create performance graph"""
        if not reports:
            return "No data available for graph"
        
        # Extract task counts over time
        timestamps = []
        task_counts = []
        
        for report in reversed(reports):  # Chronological order
            if "timestamp" in report:
                timestamps.append(datetime.fromisoformat(report["timestamp"]))
                task_counts.append(report.get("tasks_completed", 0))
        
        if not timestamps:
            return "No timestamp data available"
        
        # Create plot
        plt.clear_figure()
        plt.theme("dark")
        plt.plot_size(60, 15)
        
        # Convert timestamps to hours ago
        now = datetime.now()
        hours_ago = [(now - ts).total_seconds() / 3600 for ts in timestamps]
        
        plt.plot(hours_ago, task_counts)
        plt.title("Tasks Completed Over Time")
        plt.xlabel("Hours Ago")
        plt.ylabel("Tasks")
        
        return plt.build()
    
    def _format_time_ago(self, delta: timedelta) -> str:
        """Format timedelta as human-readable string"""
        seconds = int(delta.total_seconds())
        
        if seconds < 60:
            return f"{seconds}s"
        elif seconds < 3600:
            return f"{seconds // 60}m"
        elif seconds < 86400:
            return f"{seconds // 3600}h {(seconds % 3600) // 60}m"
        else:
            return f"{seconds // 86400}d {(seconds % 86400) // 3600}h"
    
    def create_layout(self) -> Layout:
        """Create dashboard layout"""
        layout = Layout()
        
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="body"),
            Layout(name="footer", size=3)
        )
        
        layout["body"].split_row(
            Layout(name="left"),
            Layout(name="right")
        )
        
        layout["left"].split_column(
            Layout(name="metrics", size=15),
            Layout(name="graph")
        )
        
        layout["right"].split_column(
            Layout(name="status", size=10),
            Layout(name="tasks")
        )
        
        return layout
    
    async def update_dashboard(self, layout: Layout):
        """Update dashboard with latest data"""
        # Load data
        metrics = self.load_metrics()
        reports = self.load_recent_reports()
        zen_status = await self.check_zen_server_status()
        
        # Update header
        header_text = Text("🤖 Zen-MCP Automated Code Management Dashboard", style="bold blue")
        header_text.append(f"\n{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", style="dim")
        layout["header"].update(Panel(header_text, border_style="blue"))
        
        # Update metrics
        layout["metrics"].update(self.create_metrics_table(metrics))
        
        # Update graph
        graph = self.create_performance_graph(reports)
        layout["graph"].update(Panel(graph, title="📈 Performance Trend", border_style="green"))
        
        # Update status
        status_table = Table(show_header=False)
        status_table.add_column("Status", style="cyan")
        status_table.add_column("Value", style="white")
        
        zen_status_text = "✅ Running" if zen_status else "❌ Not Running"
        zen_style = "green" if zen_status else "red"
        status_table.add_row("Zen-MCP Server", Text(zen_status_text, style=zen_style))
        
        # Check if automation is running
        automation_running = False
        if metrics["last_run"]:
            last_run = datetime.fromisoformat(metrics["last_run"])
            time_since = datetime.now() - last_run
            # Consider running if last run was within 2x the expected interval
            automation_running = time_since.total_seconds() < 3600  # 1 hour threshold
        
        auto_status_text = "✅ Active" if automation_running else "⚠️  Inactive"
        auto_style = "green" if automation_running else "yellow"
        status_table.add_row("Automation", Text(auto_status_text, style=auto_style))
        
        layout["status"].update(Panel(status_table, title="🔌 System Status", border_style="cyan"))
        
        # Update recent tasks
        layout["tasks"].update(self.create_recent_tasks_table(reports))
        
        # Update footer
        footer_text = "Press Ctrl+C to exit | Refreshing every 5 seconds"
        layout["footer"].update(Panel(footer_text, border_style="dim"))
    
    async def run(self):
        """Run the dashboard"""
        layout = self.create_layout()
        
        with Live(layout, refresh_per_second=1, screen=True) as live:
            while True:
                try:
                    await self.update_dashboard(layout)
                    await asyncio.sleep(self.refresh_interval)
                except KeyboardInterrupt:
                    break
                except Exception as e:
                    self.console.logger.info(f"[red]Error updating dashboard: {e}[/red]")
                    await asyncio.sleep(self.refresh_interval)
    
    async def run_web_interface(self):
        """Run dashboard as a web interface"""
        from aiohttp import web, web_runner
        
        async def health_check(request):
            """Health check endpoint"""
            return web.json_response({"status": "healthy", "timestamp": datetime.now().isoformat()})
        
        async def metrics_endpoint(request):
            """Metrics API endpoint"""
            metrics = self.load_metrics()
            reports = self.load_recent_reports()
            zen_status = await self.check_zen_server_status()
            
            return web.json_response({
                "metrics": metrics,
                "reports": reports,
                "zen_server_status": zen_status,
                "timestamp": datetime.now().isoformat()
            })
        
        async def dashboard_html(request):
            """Serve dashboard HTML page"""
            html = """
<!DOCTYPE html>
<html>
<head>
    <title>Zen-MCP Dashboard</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #1a1a1a; color: #fff; }
        .container { max-width: 1200px; margin: 0 auto; }
        .header { text-align: center; margin-bottom: 30px; }
        .metrics-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }
        .card { background: #2a2a2a; padding: 20px; border-radius: 8px; border: 1px solid #3a3a3a; }
        .metric { display: flex; justify-content: space-between; margin: 10px 0; }
        .metric-label { color: #aaa; }
        .metric-value { color: #0ff; font-weight: bold; }
        .status-ok { color: #0f0; }
        .status-error { color: #f00; }
        .refresh-info { text-align: center; margin-top: 20px; color: #666; }
    </style>
    <script>
        async function updateDashboard() {
            try {
                const response = await fetch('/api/metrics');
                const data = await response.json();
                
                // Update metrics
                const metrics = data.metrics;
                document.getElementById('total-runs').textContent = metrics.total_runs;
                document.getElementById('successful-runs').textContent = metrics.successful_runs;
                document.getElementById('failed-runs').textContent = metrics.failed_runs;
                document.getElementById('success-rate').textContent = 
                    metrics.total_runs > 0 ? ((metrics.successful_runs / metrics.total_runs) * 100).toFixed(1) + '%' : '0%';
                document.getElementById('tasks-completed').textContent = metrics.total_tasks_completed;
                document.getElementById('avg-runtime').textContent = metrics.average_run_time.toFixed(2) + 's';
                document.getElementById('error-count').textContent = metrics.error_count;
                document.getElementById('uptime').textContent = metrics.uptime_hours.toFixed(1) + 'h';
                
                // Update status
                const zenStatus = data.zen_server_status;
                const statusElement = document.getElementById('zen-status');
                statusElement.textContent = zenStatus ? 'Running' : 'Not Running';
                statusElement.className = zenStatus ? 'status-ok' : 'status-error';
                
                document.getElementById('last-update').textContent = new Date().toLocaleTimeString();
            } catch (error) {
                console.error('Error updating dashboard:', error);
            }
        }
        
        // Update every 5 seconds
        setInterval(updateDashboard, 5000);
        updateDashboard(); // Initial load
    </script>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 Zen-MCP Automation Dashboard</h1>
            <p>Real-time monitoring for automated code management</p>
        </div>
        
        <div class="metrics-grid">
            <div class="card">
                <h3>📊 Automation Metrics</h3>
                <div class="metric">
                    <span class="metric-label">Total Runs:</span>
                    <span class="metric-value" id="total-runs">0</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Successful Runs:</span>
                    <span class="metric-value" id="successful-runs">0</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Failed Runs:</span>
                    <span class="metric-value" id="failed-runs">0</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Success Rate:</span>
                    <span class="metric-value" id="success-rate">0%</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Tasks Completed:</span>
                    <span class="metric-value" id="tasks-completed">0</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Avg Runtime:</span>
                    <span class="metric-value" id="avg-runtime">0s</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Current Errors:</span>
                    <span class="metric-value" id="error-count">0</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Uptime:</span>
                    <span class="metric-value" id="uptime">0h</span>
                </div>
            </div>
            
            <div class="card">
                <h3>🔌 System Status</h3>
                <div class="metric">
                    <span class="metric-label">Zen-MCP Server:</span>
                    <span class="metric-value" id="zen-status">Checking...</span>
                </div>
            </div>
        </div>
        
        <div class="refresh-info">
            Last updated: <span id="last-update">Loading...</span>
        </div>
    </div>
</body>
</html>
            """
            return web.Response(text=html, content_type='text/html')
        
        # Create web application
        app = web.Application()
        app.router.add_get('/', dashboard_html)
        app.router.add_get('/health', health_check)
        app.router.add_get('/api/metrics', metrics_endpoint)
        
        # Start server
        runner = web_runner.AppRunner(app)
        await runner.setup()
        site = web_runner.TCPSite(runner, self.host, self.port)
        await site.start()
        
        self.console.print(f"✅ Web dashboard started at http://{self.host}:{self.port}")
        self.console.print("Press Ctrl+C to stop")
        
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            pass
        finally:
            await runner.cleanup()


async def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Zen-MCP Automation Dashboard")
    parser.add_argument(
        "--mode", 
        choices=["terminal", "web"], 
        default="terminal",
        help="Dashboard mode: terminal (rich TUI) or web (HTTP server)"
    )
    parser.add_argument(
        "--host",
        default=os.getenv("DASHBOARD_HOST", "localhost"),
        help="Host to bind web server to"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.getenv("DASHBOARD_PORT", "8080")),
        help="Port for web server"
    )
    
    args = parser.parse_args()
    
    dashboard = AutomationDashboard()
    
    # Override host/port if provided via command line
    if args.host != "localhost":
        dashboard.host = args.host
    if args.port != 8080:
        dashboard.port = args.port
    
    try:
        if args.mode == "web":
            await dashboard.run_web_interface()
        else:
            await dashboard.run()
    except KeyboardInterrupt:
        logger.info("\n✅ Dashboard closed")


if __name__ == "__main__":
    # Check if required libraries are installed
    try:
        import plotext
    except ImportError:
        logger.info("Please install required libraries:")
        logger.info("pip install rich plotext")
        exit(1)
    
    asyncio.run(main())