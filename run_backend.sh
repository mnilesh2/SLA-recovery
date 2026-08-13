#!/bin/bash

# Load environment variables from .env file
export $(grep -v '^#' .env | xargs)

# Activate virtual environment
source .venv/bin/activate

# Start backend
uvicorn backend.main:app --reload
