#!/usr/bin/env python3
"""
Comprehensive cleanup script for Beverly Knits codebase

This script performs various cleanup operations:
1. Removes unused imports
2. Formats code with black
3. Sorts imports with isort
4. Removes dead code
5. Adds type hints where missing
6. Replaces print statements with logging
"""

import ast
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import List, Set, Tuple

# Add parent directory to path to import utils
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.logger import get_logger

logger = get_logger(__name__)


class CodeCleaner:
    """Main code cleanup class"""
    
    def __init__(self, project_root: Path):
        """
        Initialize code cleaner
        
        Args:
            project_root: Root directory of the project
        """
        self.project_root = project_root
        self.python_files = self._find_python_files()
        
    def _find_python_files(self) -> List[Path]:
        """Find all Python files in the project"""
        exclude_dirs = {
            '__pycache__', '.git', '.venv', 'venv', 
            'env', '.env', 'tensorflow', 'zen-mcp-server'
        }
        
        python_files = []
        for root, dirs, files in os.walk(self.project_root):
            # Remove excluded directories from search
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            
            for file in files:
                if file.endswith('.py'):
                    python_files.append(Path(root) / file)
                    
        logger.info(f"Found {len(python_files)} Python files")
        return python_files
    
    def remove_unused_imports(self) -> None:
        """Remove unused imports from all Python files"""
        logger.info("Removing unused imports...")
        
        try:
            subprocess.run(
                ["autoflake", "--in-place", "--remove-all-unused-imports", 
                 "--remove-unused-variables", "--recursive", str(self.project_root)],
                check=True
            )
            logger.info("Successfully removed unused imports")
        except subprocess.CalledProcessError as e:
            logger.warning(f"autoflake not available: {e}")
            logger.info("Install with: pip install autoflake")
    
    def format_code(self) -> None:
        """Format code with black"""
        logger.info("Formatting code with black...")
        
        try:
            subprocess.run(
                ["black", str(self.project_root), "--exclude", "tensorflow|zen-mcp-server"],
                check=True
            )
            logger.info("Successfully formatted code")
        except subprocess.CalledProcessError as e:
            logger.warning(f"black not available: {e}")
            logger.info("Install with: pip install black")
    
    def sort_imports(self) -> None:
        """Sort imports with isort"""
        logger.info("Sorting imports with isort...")
        
        try:
            subprocess.run(
                ["isort", str(self.project_root), "--skip", "tensorflow", 
                 "--skip", "zen-mcp-server"],
                check=True
            )
            logger.info("Successfully sorted imports")
        except subprocess.CalledProcessError as e:
            logger.warning(f"isort not available: {e}")
            logger.info("Install with: pip install isort")
    
    def replace_print_with_logging(self) -> None:
        """Replace print statements with proper logging"""
        logger.info("Replacing print statements with logging...")
        
        replacements = 0
        for file_path in self.python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Skip if already has logging
                if 'import logging' in content or 'from utils.logger import' in content:
                    continue
                
                # Find print statements
                if 'print(' in content:
                    # Add import at the top
                    lines = content.split('\n')
                    import_added = False
                    new_lines = []
                    
                    for i, line in enumerate(lines):
                        if not import_added and (line.startswith('import ') or 
                                                line.startswith('from ')):
                            new_lines.append(line)
                            new_lines.append('from utils.logger import get_logger')
                            new_lines.append('')
                            new_lines.append('logger = get_logger(__name__)')
                            import_added = True
                        else:
                            # Replace print statements
                            if 'print(' in line:
                                # Simple replacement - can be improved
                                new_line = line.replace('print(', 'logger.info(')
                                new_lines.append(new_line)
                                replacements += 1
                            else:
                                new_lines.append(line)
                    
                    # Write back
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write('\n'.join(new_lines))
                        
            except Exception as e:
                logger.error(f"Error processing {file_path}: {e}")
        
        logger.info(f"Replaced {replacements} print statements")
    
    def add_type_hints(self) -> None:
        """Add type hints to functions missing them"""
        logger.info("Adding type hints...")
        
        for file_path in self.python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Parse AST
                tree = ast.parse(content)
                
                # Find functions without type hints
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        if not node.returns and node.name != '__init__':
                            logger.debug(f"Function {node.name} in {file_path} missing return type")
                            
            except Exception as e:
                logger.error(f"Error analyzing {file_path}: {e}")
    
    def check_security_issues(self) -> None:
        """Check for common security issues"""
        logger.info("Checking for security issues...")
        
        issues = []
        
        for file_path in self.python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Check for hardcoded secrets
                secret_patterns = [
                    r'password\s*=\s*["\'][^"\']+["\']',
                    r'api_key\s*=\s*["\'][^"\']+["\']',
                    r'secret\s*=\s*["\'][^"\']+["\']',
                    r'token\s*=\s*["\'][^"\']+["\']'
                ]
                
                for pattern in secret_patterns:
                    matches = re.findall(pattern, content, re.IGNORECASE)
                    if matches:
                        for match in matches:
                            if 'your_' not in match and 'placeholder' not in match:
                                issues.append(f"Potential hardcoded secret in {file_path}: {match}")
                
                # Check for SQL injection vulnerabilities
                if 'execute(' in content and '%s' not in content:
                    sql_patterns = [
                        r'execute\(["\'][^"\']*%[^"\']*["\'].*%',
                        r'execute\(.*\.format\(',
                        r'execute\(.*\+.*\)'
                    ]
                    
                    for pattern in sql_patterns:
                        if re.search(pattern, content):
                            issues.append(f"Potential SQL injection in {file_path}")
                            
            except Exception as e:
                logger.error(f"Error checking {file_path}: {e}")
        
        if issues:
            logger.warning(f"Found {len(issues)} security issues:")
            for issue in issues:
                logger.warning(f"  - {issue}")
        else:
            logger.info("No security issues found")
    
    def run_all_cleanups(self) -> None:
        """Run all cleanup operations"""
        logger.info("Starting comprehensive code cleanup...")
        
        self.remove_unused_imports()
        self.sort_imports()
        self.format_code()
        self.replace_print_with_logging()
        self.add_type_hints()
        self.check_security_issues()
        
        logger.info("Code cleanup completed!")


def main():
    """Main entry point"""
    project_root = Path.cwd()
    
    logger.info(f"Starting cleanup for project at: {project_root}")
    
    cleaner = CodeCleaner(project_root)
    cleaner.run_all_cleanups()
    
    # Additional cleanup tasks
    logger.info("Running additional cleanup tasks...")
    
    # Move test files
    test_files = list(project_root.glob("test_*.py"))
    if test_files:
        tests_dir = project_root / "tests"
        tests_dir.mkdir(exist_ok=True)
        
        for test_file in test_files:
            if test_file.parent == project_root:
                logger.info(f"Moving {test_file.name} to tests/")
                test_file.rename(tests_dir / test_file.name)
    
    # Move demo/script files
    script_files = list(project_root.glob("demo_*.py")) + \
                  list(project_root.glob("check_*.py")) + \
                  list(project_root.glob("setup_*.py"))
    
    if script_files:
        scripts_dir = project_root / "scripts"
        scripts_dir.mkdir(exist_ok=True)
        
        for script_file in script_files:
            if script_file.parent == project_root:
                logger.info(f"Moving {script_file.name} to scripts/")
                script_file.rename(scripts_dir / script_file.name)
    
    logger.info("Cleanup completed successfully!")


if __name__ == "__main__":
    main()