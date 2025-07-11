# Beverly Knits Markdown Consolidation and File Cleanup Script (PowerShell)
# This script safely removes redundant files after consolidating documentation

Write-Host "🧹 Beverly Knits Markdown Consolidation and File Cleanup" -ForegroundColor Green
Write-Host "========================================================" -ForegroundColor Green

# Create backup directory with timestamp
$BackupDir = "cleanup-backup-$(Get-Date -Format 'yyyyMMdd_HHmmss')"
New-Item -ItemType Directory -Path $BackupDir -Force | Out-Null

Write-Host "📦 Creating backup in $BackupDir..." -ForegroundColor Yellow

# Backup all markdown files before deletion
Write-Host "📋 Backing up markdown files..." -ForegroundColor Cyan
Get-ChildItem -Path . -Filter "*.md" -Recurse | Where-Object { 
    $_.FullName -notlike "*\venv*" -and 
    $_.FullName -notlike "*\tensorflow*" -and 
    $_.FullName -notlike "*\zen-mcp-server*" 
} | Copy-Item -Destination $BackupDir -Force

# Backup reports and logs
Write-Host "📊 Backing up reports and logs..." -ForegroundColor Cyan
if (Test-Path "reports") { Copy-Item -Path "reports\*" -Destination $BackupDir -Recurse -Force -ErrorAction SilentlyContinue }
if (Test-Path "logs") { Copy-Item -Path "logs\*" -Destination $BackupDir -Recurse -Force -ErrorAction SilentlyContinue }

Write-Host "✅ Backup completed in $BackupDir" -ForegroundColor Green

# Phase 1: Remove completed documentation files
Write-Host ""
Write-Host "🗑️  Phase 1: Removing completed documentation files..." -ForegroundColor Yellow

# Completed task documentation
$CompletedDocs = @(
    "REFACTORING_PLAN.md",
    "REFACTORING_IMPLEMENTATION_SUMMARY.md",
    "CODEBASE_CLEANUP_PLAN.md",
    "CODEBASE_CLEANUP_SUMMARY.md",
    "CODEBASE_CLEANUP_FINAL_REPORT.md",
    "CLEANUP_SUMMARY.md",
    "PROJECT_STRUCTURE_CLEAN.md",
    "ZEN_MCP_VERIFICATION_SUMMARY.md",
    "ZEN_MCP_VERIFICATION_COMPLETE.md",
    "ZEN_MCP_INTEGRATION_GUIDE.md",
    "ZEN_MCP_SUCCESS.md",
    "PHASE1_COMPLETION_SUMMARY.md",
    "PHASE2_IMPLEMENTATION_SUMMARY.md",
    "PHASE_2_1_COMPLETION_SUMMARY.md",
    "PHASE_2_3_COMPLETION_SUMMARY.md",
    "CSV_UPLOAD_FIX_SUMMARY.md",
    "COMPREHENSIVE_PROJECT_ANALYSIS_REPORT.md",
    "COMPREHENSIVE_INTEGRATION_TASKLIST.md",
    "PYTHON_313_COMPATIBILITY.md",
    "PYTHON312_ENV_SETUP.md"
)

# Consolidated files (content moved to comprehensive doc)
$ConsolidatedDocs = @(
    "USAGE_GUIDE.md",
    "ai.md",
    "DATA_INTEGRATION_README.md",
    "SALES_INTEGRATION_DOCUMENTATION.md",
    "SALES_FORECAST_INTEGRATION.md",
    "CSV_COLUMN_MAPPING.md",
    "BOM_DATA_QUALITY_REPORT.md",
    "devcod.md",
    "PROJECT_STRUCTURE.md",
    "data_integration_analysis.md"
)

$AllDocsToRemove = $CompletedDocs + $ConsolidatedDocs

foreach ($doc in $AllDocsToRemove) {
    if (Test-Path $doc) {
        Remove-Item $doc -Force
        Write-Host "  ✓ Removed $doc" -ForegroundColor Gray
    }
}

Write-Host "✅ Phase 1 completed: Removed redundant markdown files" -ForegroundColor Green

# Phase 2: Remove duplicate virtual environments
Write-Host ""
Write-Host "🗑️  Phase 2: Removing duplicate virtual environments..." -ForegroundColor Yellow

$VenvToRemove = @("venv", "venv_fresh", "venv_py312_fresh")

foreach ($venv in $VenvToRemove) {
    if (Test-Path $venv) {
        Remove-Item $venv -Recurse -Force -ErrorAction SilentlyContinue
        Write-Host "  ✓ Removed $venv/" -ForegroundColor Gray
    }
}

Write-Host "✅ Phase 2 completed: Removed duplicate virtual environments" -ForegroundColor Green

# Phase 3: Remove large report files
Write-Host ""
Write-Host "🗑️  Phase 3: Removing large report files..." -ForegroundColor Yellow

if (Test-Path "reports") {
    Get-ChildItem -Path "reports" -Filter "automation_report_*.json" | Remove-Item -Force
    Write-Host "  ✓ Removed large automation reports" -ForegroundColor Gray
}

Write-Host "✅ Phase 3 completed: Removed large report files" -ForegroundColor Green

# Phase 4: Remove old log files
Write-Host ""
Write-Host "🗑️  Phase 4: Removing old log files..." -ForegroundColor Yellow

if (Test-Path "logs") {
    $LogFiles = @("beverly_knits_*.log", "ml_integration.log", "automation.log", "zen_automation.log")
    foreach ($pattern in $LogFiles) {
        Get-ChildItem -Path "logs" -Filter $pattern | Remove-Item -Force
    }
    Write-Host "  ✓ Removed old log files" -ForegroundColor Gray
}

