#!/usr/bin/env python3
"""
MCP Server Setup for LoyaltyAnalytics
Downloads and configures the required MCP servers.
"""

import os
import shutil
import platform
import subprocess
import requests
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MCP_DIR = Path(__file__).parent / "mcp_servers"
TOOLBOX_VERSION = "v0.13.0"


def get_system_info():
    """Get system architecture information."""
    system = platform.system().lower()
    machine = platform.machine().lower()
    
    if system == "darwin":
        arch = "arm64" if machine == "arm64" else "amd64"
    elif system == "linux":
        arch = "amd64"
    elif system == "windows":
        arch = "amd64"
    else:
        raise ValueError(f"Unsupported system: {system}")
    
    return system, arch


def download_toolbox():
    """Download the MCP Toolbox binary for database operations."""
    system, arch = get_system_info()
    
    # Create MCP directory
    MCP_DIR.mkdir(exist_ok=True)
    
    # Determine binary name and URL
    if system == "windows":
        binary_name = "toolbox.exe"
    else:
        binary_name = "toolbox"
    
    binary_path = MCP_DIR / binary_name

    # Check if toolbox exists in MCP_DIR
    if binary_path.exists():
        logger.info(f"Toolbox binary already exists: {binary_path}")
        return binary_path

    # Also check if toolbox exists in system PATH (e.g., /usr/local/bin/toolbox)    
    system_toolbox_path = shutil.which(binary_name)
    if system_toolbox_path:
        logger.info(f"Toolbox binary found in system PATH: {system_toolbox_path}")
        # Create an alias in MCP_DIR pointing to the system toolbox
        try:
            if not binary_path.exists():
                binary_path.symlink_to(system_toolbox_path)
                logger.info(f"Created symlink: {binary_path} -> {system_toolbox_path}")
        except Exception as e:
            logger.warning(f"Could not create symlink for toolbox: {e}")
            binary_path = system_toolbox_path
            
        return binary_path
    
    # Download URL based on the documentation
    url = f"https://storage.googleapis.com/genai-toolbox/{TOOLBOX_VERSION}/{system}/{arch}/{binary_name}"
    
    logger.info(f"Downloading toolbox from {url}")
    
    try:
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()
        
        with open(binary_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        # Make executable on Unix systems
        if system != "windows":
            os.chmod(binary_path, 0o755)
        
        logger.info(f"Successfully downloaded toolbox to {binary_path}")
        
        # Verify installation
        result = subprocess.run([str(binary_path), "--version"], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            logger.info(f"Toolbox version: {result.stdout.strip()}")
        else:
            logger.warning(f"Toolbox verification failed: {result.stderr}")
        
        return binary_path
        
    except Exception as e:
        logger.error(f"Failed to download toolbox: {e}")
        if binary_path.exists():
            binary_path.unlink()
        raise


def setup_vizro_mcp():
    """Set up Vizro MCP server using Docker."""
    logger.info("Setting up Vizro MCP server...")
    
    # Check if Docker is available
    try:
        subprocess.run(["docker", "--version"], 
                      capture_output=True, check=True, timeout=10)
        logger.info("Docker is available")
    except (subprocess.CalledProcessError, FileNotFoundError):
        logger.error("Docker is not available. Please install Docker to use Vizro MCP.")
        return False
    
    # Pull the Vizro MCP image (this is a placeholder - actual image may vary)
    try:
        logger.info("Pulling Vizro MCP Docker image...")
        subprocess.run(["docker", "pull", "mcp/vizro:latest"], 
                      check=True, timeout=120)
        logger.info("Vizro MCP Docker image ready")
        return True
    except subprocess.CalledProcessError as e:
        logger.warning(f"Failed to pull Vizro MCP image: {e}")
        # For now, we'll continue without Vizro MCP
        return False


def create_mcp_config():
    """Create MCP configuration for the servers using working mcpui-sandbox-chat format."""
    from config import settings
    
    toolbox_path = download_toolbox()
    
    # Use the working format from mcpui-sandbox-chat
    mcp_config = {
        "servers": [
            {
                "name": "postgres_toolbox",
                "enabled": True,
                "connection_type": "stdio",
                "command": f"./mcp_servers/{toolbox_path.name}",
                "args": ["--prebuilt", "postgres", "--stdio"],
                "env_vars": {
                    "POSTGRES_HOST": settings.postgres_host,
                    "POSTGRES_PORT": str(settings.postgres_port),
                    "POSTGRES_DATABASE": settings.postgres_database,
                    "POSTGRES_USER": settings.postgres_user,
                    "POSTGRES_PASSWORD": settings.postgres_password
                },
                "description": "PostgreSQL database operations via MCP Toolbox"
            },
            {
                "name": "filesystem",
                "enabled": False,
                "connection_type": "stdio",
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-filesystem", str(Path.cwd())],
                "description": "File system operations for the project directory"
            }
        ]
    }
    
    return mcp_config


if __name__ == "__main__":
    logger.info("Setting up MCP servers for LoyaltyAnalytics...")
    
    try:
        config = create_mcp_config()
        
        # Save config to file for reference
        import json
        config_path = MCP_DIR / "mcp_config.json"
        with open(config_path, "w") as f:
            json.dump(config, f, indent=2)
        
        logger.info(f"MCP configuration saved to {config_path}")
        logger.info("MCP setup completed successfully!")
        
        # Print available tools
        toolbox_path = MCP_DIR / ("toolbox.exe" if platform.system().lower() == "windows" else "toolbox")
        if toolbox_path.exists():
            logger.info("Available PostgreSQL tools:")
            logger.info("- postgres-execute-sql: Execute SQL statements")
            logger.info("- postgres-sql: Query the database")
        
    except Exception as e:
        logger.error(f"MCP setup failed: {e}")
        exit(1)
