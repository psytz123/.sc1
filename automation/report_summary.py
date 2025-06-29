"""
Summary of Automation Results

This script provides a quick summary of the automation findings.
"""

import json
from utils.logger import get_logger

logger = get_logger(__name__)
from collections import Counter
from pathlib import Path


def summarize_report(report_path: str):
    """Generate a summary of the automation report"""
    with open(report_path, 'r') as f:
        report = json.load(f)
    
    logger.info("📊 Automation Report Summary")
    logger.info("=" * 50)
    
    # Summary stats
    summary = report['summary']
    logger.info(f"\n📈 Overall Statistics:")
    logger.info(f"  • Files analyzed: {summary['total_files_analyzed']}")
    logger.info(f"  • Total issues: {summary['total_issues_found']}")
    logger.info(f"  • Fixes applied: {summary['fixes_applied']}")
    logger.info(f"  • Fixes failed: {summary['fixes_failed']}")
    
    # Priority breakdown
    logger.info(f"\n🎯 Issues by Priority:")
    for priority, count in summary['issues_by_priority'].items():
        logger.info(f"  • {priority}: {count}")
    
    # Issue types
    logger.info(f"\n📋 Issues by Type:")
    issue_types = Counter()
    for issue_type, issues in report['issues_by_type'].items():
        issue_types[issue_type] = len(issues)
    
    for issue_type, count in issue_types.most_common(10):
        logger.info(f"  • {issue_type}: {count}")
    
    # Show some critical issues
    logger.info(f"\n🚨 Sample Critical Issues:")
    critical_count = 0
    for issue_type, issues in report['issues_by_type'].items():
        for issue in issues:
            if issue['priority'] == 'CRITICAL' and critical_count < 5:
                logger.info(f"\n  [{issue['priority']}] {issue['file']}:{issue['line']}")
                logger.info(f"    Type: {issue_type}")
                logger.info(f"    Description: {issue['description']}")
                critical_count += 1
    
    # Files with most issues
    logger.info(f"\n📁 Files with Most Issues:")
    file_counts = Counter()
    for issues in report['issues_by_type'].values():
        for issue in issues:
            file_counts[issue['file']] += 1
    
    for file_path, count in file_counts.most_common(5):
        logger.info(f"  • {file_path}: {count} issues")
    
    logger.info("\n" + "=" * 50)
    logger.info("✅ Summary complete!")


if __name__ == "__main__":
    # Find the latest report
    reports_dir = Path("reports")
    report_files = list(reports_dir.glob("automation_report_*.json"))
    
    if report_files:
        latest_report = max(report_files, key=lambda p: p.stat().st_mtime)
        logger.info(f"📄 Analyzing report: {latest_report.name}\n")
        summarize_report(str(latest_report))
    else:
        logger.info("❌ No reports found in the reports directory")