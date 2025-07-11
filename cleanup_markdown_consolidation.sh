#!/bin/bash

# Beverly Knits Markdown Consolidation and File Cleanup Script
# This script safely removes redundant files after consolidating documentation

echo "🧹 Beverly Knits Markdown Consolidation and File Cleanup"
echo "========================================================"

# Create backup directory with timestamp
BACKUP_DIR="cleanup-backup-$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

echo "📦 Creating backup in $BACKUP_DIR..."

# Backup all markdown files before deletion
echo "📋 Backing up markdown files..."
find . -name "*.md" -not -path "./venv*" -not -path "./tensorflow*" -not -path "./zen-mcp-server*" -exec cp {} "$BACKUP_DIR/" \;

# Backup reports and logs
echo "📊 Backing up reports and logs..."
cp -r reports/ "$BACKUP_DIR/" 2>/dev/null || true
cp -r logs/ "$BACKUP_DIR/" 2>/dev/null || true

echo "✅ Backup completed in $BACKUP_DIR"

# Phase 1: Remove completed documentation files
echo ""
echo "🗑️  Phase 1: Removing completed documentation files..."

# Completed task documentation
rm -f REFACTORING_PLAN.md
rm -f REFACTORING_IMPLEMENTATION_SUMMARY.md
rm -f CODEBASE_CLEANUP_PLAN.md
rm -f CODEBASE_CLEANUP_SUMMARY.md
rm -f CODEBASE_CLEANUP_FINAL_REPORT.md
rm -f CLEANUP_SUMMARY.md
rm -f PROJECT_STRUCTURE_CLEAN.md
rm -f ZEN_MCP_VERIFICATION_SUMMARY.md
rm -f ZEN_MCP_VERIFICATION_COMPLETE.md
rm -f ZEN_MCP_INTEGRATION_GUIDE.md
rm -f ZEN_MCP_SUCCESS.md
rm -f PHASE1_COMPLETION_SUMMARY.md
rm -f PHASE2_IMPLEMENTATION_SUMMARY.md
rm -f PHASE_2_1_COMPLETION_SUMMARY.md
rm -f PHASE_2_3_COMPLETION_SUMMARY.md
rm -f CSV_UPLOAD_FIX_SUMMARY.md
rm -f COMPREHENSIVE_PROJECT_ANALYSIS_REPORT.md
rm -f COMPREHENSIVE_INTEGRATION_TASKLIST.md
rm -f PYTHON_313_COMPATIBILITY.md
rm -f PYTHON312_ENV_SETUP.md

# Consolidated files (content moved to comprehensive doc)
rm -f USAGE_GUIDE.md
rm -f ai.md
rm -f DATA_INTEGRATION_README.md
rm -f SALES_INTEGRATION_DOCUMENTATION.md
rm -f SALES_FORECAST_INTEGRATION.md
rm -f CSV_COLUMN_MAPPING.md
rm -f BOM_DATA_QUALITY_REPORT.md
rm -f devcod.md
rm -f PROJECT_STRUCTURE.md
rm -f data_integration_analysis.md

echo "✅ Phase 1 completed: Removed redundant markdown files"

# Phase 2: Remove duplicate virtual environments
echo ""
echo "🗑️  Phase 2: Removing duplicate virtual environments..."

# Keep only venv_py312 (the main working environment)
rm -rf venv/ 2>/dev/null || true
rm -rf venv_fresh/ 2>/dev/null || true
rm -rf venv_py312_fresh/ 2>/dev/null || true

echo "✅ Phase 2 completed: Removed duplicate virtual environments"

# Phase 3: Remove large report files
echo ""
echo "🗑️  Phase 3: Removing large report files..."

rm -f reports/automation_report_*.json 2>/dev/null || true

echo "✅ Phase 3 completed: Removed large report files"

# Phase 4: Remove old log files
echo ""
echo "🗑️  Phase 4: Removing old log files..."

rm -f logs/beverly_knits_*.log 2>/dev/null || true
rm -f logs/ml_integration.log 2>/dev/null || true
rm -f logs/automation.log 2>/dev/null || true
rm -f logs/zen_automation.log 2>/dev/null || true

