#!/bin/bash

# checkpoint.sh — Kirokyu project checkpoint utility
# Creates a clean zip of the project (excluding venv, git, caches)
# and copies it to Windows Desktop for easy attachment to Claude chats.

set -e

# Configuration
PROJECT_DIR="$HOME/projects/kirokyu"
WINDOWS_DESKTOP="/mnt/c/Users/Homer/Desktop"  # ← CHANGE "Homer" to your Windows username
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
ZIP_NAME="kirokyu_${TIMESTAMP}.zip"
ZIP_PATH="$PROJECT_DIR/${ZIP_NAME}"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if project directory exists
if [ ! -d "$PROJECT_DIR" ]; then
    echo -e "${RED}Error: Project directory not found at $PROJECT_DIR${NC}"
    exit 1
fi

# Check if Windows Desktop exists
if [ ! -d "$WINDOWS_DESKTOP" ]; then
    echo -e "${RED}Error: Windows Desktop not found at $WINDOWS_DESKTOP${NC}"
    echo "Update the script with your actual Windows username."
    exit 1
fi

# Check for uncommitted changes
echo -e "${BLUE}Checking git status...${NC}"
cd "$PROJECT_DIR"
if [ -n "$(git status --porcelain)" ]; then
    echo -e "${RED}Warning: You have uncommitted changes:${NC}"
    git status --short
    echo ""
    read -p "Continue anyway? (y/N): " CONFIRM
    if [[ "$CONFIRM" != "y" && "$CONFIRM" != "Y" ]]; then
        echo "Checkpoint aborted. Commit your changes first."
        exit 1
    fi
    echo ""
else
    echo -e "${GREEN}✓ Working tree is clean${NC}"
    echo ""
fi

echo -e "${BLUE}Creating checkpoint for Kirokyu...${NC}"
echo "Project directory: $PROJECT_DIR"
echo "Output zip: $ZIP_PATH"
echo ""

# Change to parent directory to create the zip
cd "$(dirname "$PROJECT_DIR")"

# Create the zip, excluding unnecessary directories
echo -e "${BLUE}Zipping project (excluding venv, .git, caches)...${NC}"
zip -r -q "$ZIP_PATH" kirokyu \
    -x "kirokyu/.venv/*" \
       "kirokyu/.git/*" \
       "kirokyu/.mypy_cache/*" \
       "kirokyu/.pytest_cache/*" \
       "kirokyu/.ruff_cache/*" \
       "kirokyu/__pycache__/*" \
       "kirokyu/*/__pycache__/*" \
       "kirokyu/*/*/__pycache__/*"

if [ ! -f "$ZIP_PATH" ]; then
    echo -e "${RED}Error: Failed to create zip file${NC}"
    exit 1
fi

# Get file size
ZIP_SIZE=$(du -h "$ZIP_PATH" | cut -f1)
echo -e "${GREEN}✓ Zip created successfully${NC}"
echo "  Size: $ZIP_SIZE"
echo ""

# Copy to Windows Desktop
echo -e "${BLUE}Copying to Windows Desktop...${NC}"
cp "$ZIP_PATH" "$WINDOWS_DESKTOP/$ZIP_NAME"

if [ ! -f "$WINDOWS_DESKTOP/$ZIP_NAME" ]; then
    echo -e "${RED}Error: Failed to copy to Windows Desktop${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Copied to Windows Desktop${NC}"
echo "  Location: $WINDOWS_DESKTOP/$ZIP_NAME"
echo ""

# Summary
echo -e "${GREEN}Checkpoint complete!${NC}"
echo ""
echo "Next steps:"
echo "  1. Open your Claude chat"
echo "  2. Attach the file: $ZIP_NAME"
echo "  3. Let Claude know the checkpoint is ready"
echo ""
echo "The zip file is ready for upload."
