#!/bin/bash

# Update submodules
git submodule update --init --recursive

# Install Python dependencies
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "Error: Python dependencies installation failed"
    exit 1
fi

# Install custom aider
cd vendor/aider
pip install -e .
if [ $? -ne 0 ]; then
    echo "Error: Aider installation failed"
    exit 1
fi
cd ../..

# Install and build repo-visualizer
cd vendor/repo-visualizer
npm install --legacy-peer-deps
if [ $? -ne 0 ]; then
    echo "Error: repo-visualizer dependencies installation failed"
    exit 1
fi

npm install -g esbuild
if [ $? -ne 0 ]; then
    echo "Error: esbuild installation failed"
    exit 1
fi

mkdir -p dist
npm run build
if [ $? -ne 0 ]; then
    echo "Error: repo-visualizer build failed"
    exit 1
fi
cd ../..

# Create symbolic link for kin command
if [[ "$OSTYPE" == "darwin"* ]] || [[ "$OSTYPE" == "linux-gnu"* ]]; then
    sudo ln -sf "$(pwd)/kin" /usr/local/bin/kin
fi
