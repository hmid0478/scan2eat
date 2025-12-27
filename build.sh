#!/usr/bin/env bash
# Render Build Script

set -o errexit

echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "Initializing database..."
python init_db.py

echo "Build completed successfully!"
