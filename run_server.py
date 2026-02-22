#!/usr/bin/env python3
"""
Direct Python startup script for Canvas MCP Server
This avoids bash script permission issues that can occur with some MCP clients
"""

import os
import sys
from pathlib import Path

def main():
    # Get the directory containing this script
    script_dir = Path(__file__).parent.absolute()
    
    # Load environment variables from .env file
    env_file = script_dir / '.env'
    if env_file.exists():
        print(f"Loading environment from: {env_file}", file=sys.stderr)
        from dotenv import load_dotenv
        load_dotenv(env_file)
    else:
        print(f"Error: .env file not found at {env_file}", file=sys.stderr)
        sys.exit(1)
    
    # Verify required environment variables
    if not os.getenv('CANVAS_API_TOKEN') or not os.getenv('CANVAS_API_URL'):
        print("Error: CANVAS_API_TOKEN and CANVAS_API_URL must be set in .env file", file=sys.stderr)
        sys.exit(1)
    
    # Change to script directory
    os.chdir(script_dir)
    
    # Add src to Python path
    sys.path.insert(0, str(script_dir / 'src'))
    
    # Import and run the server
    try:
        from canvas_mcp.server import main as server_main
        server_main()
    except ImportError as e:
        print(f"Error importing Canvas MCP server: {e}", file=sys.stderr)
        print("Make sure the package is properly installed in the virtual environment", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()