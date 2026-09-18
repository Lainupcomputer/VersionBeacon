#!/usr/bin/env sh
set -eu

python -m pip install --upgrade build twine
python -m build

echo "Build completed. Files are in dist/"
