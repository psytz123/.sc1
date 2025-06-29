"""
Zen-MCP Automation Scheduler

Continuously runs the automated code management system
with configurable intervals and monitoring.
"""

import asyncio
import json
import logging
import signal
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

from zen_code_automation import ZenCodeAutomation

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/automation_scheduler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class AutomationScheduler:
    """
    Scheduler for continuous code automation
    
    Features:
    - Configurable run intervals
    - Health monitoring
    - Graceful shutdown
    - Error recovery
    - Performance metrics
    """
    
    def __init__(self, config_path: str = "config/scheduler_config.json"):
        self.config = self._load_config(config_path)
        self.automation = ZenCodeAutomation()
        self.running = False
        self.last_run: Optional[datetime] = None
        self.run_count = 0
        self.error_count = 0
        self.metrics = {
            "total_runs": 0,
            "successful_runs": 0,
            "failed_runs": 0,
            "total_tasks_completed": 0,
            "average_run_time": 0
        }
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _load_config(self, config_path: str) -> dict:
        """Load scheduler configuration"""
        default_config = {
            "run_interval_minutes": 30,
            "initial_delay_seconds": 10,
            "max_consecutive_errors": 3,
            "error_retry_delay_minutes": 5,
            "working_hours": {
                "enabled": False,
                "start_hour": 9,
                "end_hour": 17,
                "weekends_enabled": False
            },
            "notifications": {
                "enabled": False,
                "webhook_url": "",
                "notify_on_error": True,
                "notify_on_completion": False
            },
            "performance": {
                "max_run_time_minutes": 60,
                "memory_limit_mb": 1024
            }
        }
        
        config_file = Path(config_path)
        if config_file.exists():
            with open(config_file, 'r') as f:
                user_config = json.load(f)
                default_config.update(user_config)
        else:
            # Create default config
            config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(config_file, 'w') as f:
                json.dump(default_config, f, indent=2)
        
        return default_config
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        logger.info(f"Received signal {signum}. Shutting down gracefully...")
        self.running = False
    
    def _should_run_now(self) -> bool:
        """Check if automation should run based on working hours config"""
        if not self.config["working_hours"]["enabled"]:
            return True
        
        now = datetime.now()
        
        # Check weekend
        if now.weekday() >= 5 and not self.config["working_hours"]["weekends_enabled"]:
            return False
        
        # Check working hours
        start_hour = self.config["working_hours"]["start_hour"]
        end_hour = self.config["working_hours"]["end_hour"]
        
        return start_hour <= now.hour < end_hour
    
    async def _run_automation_cycle(self):
        """Run a single automation cycle with monitoring"""
        start_time = datetime.now()
        
        try:
            logger.info(f"Starting automation cycle #{self.run_count + 1}")
            
            # Check if we should run
            if not self._should_run_now():
                logger.info("Outside working hours. Skipping run.")
                return
            
            # Run automation
            await self.automation.run_automation_cycle()
            
            # Generate report
            report = await self.automation.generate_improvement_report()
            
            # Update metrics
            run_time = (datetime.now() - start_time).total_seconds()
            self._update_metrics(True, run_time, report)
            
            # Send notification if enabled
            if self.config["notifications"]["enabled"] and self.config["notifications"]["notify_on_completion"]:
                await self._send_notification(
                    f"✅ Automation cycle #{self.run_count} completed",
                    f"Tasks completed: {report['tasks_completed']}\n"
                    f"Files modified: {len(report['files_modified'])}\n"
                    f"Run time: {run_time:.2f} seconds"
                )
            
            # Reset error count on success
            self.error_count = 0
            
            logger.info(f"Automation cycle completed in {run_time:.2f} seconds")
            
        except Exception as e:
            logger.error(f"Error in automation cycle: {e}", exc_info=True)
            
            # Update metrics
            run_time = (datetime.now() - start_time).total_seconds()
            self._update_metrics(False, run_time)
            
            # Increment error count
            self.error_count += 1
            
            # Send error notification
            if self.config["notifications"]["enabled"] and self.config["notifications"]["notify_on_error"]:
                await self._send_notification(
                    f"❌ Automation cycle #{self.run_count} failed",
                    f"Error: {str(e)}\n"
                    f"Consecutive errors: {self.error_count}"
                )
            
            # Check if we should stop due to too many errors
            if self.error_count >= self.config["max_consecutive_errors"]:
                logger.error(f"Max consecutive errors ({self.error_count}) reached. Stopping scheduler.")
                self.running = False
    
    def _update_metrics(self, success: bool, run_time: float, report: dict = None):
        """Update performance metrics"""
        self.metrics["total_runs"] += 1
        
        if success:
            self.metrics["successful_runs"] += 1
            if report:
                self.metrics["total_tasks_completed"] += report.get("tasks_completed", 0)
        else:
            self.metrics["failed_runs"] += 1
        
        # Update average run time
        current_avg = self.metrics["average_run_time"]
        total_runs = self.metrics["total_runs"]
        self.metrics["average_run_time"] = ((current_avg * (total_runs - 1)) + run_time) / total_runs
        
        self.run_count += 1
        self.last_run = datetime.now()
        
        # Save metrics
        self._save_metrics()
    
    def _save_metrics(self):
        """Save metrics to file"""
        metrics_file = Path("logs/automation_metrics.json")
        metrics_file.parent.mkdir(exist_ok=True)
        
        with open(metrics_file, 'w') as f:
            json.dump({
                **self.metrics,
                "last_run": self.last_run.isoformat() if self.last_run else None,
                "error_count": self.error_count,
                "uptime_hours": (datetime.now() - self.start_time).total_seconds() / 3600 if hasattr(self, 'start_time') else 0
            }, f, indent=2)
    
    async def _send_notification(self, title: str, message: str):
        """Send notification via webhook"""
        if not self.config["notifications"]["webhook_url"]:
            return
        
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                payload = {
                    "title": title,
                    "message": message,
                    "timestamp": datetime.now().isoformat()
                }
                
                async with session.post(
                    self.config["notifications"]["webhook_url"],
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status != 200:
                        logger.warning(f"Failed to send notification: {response.status}")
                        
        except Exception as e:
            logger.warning(f"Error sending notification: {e}")
    
    async def run(self):
        """Main scheduler loop"""
        self.running = True
        self.start_time = datetime.now()
        
        logger.info("🚀 Zen-MCP Automation Scheduler started")
        logger.info(f"Run interval: {self.config['run_interval_minutes']} minutes")
        
        # Initial delay
        if self.config["initial_delay_seconds"] > 0:
            logger.info(f"Waiting {self.config['initial_delay_seconds']} seconds before first run...")
            await asyncio.sleep(self.config["initial_delay_seconds"])
        
        while self.running:
            try:
                # Run automation cycle
                await self._run_automation_cycle()
                
                if not self.running:
                    break
                
                # Calculate next run time
                if self.error_count > 0:
                    # Use error retry delay
                    wait_minutes = self.config["error_retry_delay_minutes"]
                    logger.info(f"Waiting {wait_minutes} minutes before retry (error recovery)...")
                else:
                    # Use normal interval
                    wait_minutes = self.config["run_interval_minutes"]
                    logger.info(f"Waiting {wait_minutes} minutes until next run...")
                
                # Wait for next run
                wait_seconds = wait_minutes * 60
                start_wait = time.time()
                
                while self.running and (time.time() - start_wait) < wait_seconds:
                    # Check every second for shutdown signal
                    await asyncio.sleep(1)
                    
            except Exception as e:
                logger.error(f"Unexpected error in scheduler loop: {e}", exc_info=True)
                await asyncio.sleep(60)  # Wait a minute before retrying
        
        # Cleanup
        await self.automation.close()
        logger.info("✅ Scheduler stopped gracefully")
        
        # Final metrics
        self._print_final_metrics()
    
    def _print_final_metrics(self):
        """Print final metrics summary"""
        print("\n" + "="*50)
        print("📊 AUTOMATION METRICS SUMMARY")
        print("="*50)
        print(f"Total runs: {self.metrics['total_runs']}")
        print(f"Successful runs: {self.metrics['successful_runs']}")
        print(f"Failed runs: {self.metrics['failed_runs']}")
        print(f"Success rate: {(self.metrics['successful_runs'] / max(1, self.metrics['total_runs']) * 100):.1f}%")
        print(f"Total tasks completed: {self.metrics['total_tasks_completed']}")
        print(f"Average run time: {self.metrics['average_run_time']:.2f} seconds")
        
        if hasattr(self, 'start_time'):
            uptime = datetime.now() - self.start_time
            print(f"Total uptime: {uptime}")
        
        print("="*50)


async def main():
    """Main entry point"""
    print("🤖 Zen-MCP Automated Code Management System")
    print("=" * 50)
    
    scheduler = AutomationScheduler()
    
    try:
        await scheduler.run()
    except KeyboardInterrupt:
        print("\n⚠️  Interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        print(f"\n❌ Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())