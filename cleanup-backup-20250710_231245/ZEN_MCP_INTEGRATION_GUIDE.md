# Zen MCP Server Integration Guide for Beverly Knits

## Overview

Zen MCP Server is a Model Context Protocol server that orchestrates multiple AI models (Claude, Gemini, GPT-4, etc.) for enhanced AI capabilities. It's a separate Node.js application that runs alongside your Python application.

## Current Status

✅ **Prerequisites Installed:**
- Git version 2.50.0.windows.1
- Node.js v22.17.0

❌ **Zen MCP Server:** Not yet installed

## Installation Options

### Option 1: Install Zen MCP Server (Recommended for Advanced AI Features)

1. **Clone and Setup:**
   ```bash
   # Navigate to a suitable directory (outside your project)
   cd C:\
   git clone https://github.com/BeehiveInnovations/zen-mcp-server.git
   cd zen-mcp-server
   npm install
   ```

2. **Configure Environment:**
   ```bash
   copy .env.example .env
   # Edit .env with your API keys
   ```

3. **Required API Keys:**
   - `ANTHROPIC_API_KEY` - For Claude models
   - `GOOGLE_API_KEY` - For Gemini models
   - `OPENAI_API_KEY` - For GPT models (optional)

4. **Start the Server:**
   ```bash
   npm start
   # Server will run on http://localhost:3000
   ```

### Option 2: Proceed Without Zen MCP Server

The Beverly Knits project is designed to work without zen-mcp-server. You can:
- Use local ML libraries (XGBoost, LightGBM, scikit-learn)
- Implement all ML features using installed packages
- Add zen-mcp-server integration later if needed

## Integration Architecture

```
Beverly Knits Python App
    ├── ML Integration Client
    │   ├── Local ML Models (XGBoost, etc.)
    │   └── Zen MCP Server API (optional)
    │       └── HTTP requests to localhost:3000
    │
    ├── Code Management Client
    │   └── Local code analysis
    │
    └── Data Processing Client
        └── Local data processing

Zen MCP Server (separate process)
    ├── Claude API
    ├── Gemini API
    └── Other AI APIs
```

## Configuration Created

A `config/zen_mcp_config.json` file has been created with:
- Server URL configuration
- API endpoints
- Model preferences
- Retry and timeout settings

## Benefits of Zen MCP Server

1. **Multi-Model Consensus:** Get opinions from multiple AI models
2. **Specialized Models:** Use different models for different tasks
3. **Advanced Code Generation:** Leverage Claude's coding capabilities
4. **AI Orchestration:** Coordinate multiple AIs for complex tasks

## Proceeding with Phase 2

You can proceed with Phase 2 in two ways:

### With Zen MCP Server:
1. Install and configure zen-mcp-server
2. Update ML client to use both local and remote AI
3. Implement hybrid approach

### Without Zen MCP Server:
1. Continue with local ML libraries
2. Implement all features using XGBoost, LightGBM, etc.
3. Add zen-mcp-server integration later

## Recommendation

For immediate progress, proceed with Phase 2 using local ML libraries. The architecture is designed to allow adding zen-mcp-server later without major refactoring.

## Next Steps

1. **Decision:** Choose whether to install zen-mcp-server now or proceed without it
2. **Phase 2:** Begin implementing core clients with chosen approach
3. **Testing:** Verify ML operations work with available resources