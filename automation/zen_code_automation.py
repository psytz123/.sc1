"""
Zen-MCP Automated Code Management System

This module provides automated code management, continuous improvement,
and intelligent maintenance using zen-mcp-server capabilities.
"""

import asyncio
import hashlib
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

import aiohttp
import git

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/zen_automation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class TaskPriority(Enum):
    """Priority levels for automated tasks"""
    CRITICAL = 1  # Security issues, breaking changes
    HIGH = 2      # Performance issues, bugs
    MEDIUM = 3    # Code quality, refactoring
    LOW = 4       # Documentation, style improvements


@dataclass
class AutomationTask:
    """Represents an automation task"""
    id: str
    type: str
    priority: TaskPriority
    file_path: Optional[str] = None
    description: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    completed: bool = False


class ZenCodeAutomation:
    """
    Automated code management system using zen-mcp-server
    
    Features:
    - Continuous code analysis and improvement
    - Automated refactoring and optimization
    - Security vulnerability detection
    - Documentation generation and updates
    - Test coverage improvement
    - Performance optimization
    """
    
    def __init__(self, config_path: str = "config/automation_config.json"):
        self.config = self._load_config(config_path)
        self.zen_url = self.config.get("zen_server_url", "http://localhost:5000")
        self.session: Optional[aiohttp.ClientSession] = None
        self.task_queue: List[AutomationTask] = []
        self.processed_files: Set[str] = set()
        self.last_analysis: Dict[str, datetime] = {}
        self.repo = self._init_git_repo()
        
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load automation configuration"""
        default_config = {
            "zen_server_url": "http://localhost:5000",
            "scan_interval_minutes": 30,
            "auto_commit": False,
            "auto_pr": True,
            "excluded_paths": ["__pycache__", ".git", "node_modules", "venv"],
            "file_patterns": ["*.py", "*.js", "*.ts", "*.jsx", "*.tsx"],
            "max_concurrent_tasks": 3,
            "task_priorities": {
                "security": "CRITICAL",
                "bug_fix": "HIGH",
                "performance": "HIGH",
                "refactor": "MEDIUM",
                "documentation": "LOW"
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
    
    def _init_git_repo(self) -> Optional[git.Repo]:
        """Initialize git repository if available"""
        try:
            return git.Repo(search_parent_directories=True)
        except:
            logger.warning("Git repository not found. Git features will be disabled.")
            return None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=300)
            )
        return self.session
    
    async def _call_zen_tool(self, tool: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Call a zen-mcp-server tool"""
        try:
            session = await self._get_session()
            url = f"{self.zen_url}/{tool}"
            
            async with session.post(url, json=params) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    logger.error(f"Zen tool {tool} failed: {error_text}")
                    return {"status": "error", "message": error_text}
                    
        except Exception as e:
            logger.error(f"Error calling zen tool {tool}: {e}")
            return {"status": "error", "message": str(e)}
    
    async def analyze_codebase(self) -> List[AutomationTask]:
        """
        Perform comprehensive codebase analysis
        
        Returns list of automation tasks to perform
        """
        logger.info("Starting comprehensive codebase analysis...")
        tasks = []
        
        # Get all relevant files
        files_to_analyze = self._get_files_to_analyze()
        
        for file_path in files_to_analyze:
            # Skip recently analyzed files
            if self._was_recently_analyzed(file_path):
                continue
                
            # Analyze file with multiple zen tools
            analysis_tasks = await self._analyze_file(file_path)
            tasks.extend(analysis_tasks)
            
            # Update last analysis time
            self.last_analysis[file_path] = datetime.now()
        
        # Sort tasks by priority
        tasks.sort(key=lambda t: t.priority.value)
        
        logger.info(f"Analysis complete. Found {len(tasks)} improvement tasks.")
        return tasks
    
    def _get_files_to_analyze(self) -> List[Path]:
        """Get list of files to analyze based on patterns and exclusions"""
        files = []
        root_path = Path.cwd()
        
        for pattern in self.config["file_patterns"]:
            for file_path in root_path.rglob(pattern):
                # Check exclusions
                if any(excluded in str(file_path) for excluded in self.config["excluded_paths"]):
                    continue
                    
                files.append(file_path)
        
        return files
    
    def _was_recently_analyzed(self, file_path: Path) -> bool:
        """Check if file was recently analyzed"""
        if str(file_path) not in self.last_analysis:
            return False
            
        last_time = self.last_analysis[str(file_path)]
        interval = timedelta(minutes=self.config["scan_interval_minutes"])
        
        return datetime.now() - last_time < interval
    
    async def _analyze_file(self, file_path: Path) -> List[AutomationTask]:
        """Analyze a single file and generate improvement tasks"""
        tasks = []
        file_str = str(file_path)
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            logger.error(f"Error reading {file_path}: {e}")
            return tasks
        
        # 1. Code Review
        review_result = await self._call_zen_tool("codereview", {
            "code": content,
            "filename": file_str,
            "language": file_path.suffix[1:]  # Remove the dot
        })
        
        if review_result.get("status") != "error":
            tasks.extend(self._parse_review_results(review_result, file_path))
        
        # 2. Security Audit
        security_result = await self._call_zen_tool("secaudit", {
            "code": content,
            "filename": file_str
        })
        
        if security_result.get("status") != "error":
            tasks.extend(self._parse_security_results(security_result, file_path))
        
        # 3. Performance Analysis
        analyze_result = await self._call_zen_tool("analyze", {
            "code": content,
            "focus": "performance optimization"
        })
        
        if analyze_result.get("status") != "error":
            tasks.extend(self._parse_analysis_results(analyze_result, file_path))
        
        # 4. Documentation Check
        if self._needs_documentation(content, file_path):
            doc_task = AutomationTask(
                id=self._generate_task_id("doc", file_path),
                type="documentation",
                priority=TaskPriority.LOW,
                file_path=file_str,
                description=f"Generate/update documentation for {file_path.name}"
            )
            tasks.append(doc_task)
        
        return tasks
    
    def _parse_review_results(self, result: Dict[str, Any], file_path: Path) -> List[AutomationTask]:
        """Parse code review results into tasks"""
        tasks = []
        
        # Extract issues from review
        if "issues" in result:
            for issue in result["issues"]:
                priority = self._determine_priority(issue.get("severity", "medium"))
                task = AutomationTask(
                    id=self._generate_task_id("review", file_path),
                    type="code_improvement",
                    priority=priority,
                    file_path=str(file_path),
                    description=issue.get("description", "Code improvement needed"),
                    metadata={"issue": issue}
                )
                tasks.append(task)
        
        return tasks
    
    def _parse_security_results(self, result: Dict[str, Any], file_path: Path) -> List[AutomationTask]:
        """Parse security audit results into tasks"""
        tasks = []
        
        if "vulnerabilities" in result:
            for vuln in result["vulnerabilities"]:
                task = AutomationTask(
                    id=self._generate_task_id("security", file_path),
                    type="security_fix",
                    priority=TaskPriority.CRITICAL,
                    file_path=str(file_path),
                    description=f"Security: {vuln.get('type', 'Unknown vulnerability')}",
                    metadata={"vulnerability": vuln}
                )
                tasks.append(task)
        
        return tasks
    
    def _parse_analysis_results(self, result: Dict[str, Any], file_path: Path) -> List[AutomationTask]:
        """Parse analysis results into tasks"""
        tasks = []
        
        if "optimizations" in result:
            for opt in result["optimizations"]:
                task = AutomationTask(
                    id=self._generate_task_id("optimize", file_path),
                    type="performance",
                    priority=TaskPriority.HIGH,
                    file_path=str(file_path),
                    description=opt.get("description", "Performance optimization"),
                    metadata={"optimization": opt}
                )
                tasks.append(task)
        
        return tasks
    
    def _needs_documentation(self, content: str, file_path: Path) -> bool:
        """Check if file needs documentation"""
        # Simple heuristic: check for docstrings in Python files
        if file_path.suffix == '.py':
            # Check for module docstring
            if not content.strip().startswith('"""') and not content.strip().startswith("'''"):
                return True
            
            # Check for undocumented functions/classes
            import re
            functions = re.findall(r'^def\s+\w+\s*\(', content, re.MULTILINE)
            classes = re.findall(r'^class\s+\w+', content, re.MULTILINE)
            
            # If there are many functions/classes, likely needs better docs
            if len(functions) + len(classes) > 5:
                return True
        
        return False
    
    def _determine_priority(self, severity: str) -> TaskPriority:
        """Determine task priority from severity"""
        severity_map = {
            "critical": TaskPriority.CRITICAL,
            "high": TaskPriority.HIGH,
            "medium": TaskPriority.MEDIUM,
            "low": TaskPriority.LOW
        }
        return severity_map.get(severity.lower(), TaskPriority.MEDIUM)
    
    def _generate_task_id(self, task_type: str, file_path: Path) -> str:
        """Generate unique task ID"""
        timestamp = datetime.now().isoformat()
        content = f"{task_type}:{file_path}:{timestamp}"
        return hashlib.md5(content.encode()).hexdigest()[:8]
    
    async def execute_task(self, task: AutomationTask) -> bool:
        """Execute a single automation task"""
        logger.info(f"Executing task {task.id}: {task.description}")
        
        try:
            if task.type == "code_improvement":
                return await self._execute_code_improvement(task)
            elif task.type == "security_fix":
                return await self._execute_security_fix(task)
            elif task.type == "performance":
                return await self._execute_performance_optimization(task)
            elif task.type == "documentation":
                return await self._execute_documentation_generation(task)
            else:
                logger.warning(f"Unknown task type: {task.type}")
                return False
                
        except Exception as e:
            logger.error(f"Error executing task {task.id}: {e}")
            return False
    
    async def _execute_code_improvement(self, task: AutomationTask) -> bool:
        """Execute code improvement task"""
        if not task.file_path:
            return False
            
        # Read current code
        with open(task.file_path, 'r', encoding='utf-8') as f:
            current_code = f.read()
        
        # Use zen refactor tool
        result = await self._call_zen_tool("refactor", {
            "code": current_code,
            "focus": task.metadata.get("issue", {}).get("type", "general improvement"),
            "filename": task.file_path
        })
        
        if result.get("status") != "error" and "refactored_code" in result:
            # Create backup
            self._backup_file(task.file_path)
            
            # Write improved code
            with open(task.file_path, 'w', encoding='utf-8') as f:
                f.write(result["refactored_code"])
            
            # Log the improvement
            logger.info(f"Applied code improvement to {task.file_path}")
            
            # Create commit if enabled
            if self.config["auto_commit"] and self.repo:
                self._create_commit(task)
            
            return True
        
        return False
    
    async def _execute_security_fix(self, task: AutomationTask) -> bool:
        """Execute security fix task"""
        if not task.file_path:
            return False
            
        # Read current code
        with open(task.file_path, 'r', encoding='utf-8') as f:
            current_code = f.read()
        
        # Use zen debug tool with security focus
        result = await self._call_zen_tool("debug", {
            "code": current_code,
            "error_description": f"Security vulnerability: {task.description}",
            "filename": task.file_path
        })
        
        if result.get("status") != "error" and "fixed_code" in result:
            # Create backup
            self._backup_file(task.file_path)
            
            # Write fixed code
            with open(task.file_path, 'w', encoding='utf-8') as f:
                f.write(result["fixed_code"])
            
            logger.info(f"Applied security fix to {task.file_path}")
            
            # Always commit security fixes
            if self.repo:
                self._create_commit(task, prefix="[SECURITY]")
            
            return True
        
        return False
    
    async def _execute_performance_optimization(self, task: AutomationTask) -> bool:
        """Execute performance optimization task"""
        if not task.file_path:
            return False
            
        # Read current code
        with open(task.file_path, 'r', encoding='utf-8') as f:
            current_code = f.read()
        
        # Use zen analyze tool for optimization
        result = await self._call_zen_tool("analyze", {
            "code": current_code,
            "focus": "performance optimization with code suggestions"
        })
        
        if result.get("status") != "error" and "optimized_code" in result:
            # Create backup
            self._backup_file(task.file_path)
            
            # Write optimized code
            with open(task.file_path, 'w', encoding='utf-8') as f:
                f.write(result["optimized_code"])
            
            logger.info(f"Applied performance optimization to {task.file_path}")
            
            if self.config["auto_commit"] and self.repo:
                self._create_commit(task, prefix="[PERF]")
            
            return True
        
        return False
    
    async def _execute_documentation_generation(self, task: AutomationTask) -> bool:
        """Execute documentation generation task"""
        if not task.file_path:
            return False
            
        # Read current code
        with open(task.file_path, 'r', encoding='utf-8') as f:
            current_code = f.read()
        
        # Use zen docgen tool
        result = await self._call_zen_tool("docgen", {
            "code": current_code,
            "style": "comprehensive",
            "filename": task.file_path
        })
        
        if result.get("status") != "error" and "documented_code" in result:
            # Create backup
            self._backup_file(task.file_path)
            
            # Write documented code
            with open(task.file_path, 'w', encoding='utf-8') as f:
                f.write(result["documented_code"])
            
            logger.info(f"Added documentation to {task.file_path}")
            
            if self.config["auto_commit"] and self.repo:
                self._create_commit(task, prefix="[DOCS]")
            
            return True
        
        return False
    
    def _backup_file(self, file_path: str):
        """Create backup of file before modification"""
        backup_dir = Path("backups") / datetime.now().strftime("%Y%m%d")
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        source = Path(file_path)
        timestamp = datetime.now().strftime("%H%M%S")
        backup_path = backup_dir / f"{source.stem}_{timestamp}{source.suffix}"
        
        import shutil
        shutil.copy2(file_path, backup_path)
        logger.info(f"Created backup: {backup_path}")
    
    def _create_commit(self, task: AutomationTask, prefix: str = "[AUTO]"):
        """Create git commit for task"""
        if not self.repo:
            return
            
        try:
            # Stage the file
            self.repo.index.add([task.file_path])
            
            # Create commit message
            commit_message = f"{prefix} {task.description}\n\nTask ID: {task.id}\nPriority: {task.priority.name}"
            
            # Commit
            self.repo.index.commit(commit_message)
            logger.info(f"Created commit for task {task.id}")
            
        except Exception as e:
            logger.error(f"Error creating commit: {e}")
    
    async def run_automation_cycle(self):
        """Run a complete automation cycle"""
        logger.info("Starting automation cycle...")
        
        # Analyze codebase
        tasks = await self.analyze_codebase()
        
        # Add tasks to queue
        self.task_queue.extend(tasks)
        
        # Execute tasks based on priority
        max_concurrent = self.config["max_concurrent_tasks"]
        
        while self.task_queue:
            # Get next batch of tasks
            batch = []
            for _ in range(min(max_concurrent, len(self.task_queue))):
                if self.task_queue:
                    batch.append(self.task_queue.pop(0))
            
            # Execute batch concurrently
            results = await asyncio.gather(
                *[self.execute_task(task) for task in batch],
                return_exceptions=True
            )
            
            # Mark completed tasks
            for task, result in zip(batch, results):
                if isinstance(result, bool) and result:
                    task.completed = True
                    logger.info(f"Task {task.id} completed successfully")
                else:
                    logger.error(f"Task {task.id} failed: {result}")
        
        logger.info("Automation cycle complete")
    
    async def generate_improvement_report(self) -> Dict[str, Any]:
        """Generate report of improvements made"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "tasks_completed": sum(1 for t in self.task_queue if t.completed),
            "tasks_by_type": {},
            "tasks_by_priority": {},
            "files_modified": set(),
            "improvements": []
        }
        
        for task in self.task_queue:
            if task.completed:
                # Count by type
                report["tasks_by_type"][task.type] = report["tasks_by_type"].get(task.type, 0) + 1
                
                # Count by priority
                report["tasks_by_priority"][task.priority.name] = report["tasks_by_priority"].get(task.priority.name, 0) + 1
                
                # Track files
                if task.file_path:
                    report["files_modified"].add(task.file_path)
                
                # Add improvement detail
                report["improvements"].append({
                    "id": task.id,
                    "type": task.type,
                    "file": task.file_path,
                    "description": task.description,
                    "completed_at": task.created_at.isoformat()
                })
        
        # Convert set to list for JSON serialization
        report["files_modified"] = list(report["files_modified"])
        
        # Save report
        report_path = Path("reports") / f"improvement_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        report_path.parent.mkdir(exist_ok=True)
        
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Generated improvement report: {report_path}")
        
        return report
    
    async def close(self):
        """Clean up resources"""
        if self.session:
            await self.session.close()


async def main():
    """Main automation entry point"""
    automation = ZenCodeAutomation()
    
    try:
        # Run initial cycle
        await automation.run_automation_cycle()
        
        # Generate report
        report = await automation.generate_improvement_report()
        
        print(f"\n✅ Automation cycle complete!")
        print(f"📊 Tasks completed: {report['tasks_completed']}")
        print(f"📁 Files modified: {len(report['files_modified'])}")
        
    finally:
        await automation.close()


if __name__ == "__main__":
    asyncio.run(main())