#!/bin/bash

# Update submodules
git submodule update --init --recursive

# Install Python dependencies
pip install -r requirements.txt

# Install custom aider
cd vendor/aider
pip install -e .
cd ../..

# Install and build repo-visualizer
cd vendor/repo-visualizer
npm install --legacy-peer-deps
npm install -g esbuild
mkdir -p dist
npm run build
cd ../..

# Create symbolic link for kin command
if [[ "$OSTYPE" == "darwin"* ]] || [[ "$OSTYPE" == "linux-gnu"* ]]; then
    sudo ln -sf "$(pwd)/kin" /usr/local/bin/kin
fi
