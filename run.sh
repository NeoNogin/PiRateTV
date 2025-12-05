#!/bin/bash
# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE}" )" && pwd )"
# Activate the virtual environment and run the main application
source "$SCRIPT_DIR/venv/bin/activate"
# Run the main application. All output will be handled by systemd's journal.
python3 "$SCRIPT_DIR/main.py"