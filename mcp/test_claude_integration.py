#!/usr/bin/env python3
"""
Test MCP Server for Claude Desktop Integration
"""

import sys
import os
from pathlib import Path

# Add the current directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

def test_mcp_readiness():
    """Test if MCP server is ready for Claude Desktop integration"""
    print("🔍 === MCP SERVER READINESS CHECK ===")
    
    # Check Python environment
    print(f"✅ Python version: {sys.version}")
    
    # Check virtual environment
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("✅ Virtual environment: Active")
    else:
        print("⚠️  Virtual environment: Not detected")
    
    # Check MCP package
    try:
        import mcp
        print(f"✅ MCP package: {mcp.__version__ if hasattr(mcp, '__version__') else 'Installed'}")
    except ImportError:
        print("❌ MCP package: Not found")
        return False
    
    # Check environment file
    env_file = Path(".env")
    if env_file.exists():
        print("✅ Environment file: Found")
    else:
        print("❌ Environment file: Missing")
        return False
    
    # Check Claude Desktop config
    claude_config = Path.home() / "Library/Application Support/Claude/claude_desktop_config.json"
    if claude_config.exists():
        print("✅ Claude Desktop config: Installed")
    else:
        print("❌ Claude Desktop config: Missing")
        return False
    
    # Check server file
    server_file = Path("server.py")
    if server_file.exists():
        print("✅ MCP server: Ready")
    else:
        print("❌ MCP server: Missing")
        return False
    
    print("\n🚀 === READY FOR CLAUDE DESKTOP ===")
    print("✅ All components are ready!")
    print("\nNext steps:")
    print("1. Restart Claude Desktop app")
    print("2. Look for 'glomart-crm' server in available tools")
    print("3. Start asking questions about your CRM data!")
    
    return True

if __name__ == "__main__":
    success = test_mcp_readiness()
    if success:
        print("\n🎉 MCP integration is ready!")
    else:
        print("\n⚠️  Please fix the issues above before using Claude Desktop")