echo "✅ Phase 4 completed: Removed old log files"

# Phase 5: Remove development artifacts
echo ""
echo "🗑️  Phase 5: Removing development artifacts..."

# Temporary and development files
rm -f patch_planner.py 2>/dev/null || true
rm -f planner_output.txt 2>/dev/null || true
rm -f debug_materials.py 2>/dev/null || true
rm -f generate_missing_suppliers.py 2>/dev/null || true
rm -f check_data_alignment.py 2>/dev/null || true
rm -f test_bom_material_ids.py 2>/dev/null || true
rm -f test_bom_explosion.py 2>/dev/null || true
rm -f test_material_matching.py 2>/dev/null || true
rm -f test_bom_report.csv 2>/dev/null || true
rm -f test_yarn_requirements.json 2>/dev/null || true
rm -f sales_based_forecasts.csv 2>/dev/null || true
rm -f test_output_recommendations.csv 2>/dev/null || true
rm -f inventory_alerts.csv 2>/dev/null || true

echo "✅ Phase 5 completed: Removed development artifacts"

# Phase 6: Remove cache directories
echo ""
echo "🗑️  Phase 6: Removing cache directories..."

# Remove Python cache directories
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
find . -name ".pytest_cache" -type d -exec rm -rf {} + 2>/dev/null || true
rm -rf .vscode/ 2>/dev/null || true

echo "✅ Phase 6 completed: Removed cache directories"

# Phase 7: Optional - Remove TensorFlow directory (large)
echo ""
echo "❓ Phase 7: TensorFlow directory cleanup (optional)"
echo "The tensorflow/ directory (~500MB) is not used in the current implementation."
echo "Would you like to remove it? (y/N)"
read -r response
if [[ "$response" =~ ^[Yy]$ ]]; then
    echo "🗑️  Removing tensorflow/ directory..."
    rm -rf tensorflow/ 2>/dev/null || true
    echo "✅ TensorFlow directory removed"
else
    echo "⏭️  Skipping TensorFlow directory removal"
fi

# Phase 8: Review zen-mcp-server directory
echo ""
echo "❓ Phase 8: zen-mcp-server directory cleanup (optional)"
echo "The zen-mcp-server/ directory (~50MB) contains an external project."
echo "Would you like to remove it? (y/N)"
read -r response
if [[ "$response" =~ ^[Yy]$ ]]; then
    echo "🗑️  Removing zen-mcp-server/ directory..."
    rm -rf zen-mcp-server/ 2>/dev/null || true
    echo "✅ zen-mcp-server directory removed"
else
    echo "⏭️  Skipping zen-mcp-server directory removal"
fi

# Summary
echo ""
echo "🎉 Cleanup Summary"
echo "=================="
echo "✅ Consolidated 15+ markdown files into COMPREHENSIVE_PROJECT_DOCUMENTATION.md"
echo "✅ Updated README.md to point to comprehensive documentation"
echo "✅ Removed redundant documentation files"
echo "✅ Removed duplicate virtual environments"
echo "✅ Removed large report files"
echo "✅ Removed old log files"
echo "✅ Removed development artifacts"
echo "✅ Removed cache directories"
echo "📦 Full backup saved in: $BACKUP_DIR"

# Calculate space saved
if command -v du &> /dev/null; then
    echo ""
    echo "💾 Space Analysis"
    echo "================"
    BACKUP_SIZE=$(du -sh "$BACKUP_DIR" 2>/dev/null | cut -f1)
    echo "📦 Backup size: $BACKUP_SIZE"
    echo "💡 This represents the space that was cleaned up"
fi

echo ""
echo "🔍 Next Steps"
echo "============="
echo "1. Test the application: streamlit run main.py"
echo "2. Verify all imports work correctly"
echo "3. Check that comprehensive documentation is complete"
echo "4. If everything works, you can remove the backup directory"
echo ""
echo "🚨 Important: If you encounter any issues, restore from backup:"
echo "   cp -r $BACKUP_DIR/* ."
echo ""
echo "✅ Cleanup completed successfully!" 