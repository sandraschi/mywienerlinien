#!/bin/sh

# Exit on any error
set -e

echo "Starting Docsify documentation server..."

# Function to handle graceful shutdown
cleanup() {
    echo "Received shutdown signal, cleaning up..."
    if [ -n "$DOCSIFY_PID" ]; then
        kill -TERM "$DOCSIFY_PID" 2>/dev/null || true
        wait "$DOCSIFY_PID" 2>/dev/null || true
    fi
    echo "Cleanup complete"
    exit 0
}

# Set up signal handlers
trap cleanup TERM INT

# Function to start docsify server
start_docsify() {
    echo "Starting Docsify server on port 3300..."
    exec docsify serve . --port 3300 &
    DOCSIFY_PID=$!
    echo "Docsify server started with PID: $DOCSIFY_PID"
    
    # Wait for the process
    wait "$DOCSIFY_PID"
}

# Start the server
start_docsify 