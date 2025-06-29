"""
Simplified Code Automation System

This version works directly with the codebase without requiring zen-mcp-server HTTP API.
It uses local code analysis tools and AI-powered improvements.
"""

import os
import json
import asyncio
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
import ast
import re
from dataclasses import dataclass, field
from enum import Enum
import logging


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/automation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class Priority(Enum):
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4


@dataclass
class CodeIssue:
    """Represents a code issue found during analysis"""
    file_path: str
    line_number: int
    issue_type: str
    description: str
    priority: Priority
    suggested_fix: Optional[str] = None


class SimpleCodeAnalyzer:
    """Analyzes code for common issues and improvements"""
    
    def __init__(self):
        self.issues = []
    
    def analyze_file(self, file_path: Path) -> List[CodeIssue]:
        """Analyze a single file for issues"""
        self.issues = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.splitlines()
            
            # Check file extension
            if file_path.suffix == '.py':
                self._analyze_python(file_path, content, lines)
            elif file_path.suffix in ['.js', '.ts', '.jsx', '.tsx']:
                self._analyze_javascript(file_path, content, lines)
            
            # Common checks for all files
            self._check_security_issues(file_path, content, lines)
            self._check_documentation(file_path, content, lines)
            self._check_code_quality(file_path, content, lines)
            
        except Exception as e:
            logger.error(f"Error analyzing {file_path}: {e}")
        
        return self.issues
    
    def _analyze_python(self, file_path: Path, content: str, lines: List[str]):
        """Python-specific analysis"""
        try:
            tree = ast.parse(content)
            
            # Check for missing docstrings
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                    if not ast.get_docstring(node):
                        self.issues.append(CodeIssue(
                            file_path=str(file_path),
                            line_number=node.lineno,
                            issue_type="documentation",
                            description=f"Missing docstring for {node.name}",
                            priority=Priority.LOW,
                            suggested_fix=f'"""Add description for {node.name}"""'
                        ))
            
            # Check for bare except clauses
            for node in ast.walk(tree):
                if isinstance(node, ast.ExceptHandler) and node.type is None:
                    self.issues.append(CodeIssue(
                        file_path=str(file_path),
                        line_number=node.lineno,
                        issue_type="error_handling",
                        description="Bare except clause - should specify exception type",
                        priority=Priority.HIGH,
                        suggested_fix="except Exception as e:"
                    ))
            
        except SyntaxError as e:
            self.issues.append(CodeIssue(
                file_path=str(file_path),
                line_number=e.lineno or 1,
                issue_type="syntax_error",
                description=f"Syntax error: {e.msg}",
                priority=Priority.CRITICAL
            ))
    
    def _analyze_javascript(self, file_path: Path, content: str, lines: List[str]):
        """JavaScript/TypeScript analysis"""
        # Check for console.log statements
        for i, line in enumerate(lines, 1):
            if 'console.log' in line and not line.strip().startswith('//'):
                self.issues.append(CodeIssue(
                    file_path=str(file_path),
                    line_number=i,
                    issue_type="debug_code",
                    description="Console.log statement found",
                    priority=Priority.MEDIUM,
                    suggested_fix="Remove or replace with proper logging"
                ))
    
    def _check_security_issues(self, file_path: Path, content: str, lines: List[str]):
        """Check for common security issues"""
        # Check for eval usage
        if 'eval(' in content:
            for i, line in enumerate(lines, 1):
                if 'eval(' in line and not line.strip().startswith('#') and not line.strip().startswith('//'):
                    self.issues.append(CodeIssue(
                        file_path=str(file_path),
                        line_number=i,
                        issue_type="security",
                        description="Use of eval() is a security risk",
                        priority=Priority.CRITICAL,
                        suggested_fix="Replace eval() with safer alternatives"
                    ))
        
        # Check for hardcoded credentials
        credential_patterns = [
            r'password\s*=\s*["\'][^"\']+["\']',
            r'api_key\s*=\s*["\'][^"\']+["\']',
            r'secret\s*=\s*["\'][^"\']+["\']'
        ]
        
        for pattern in credential_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                line_num = content[:match.start()].count('\n') + 1
                self.issues.append(CodeIssue(
                    file_path=str(file_path),
                    line_number=line_num,
                    issue_type="security",
                    description="Possible hardcoded credential",
                    priority=Priority.CRITICAL,
                    suggested_fix="Use environment variables or secure configuration"
                ))
    
    def _check_documentation(self, file_path: Path, content: str, lines: List[str]):
        """Check documentation quality"""
        # Check for TODO comments
        for i, line in enumerate(lines, 1):
            if 'TODO' in line:
                self.issues.append(CodeIssue(
                    file_path=str(file_path),
                    line_number=i,
                    issue_type="incomplete",
                    description=f"TODO found: {line.strip()}",
                    priority=Priority.MEDIUM
                ))
    
    def _check_code_quality(self, file_path: Path, content: str, lines: List[str]):
        """Check general code quality issues"""
        # Check for very long lines
        for i, line in enumerate(lines, 1):
            if len(line) > 120:
                self.issues.append(CodeIssue(
                    file_path=str(file_path),
                    line_number=i,
                    issue_type="style",
                    description=f"Line too long ({len(line)} characters)",
                    priority=Priority.LOW,
                    suggested_fix="Break line into multiple lines"
                ))
        
        # Check for trailing whitespace
        for i, line in enumerate(lines, 1):
            if line.endswith(' ') or line.endswith('\t'):
                self.issues.append(CodeIssue(
                    file_path=str(file_path),
                    line_number=i,
                    issue_type="style",
                    description="Trailing whitespace",
                    priority=Priority.LOW,
                    suggested_fix="Remove trailing whitespace"
                ))


