#!/bin/bash
echo "Cleaning previous builds..."
rm -rf build dist
echo "Building application..."
pyinstaller build_config.spec --clean
echo "Build complete!" 