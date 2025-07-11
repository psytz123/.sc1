# Beverly Knits Codebase Cleanup Plan

## Overview
This document outlines the systematic cleanup of the Beverly Knits Raw Material Planner codebase.

## Identified Issues

### 1. Code Quality Issues
- **Inconsistent import ordering**: Imports are not following PEP 8 standards
- **Mixed import styles**: Some files use absolute imports, others use relative
- **Duplicate files**: `helpers.py` and `helpers_refactored.py` exist in utils
- **Inconsistent naming**: Mix of camelCase and snake_case
- **Missing type hints**: Many functions lack proper type annotations
- **Inconsistent formatting**: Indentation and spacing issues

### 2. Dead Code
- Multiple main files: `main.py`, `main_refactored.py`, `main_planning_system.py`
- Unused test files in root directory
- Duplicate integration files
- Unused scripts and batch files

### 3. Documentation Issues
- Missing docstrings in some functions
- Inconsistent docstring formats
- Outdated documentation files

### 4. Project Structure Issues
- Test files in root directory instead of tests folder
- Multiple configuration approaches
- Scattered utility scripts

## Cleanup Steps

### Phase 1: Remove Dead Code
1. Identify and remove duplicate files
2. Remove unused imports
3. Delete obsolete test files from root
4. Clean up unused scripts

### Phase 2: Standardize Code Style
1. Fix import ordering (standard library, third-party, local)
2. Standardize naming conventions (snake_case for functions/variables)
3. Add missing type hints
4. Fix indentation and formatting

### Phase 3: Consolidate and Organize
1. Merge duplicate helper files
2. Move test files to proper directory
3. Consolidate main entry points
4. Organize configuration files

### Phase 4: Documentation
1. Add missing docstrings
2. Standardize docstring format (Google style)
3. Update README and documentation
4. Add inline comments for complex logic

### Phase 5: Final Validation
1. Run linting tools
2. Check for remaining issues
3. Verify all imports work
4. Test functionality