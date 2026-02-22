#!/bin/bash

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
echo "Script directory: $SCRIPT_DIR" >&2

# Print startup message (directed to stderr so it doesn't interfere with JSON)
echo "Starting Canvas MCP Server..." >&2

# Path to your virtual environment
VENV_PATH="$SCRIPT_DIR/.venv"
echo "Using virtual environment at: $VENV_PATH" >&2

# Activate the virtual environment
echo "Activating virtual environment..." >&2
source "$VENV_PATH/bin/activate"

# Load environment variables from .env file
ENV_FILE="$SCRIPT_DIR/.env"
if [ -f "$ENV_FILE" ]; then
    echo "Loading environment variables from .env file: $ENV_FILE" >&2
    while IFS='=' read -r key value; do
        # Skip comments and empty lines
        [[ "$key" =~ ^[[:space:]]*# ]] && continue
        [[ -z "$key" ]] && continue
        # Trim whitespace
        key=$(echo "$key" | xargs)
        value=$(echo "$value" | xargs)
        [ -n "$key" ] && export "$key=$value"
    done < "$ENV_FILE"
else
    echo "Error: .env file not found at $ENV_FILE. Please create one with CANVAS_API_TOKEN and CANVAS_API_URL" >&2
    exit 1
fi

# Verify required environment variables are set
if [ -z "$CANVAS_API_TOKEN" ] || [ -z "$CANVAS_API_URL" ]; then
    echo "Error: CANVAS_API_TOKEN and CANVAS_API_URL must be set in .env file" >&2
    exit 1
fi

# Go to the script directory
cd $SCRIPT_DIR
echo "Changed directory to: $(pwd)" >&2

# Run the Canvas MCP server
echo "Starting Canvas MCP server" >&2
"$VENV_PATH/bin/irq-canvas-mcp"

# Exit message
echo "Server stopped" >&2