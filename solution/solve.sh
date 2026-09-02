#!/bin/bash
set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET_DIR="${TARGET_ENGINE:-/app/engine}"

echo "Deploying solution engine from $SCRIPT_DIR/engine to $TARGET_DIR..."
mkdir -p "$TARGET_DIR"
cp -r "$SCRIPT_DIR/engine/"* "$TARGET_DIR/"
echo "Solution engine deployment complete."
