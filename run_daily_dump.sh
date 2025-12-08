#!/bin/bash
set -euo pipefail

# Move to project directory
cd "/Users/anupamprasad/Documents/Python_File" || exit 1

# Export scheduler flag for the script
export ENABLE_SCHEDULER=0

# Run the Python script using the project's venv Python, log output
"/Users/anupamprasad/Documents/Python_File/.venv/bin/python3" "/Users/anupamprasad/Documents/Python_File/daily_supabase_dump.py" >> "/Users/anupamprasad/Documents/Python_File/cron.log" 2>&1
