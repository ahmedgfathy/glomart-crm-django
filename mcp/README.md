# Glomart CRM MCP Server

A Model Context Protocol (MCP) server providing comprehensive file system access and MariaDB database integration for the Glomart Real Estate CRM system.

## 🎯 Overview

This MCP server enables AI assistants to interact directly with your Django CRM system by providing:
- **File System Operations**: Read/write access to CRM project files
- **Database Integration**: Full MariaDB query capabilities with 3,228+ properties
- **Django Management**: Execute Django commands and migrations
- **Secure Access**: Restricted to CRM project directory with proper authentication

## 📊 Current Database Status
- **9 Leads** in the system
- **3,228 Properties** available
- **9 Projects** managed
- **65 Users** registered

## 🚀 Quick Start

### Prerequisites
- Python 3.13+ 
- MariaDB/MySQL server running locally
- Django CRM project at `/Users/ahmedgomaa/Downloads/crm`

### Installation

1. **Clone and Setup**
```bash
cd /Users/ahmedgomaa/Downloads/crm/mcp
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

2. **Configure Environment**
```bash
cp .env.example .env
# Edit .env with your MariaDB credentials
```

3. **Test Installation**
```bash
python test_complete.py
```

## 🛠️ Available MCP Tools

### File System Operations
- `read_file(path)` - Read any file in the CRM project
- `write_file(path, content)` - Write content to files
- `list_directory(path)` - List directory contents
- `create_directory(path)` - Create new directories

### Database Operations  
- `db_query(query, params)` - Execute SQL queries
- `get_tables()` - List all database tables
- `get_table_schema(table)` - Show table structure
- `backup_database(filename)` - Create database backups

### Django Management
- `django_migrate(app)` - Run Django migrations
- `django_collectstatic()` - Collect static files
- `django_shell(command)` - Execute Django shell commands
- `django_makemigrations(app)` - Create new migrations

## 🔧 Configuration

### Environment Variables (.env)
```env
# CRM Project Path (security restriction)
CRM_PROJECT_PATH=/Users/ahmedgomaa/Downloads/crm

# MariaDB Database Configuration
DB_HOST=localhost
DB_PORT=3306
DB_NAME=django_db_glomart_rs
DB_USER=root
DB_PASSWORD=zerocall

# Django Settings
DJANGO_SETTINGS_MODULE=real_estate_crm.settings

# Debug Mode
DEBUG=false
```

### Claude Desktop Configuration

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "glomart-crm": {
      "command": "python",
      "args": ["/Users/ahmedgomaa/Downloads/crm/mcp/server.py"],
      "env": {
        "DB_HOST": "localhost",
        "DB_USER": "root",
        "DB_PASSWORD": "zerocall",
        "DB_NAME": "django_db_glomart_rs",
        "CRM_PROJECT_PATH": "/Users/ahmedgomaa/Downloads/crm"
      }
    }
  }
}
```

## 📁 Project Structure

```
mcp/
├── server.py                 # Main MCP server with FastMCP
├── requirements.txt          # Python dependencies 
├── .env                     # Environment configuration
├── .env.example             # Environment template
├── README.md                # This documentation
├── test_complete.py         # Comprehensive functionality test
├── test_tools.py            # Individual service tests
├── explore_schema.py        # Database schema explorer
└── services/
    ├── __init__.py
    ├── filesystem.py        # File operations with security
    ├── database.py          # MariaDB integration
    └── django_manager.py    # Django command execution
```

## 🔐 Security Features

- **Path Restriction**: File access limited to CRM_PROJECT_PATH
- **SQL Injection Prevention**: Parameterized queries only
- **Error Handling**: Comprehensive logging to stderr
- **Directory Validation**: Path traversal attack prevention

## 🎯 Use Cases

### Real Estate Data Analysis
```python
# Query property trends
properties = db_query("""
    SELECT region_id, AVG(asking_price) as avg_price, COUNT(*) as count
    FROM properties_property 
    WHERE asking_price IS NOT NULL
    GROUP BY region_id
    ORDER BY avg_price DESC
""")
```

### Lead Management
```python
# Find high-score leads
leads = db_query("""
    SELECT first_name, last_name, email, score, budget_max
    FROM leads_lead 
    WHERE score > 80 AND is_qualified = 1
    ORDER BY score DESC
""")
```

### Django Development
```python
# Run migrations
django_migrate("properties")

# Collect static files
django_collectstatic()
```

## 🧪 Testing

Run the comprehensive test suite:
```bash
python test_complete.py
```

Individual service tests:
```bash
python test_tools.py          # Test file system and database
python explore_schema.py      # Explore database schema
```

## 🚀 Integration with MCP Clients

### VS Code Integration
1. Install MCP-compatible extension
2. Configure server endpoint
3. Use AI assistant with CRM context

### Claude Desktop Integration  
1. Add server configuration to Claude config
2. Restart Claude Desktop
3. Access CRM data through conversations

## 📈 Performance

- **Database**: 3,228 properties queryable in milliseconds
- **File System**: Instant access to Django project files
- **Memory**: Efficient connection pooling
- **Security**: Zero file system escapes in testing

## 🐛 Troubleshooting

### Database Connection Issues
```bash
# Test MariaDB connection
mysql -u root -p django_db_glomart_rs

# Check service status
brew services list | grep mariadb
```

### Import Errors
```bash
# Verify virtual environment
source venv/bin/activate
python -c "import mcp; print('✅ MCP installed')"
```

### File Access Denied
- Ensure CRM_PROJECT_PATH in .env is correct
- Check file permissions
- Verify path exists and is accessible

## 🔮 Future Enhancements

- [ ] Real-time property updates via WebSocket
- [ ] Advanced analytics and reporting tools  
- [ ] Integration with external real estate APIs
- [ ] Multi-tenant support for different agencies
- [ ] Automated property valuation models

## 📝 License

This MCP server is part of the Glomart CRM system for internal use.

## 🤝 Support

For technical support or questions about the MCP server:
1. Check the troubleshooting section
2. Run diagnostic tests
3. Review error logs in stderr output
4. Verify environment configuration

---

**Status**: ✅ Fully Operational | **Version**: 1.0.0 | **Last Updated**: September 21, 2025