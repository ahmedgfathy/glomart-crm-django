#!/bin/bash

# Glomart CRM MCP Server Installation Script

echo "🚀 Setting up Glomart CRM MCP Server..."

# Navigate to MCP server directory
cd "$(dirname "$0")"

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js 18+ first."
    echo "Visit: https://nodejs.org/"
    exit 1
fi

# Check Node.js version
NODE_VERSION=$(node --version | cut -d'v' -f2)
REQUIRED_VERSION="18.0.0"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$NODE_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo "❌ Node.js version 18+ is required. Current version: $NODE_VERSION"
    exit 1
fi

echo "✅ Node.js version: $NODE_VERSION"

# Install dependencies
echo "📦 Installing dependencies..."
npm install

if [ $? -ne 0 ]; then
    echo "❌ Failed to install dependencies"
    exit 1
fi

# Build TypeScript
echo "🔨 Building TypeScript..."
npm run build

if [ $? -ne 0 ]; then
    echo "❌ Failed to build TypeScript"
    exit 1
fi

# Update environment file with current project path
echo "⚙️ Configuring environment..."
PROJECT_PATH="$(cd .. && pwd)"
sed -i.bak "s|PROJECT_ROOT=.*|PROJECT_ROOT=$PROJECT_PATH|" .env

# Check if MariaDB is installed
if command -v mysql &> /dev/null; then
    echo "✅ MySQL/MariaDB found"
else
    echo "⚠️ MySQL/MariaDB not found. Please ensure it's installed and accessible."
fi

# Create MCP configuration for Claude Desktop (if on macOS)
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "📱 Setting up Claude Desktop configuration..."
    
    CLAUDE_CONFIG_DIR="$HOME/Library/Application Support/Claude"
    CLAUDE_CONFIG_FILE="$CLAUDE_CONFIG_DIR/claude_desktop_config.json"
    
    # Create directory if it doesn't exist
    mkdir -p "$CLAUDE_CONFIG_DIR"
    
    # Create or update Claude Desktop configuration
    if [ -f "$CLAUDE_CONFIG_FILE" ]; then
        echo "⚠️ Claude Desktop config exists. Please manually add the MCP server configuration:"
        echo ""
        echo "Add this to your Claude Desktop config at:"
        echo "$CLAUDE_CONFIG_FILE"
        echo ""
        echo '{'
        echo '  "mcpServers": {'
        echo '    "glomart-crm": {'
        echo "      \"command\": \"node\","
        echo "      \"args\": [\"$PROJECT_PATH/mcp_server/dist/index.js\"]"
        echo '    }'
        echo '  }'
        echo '}'
    else
        cat > "$CLAUDE_CONFIG_FILE" << EOF
{
  "mcpServers": {
    "glomart-crm": {
      "command": "node",
      "args": ["$PROJECT_PATH/mcp_server/dist/index.js"]
    }
  }
}
EOF
        echo "✅ Claude Desktop configuration created"
    fi
fi

echo ""
echo "🎉 Installation completed!"
echo ""
echo "Next steps:"
echo "1. Update the database password in .env file:"
echo "   DB_PASSWORD=your_actual_mariadb_password"
echo ""
echo "2. Test the MCP server:"
echo "   npm run start"
echo ""
echo "3. If using Claude Desktop, restart it to load the MCP server"
echo ""
echo "4. Available MCP tools:"
echo "   - File operations (read, write, list, search)"
echo "   - Database operations (execute SQL, backup, table info)"
echo "   - Django management (migrate, collectstatic, shell)"
echo "   - Git operations (status, commit, push)"
echo "   - Project analysis (models, stats)"
echo ""
echo "Configuration file: $PROJECT_PATH/mcp_server/.env"
echo "MCP Server path: $PROJECT_PATH/mcp_server/dist/index.js"