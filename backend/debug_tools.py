#!/usr/bin/env python3
"""
Debug script to check what MCP tools are available.
"""
import asyncio
import sys
import json
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent))

async def main():
    try:
        from mcp_multi_client import mcp_manager
        from config import settings
        
        print("🔧 Initializing MCP manager...")
        await mcp_manager.initialize()
        
        print("📋 Listing all available tools...")
        tools = await mcp_manager.list_all_tools()
        
        print(f"\n🛠️  Found {len(tools)} servers:")
        for server_name, server_tools in tools.items():
            print(f"\n📦 Server: {server_name}")
            print(f"   Tools count: {len(server_tools)}")
            for tool in server_tools:
                print(f"   - {tool.get('name', 'unnamed')}: {tool.get('description', 'no description')}")
        
        print(f"\n📊 Testing execute_sql tool...")
        result = await mcp_manager.call_tool("execute_sql", {"sql": "SELECT COUNT(*) as table_count FROM information_schema.tables WHERE table_schema = 'public'"})
        print(f"SQL test result: {result}")
        
        print(f"\n📊 Testing list_tables tool...")
        result = await mcp_manager.call_tool("list_tables", {"table_names": "", "output_format": "simple"})
        print(f"List tables result: {result}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())