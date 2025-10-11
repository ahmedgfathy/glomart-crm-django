# Glomart CRM MCP Server - Copilot Instructions

This is a Model Context Protocol (MCP) server workspace for the Glomart Real Estate CRM system.

## Project Overview
- **Purpose**: MCP server providing file system access and MariaDB integration for Glomart CRM
- **Technology**: Python with MCP SDK
- **Database**: MariaDB with full query capabilities using PyMySQL
- **File Access**: Complete project file operations for Django CRM
- **Features**: Django management commands, deployment automation, database tools

## Development Guidelines
- Use Python with proper type hints and error handling
- Implement secure database connections with PyMySQL
- Follow MCP protocol specifications for tool definitions
- Restrict file access to the CRM project directory only
- Provide comprehensive Django management capabilities
- Support database operations with proper SQL injection protection

## Key Components
1. **server.py**: Main MCP server with FastMCP framework
2. **services/filesystem.py**: File system operations with security restrictions
3. **services/database.py**: MariaDB connection and query tools
4. **services/django_manager.py**: Django management command execution
5. **requirements.txt**: Python dependencies (mcp, PyMySQL, python-dotenv)

## File Structure
```
mcp/
├── server.py                    # Main MCP server
├── requirements.txt             # Python dependencies
├── .env.example                # Environment variables template
├── README.md                   # Documentation
└── services/
    ├── __init__.py
    ├── filesystem.py           # File operations
    ├── database.py             # Database operations
    └── django_manager.py       # Django commands
```

## Security Considerations
- File access restricted to CRM_PROJECT_PATH environment variable
- Database queries use parameterized statements
- All operations logged to stderr (not stdout for MCP compatibility)
- Environment variables for sensitive database credentials
- Path validation to prevent directory traversal attacks