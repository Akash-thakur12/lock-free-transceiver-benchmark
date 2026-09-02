#!/bin/bash
set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TASK_ROOT="$SCRIPT_DIR/.."
TARGET_DIR="${TARGET_ENGINE:-$TASK_ROOT/environment/engine}"

echo "Deploying solution engine to $TARGET_DIR..."
mkdir -p "$TARGET_DIR"
cp -r "$SCRIPT_DIR/engine/"* "$TARGET_DIR/"
echo "Solution deployment complete."
