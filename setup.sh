#!/bin/bash

# Make sure the script stops on first error
set -e

# Install Python dependencies
pip install -r requirements.txt

# Make directory for Streamlit config
mkdir -p ~/.streamlit

# Create Streamlit config file
echo "[server]
headless = true
port = $PORT
enableCORS = false
" > ~/.streamlit/config.toml