class SimpleCodeImprover:
    """Applies simple code improvements"""
    
    def __init__(self):
        self.backup_dir = Path("backups")
        self.backup_dir.mkdir(exist_ok=True)
    
    def fix_issue(self, issue: CodeIssue) -> bool:
        """Attempt to fix a code issue"""
        try:
            file_path = Path(issue.file_path)
            
            # Create backup
            backup_path = self._create_backup(file_path)
            logger.info(f"Created backup: {backup_path}")
            
            # Read file
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Apply fix based on issue type
            fixed = False
            
            if issue.issue_type == "style" and "trailing whitespace" in issue.description.lower():
                # Fix trailing whitespace
                lines[issue.line_number - 1] = lines[issue.line_number - 1].rstrip() + '\n'
                fixed = True
            
            elif issue.issue_type == "debug_code" and "console.log" in issue.description.lower():
                # Comment out console.log
                line = lines[issue.line_number - 1]
                if 'console.log' in line:
                    lines[issue.line_number - 1] = line.replace('console.log', '// console.log')
                    fixed = True
            
            # Write fixed content
            if fixed:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.writelines(lines)
                logger.info(f"Fixed {issue.issue_type} in {file_path}:{issue.line_number}")
                return True
            
        except Exception as e:
            logger.error(f"Error fixing issue: {e}")
        
        return False
    
    def _create_backup(self, file_path: Path) -> Path:
        """Create a backup of the file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{file_path.stem}_{timestamp}{file_path.suffix}"
        backup_path = self.backup_dir / backup_name
        
        with open(file_path, 'rb') as src, open(backup_path, 'wb') as dst:
            dst.write(src.read())
        
        return backup_path


class SimpleAutomation:
    """Main automation system"""
    
    def __init__(self, config_path: str = "config/automation_config.json"):
        self.config = self._load_config(config_path)
        self.analyzer = SimpleCodeAnalyzer()
        self.improver = SimpleCodeImprover()
        self.report_dir = Path("reports")
        self.report_dir.mkdir(exist_ok=True)
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration"""
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning(f"Config file not found: {config_path}, using defaults")
            return {
                "file_patterns": ["*.py", "*.js", "*.ts"],
                "excluded_paths": ["__pycache__", ".git", "node_modules", "venv"],
                "max_fixes_per_run": 10
            }
    
    async def run_analysis(self) -> List[CodeIssue]:
        """Run analysis on all configured files"""
        all_issues = []
        
        # Find files to analyze
        files_to_analyze = self._find_files()
        logger.info(f"Found {len(files_to_analyze)} files to analyze")
        
        # Analyze each file
        for file_path in files_to_analyze:
            issues = self.analyzer.analyze_file(file_path)
            all_issues.extend(issues)
        
        # Sort by priority
        all_issues.sort(key=lambda x: (x.priority.value, x.file_path))
        
        logger.info(f"Found {len(all_issues)} total issues")
        return all_issues
    
    def _find_files(self) -> List[Path]:
        """Find all files matching configured patterns"""
        files = []
        
        for pattern in self.config.get("file_patterns", ["*.py"]):
            for file_path in Path(".").rglob(pattern):
                # Skip excluded paths
                skip = False
                for excluded in self.config.get("excluded_paths", []):
                    if excluded in str(file_path):
                        skip = True
                        break
                
                if not skip and file_path.is_file():
                    files.append(file_path)
        
        return files
    
    async def apply_fixes(self, issues: List[CodeIssue], max_fixes: Optional[int] = None) -> Dict[str, Any]:
        """Apply fixes to issues"""
        if max_fixes is None:
            max_fixes = self.config.get("max_fixes_per_run", 10)
        
        results = {
            "total_issues": len(issues),
            "attempted_fixes": 0,
            "successful_fixes": 0,
            "failed_fixes": 0,
            "fixes": []
        }
        
        # Apply fixes to high-priority issues first
        for issue in issues[:max_fixes]:
            results["attempted_fixes"] += 1
            
            if self.improver.fix_issue(issue):
                results["successful_fixes"] += 1
                results["fixes"].append({
                    "file": issue.file_path,
                    "line": issue.line_number,
                    "type": issue.issue_type,
                    "description": issue.description,
                    "status": "fixed"
                })
            else:
                results["failed_fixes"] += 1
                results["fixes"].append({
                    "file": issue.file_path,
                    "line": issue.line_number,
                    "type": issue.issue_type,
                    "description": issue.description,
                    "status": "failed"
                })
        
        return results
    
    def generate_report(self, issues: List[CodeIssue], fix_results: Dict[str, Any]) -> str:
        """Generate a report of the analysis and fixes"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = self.report_dir / f"automation_report_{timestamp}.json"
        
        # Group issues by type
        issues_by_type = {}
        for issue in issues:
            if issue.issue_type not in issues_by_type:
                issues_by_type[issue.issue_type] = []
            issues_by_type[issue.issue_type].append({
                "file": issue.file_path,
                "line": issue.line_number,
                "description": issue.description,
                "priority": issue.priority.name
            })
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_files_analyzed": len(set(i.file_path for i in issues)),
                "total_issues_found": len(issues),
                "issues_by_priority": {
                    "CRITICAL": len([i for i in issues if i.priority == Priority.CRITICAL]),
                    "HIGH": len([i for i in issues if i.priority == Priority.HIGH]),
                    "MEDIUM": len([i for i in issues if i.priority == Priority.MEDIUM]),
                    "LOW": len([i for i in issues if i.priority == Priority.LOW])
                },
                "fixes_applied": fix_results["successful_fixes"],
                "fixes_failed": fix_results["failed_fixes"]
            },
            "issues_by_type": issues_by_type,
            "fixes_applied": fix_results["fixes"]
        }
        
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Report saved to: {report_path}")
        return str(report_path)


async def main():
    """Run the simplified automation"""
    print("🚀 Simple Code Automation System")
    print("=" * 50)
    
    automation = SimpleAutomation()
    
    # Run analysis
    print("\n📊 Analyzing codebase...")
    issues = await automation.run_analysis()
    
    if not issues:
        print("✅ No issues found!")
        return
    
    # Show summary
    print(f"\n📋 Found {len(issues)} issues:")
    priority_counts = {}
    for issue in issues:
        priority_counts[issue.priority.name] = priority_counts.get(issue.priority.name, 0) + 1
    
    for priority, count in sorted(priority_counts.items()):
        print(f"  • {priority}: {count}")
    
    # Show top issues
    print("\n🔍 Top issues:")
    for issue in issues[:5]:
        print(f"\n[{issue.priority.name}] {issue.file_path}:{issue.line_number}")
        print(f"  Type: {issue.issue_type}")
        print(f"  Description: {issue.description}")
        if issue.suggested_fix:
            print(f"  Suggested fix: {issue.suggested_fix}")
    
    # Apply fixes
    print("\n🔧 Applying automatic fixes...")
    fix_results = await automation.apply_fixes(issues, max_fixes=5)
    
    print(f"\n✅ Fixed {fix_results['successful_fixes']} issues")
    if fix_results['failed_fixes'] > 0:
        print(f"❌ Failed to fix {fix_results['failed_fixes']} issues")
    
    # Generate report
    report_path = automation.generate_report(issues, fix_results)
    print(f"\n📄 Detailed report saved to: {report_path}")
    
    print("\n" + "=" * 50)
    print("✅ Automation complete!")
    print("\nThis simplified system can:")
    print("  • Analyze Python and JavaScript/TypeScript files")
    print("  • Find security issues, style problems, and TODOs")
    print("  • Automatically fix simple issues")
    print("  • Generate detailed reports")
    print("\nFor more advanced AI-powered improvements,")
    print("use the zen-mcp-server with Claude Desktop!")


if __name__ == "__main__":
    asyncio.run(main())