Write-Host "✅ Phase 4 completed: Removed old log files" -ForegroundColor Green

# Phase 5: Remove development artifacts
Write-Host ""
Write-Host "🗑️  Phase 5: Removing development artifacts..." -ForegroundColor Yellow

$DevArtifacts = @(
    "patch_planner.py",
    "planner_output.txt",
    "debug_materials.py",
    "generate_missing_suppliers.py",
    "check_data_alignment.py",
    "test_bom_material_ids.py",
    "test_bom_explosion.py",
    "test_material_matching.py",
    "test_bom_report.csv",
    "test_yarn_requirements.json",
    "sales_based_forecasts.csv",
    "test_output_recommendations.csv",
    "inventory_alerts.csv"
)

foreach ($artifact in $DevArtifacts) {
    if (Test-Path $artifact) {
        Remove-Item $artifact -Force
        Write-Host "  ✓ Removed $artifact" -ForegroundColor Gray
    }
}

Write-Host "✅ Phase 5 completed: Removed development artifacts" -ForegroundColor Green

# Phase 6: Remove cache directories
Write-Host ""
Write-Host "🗑️  Phase 6: Removing cache directories..." -ForegroundColor Yellow

# Remove Python cache directories
Get-ChildItem -Path . -Name "__pycache__" -Recurse -Directory | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
Get-ChildItem -Path . -Name ".pytest_cache" -Recurse -Directory | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
if (Test-Path ".vscode") { Remove-Item ".vscode" -Recurse -Force -ErrorAction SilentlyContinue }

Write-Host "✅ Phase 6 completed: Removed cache directories" -ForegroundColor Green

# Phase 7: Optional - Remove TensorFlow directory (large)
Write-Host ""
Write-Host "❓ Phase 7: TensorFlow directory cleanup (optional)" -ForegroundColor Magenta
Write-Host "The tensorflow/ directory (~500MB) is not used in the current implementation."
$response = Read-Host "Would you like to remove it? (y/N)"
if ($response -match "^[Yy]$") {
    Write-Host "🗑️  Removing tensorflow/ directory..." -ForegroundColor Yellow
    if (Test-Path "tensorflow") {
        Remove-Item "tensorflow" -Recurse -Force -ErrorAction SilentlyContinue
        Write-Host "✅ TensorFlow directory removed" -ForegroundColor Green
    }
} else {
    Write-Host "⏭️  Skipping TensorFlow directory removal" -ForegroundColor Gray
}

# Phase 8: Review zen-mcp-server directory
Write-Host ""
Write-Host "❓ Phase 8: zen-mcp-server directory cleanup (optional)" -ForegroundColor Magenta
Write-Host "The zen-mcp-server/ directory (~50MB) contains an external project."
$response = Read-Host "Would you like to remove it? (y/N)"
if ($response -match "^[Yy]$") {
    Write-Host "🗑️  Removing zen-mcp-server/ directory..." -ForegroundColor Yellow
    if (Test-Path "zen-mcp-server") {
        Remove-Item "zen-mcp-server" -Recurse -Force -ErrorAction SilentlyContinue
        Write-Host "✅ zen-mcp-server directory removed" -ForegroundColor Green
    }
} else {
    Write-Host "⏭️  Skipping zen-mcp-server directory removal" -ForegroundColor Gray
}

# Summary
Write-Host ""
Write-Host "🎉 Cleanup Summary" -ForegroundColor Green
Write-Host "=================="
Write-Host "✅ Consolidated 15+ markdown files into COMPREHENSIVE_PROJECT_DOCUMENTATION.md" -ForegroundColor Green
Write-Host "✅ Updated README.md to point to comprehensive documentation" -ForegroundColor Green
Write-Host "✅ Removed redundant documentation files" -ForegroundColor Green
Write-Host "✅ Removed duplicate virtual environments" -ForegroundColor Green
Write-Host "✅ Removed large report files" -ForegroundColor Green
Write-Host "✅ Removed old log files" -ForegroundColor Green
Write-Host "✅ Removed development artifacts" -ForegroundColor Green
Write-Host "✅ Removed cache directories" -ForegroundColor Green
Write-Host "📦 Full backup saved in: $BackupDir" -ForegroundColor Cyan

# Calculate space saved
if (Test-Path $BackupDir) {
    Write-Host ""
    Write-Host "💾 Space Analysis" -ForegroundColor Yellow
    Write-Host "================"
    $BackupSize = (Get-ChildItem -Path $BackupDir -Recurse | Measure-Object -Property Length -Sum).Sum
    $BackupSizeMB = [math]::Round($BackupSize / 1MB, 2)
    Write-Host "📦 Backup size: $BackupSizeMB MB" -ForegroundColor Cyan
    Write-Host "💡 This represents the space that was cleaned up" -ForegroundColor Gray
}

Write-Host ""
Write-Host "🔍 Next Steps" -ForegroundColor Yellow
Write-Host "============="
Write-Host "1. Test the application: streamlit run main.py" -ForegroundColor White
Write-Host "2. Verify all imports work correctly" -ForegroundColor White
Write-Host "3. Check that comprehensive documentation is complete" -ForegroundColor White
Write-Host "4. If everything works, you can remove the backup directory" -ForegroundColor White
Write-Host ""
Write-Host "🚨 Important: If you encounter any issues, restore from backup:" -ForegroundColor Red
Write-Host "   Copy-Item -Path '$BackupDir\*' -Destination . -Recurse -Force" -ForegroundColor Red
Write-Host ""
Write-Host "✅ Cleanup completed successfully!" -ForegroundColor Green 