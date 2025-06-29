"""
Zen-MCP Automation Dashboard

Real-time monitoring dashboard for the automated code management system.
"""

import asyncio
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
        self.zen_url = "http://localhost:5000"
        self.metrics_file = Path("logs/automation_metrics.json")
        self.reports_dir = Path("reports")
        self.refresh_interval = 5  # seconds
        
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
    
    def load_recent_reports(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Load recent improvement reports"""
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
                    timeout=aiohttp.ClientTimeout(total=5)
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


async def main():
    """Main entry point"""
    dashboard = AutomationDashboard()
    
    try:
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