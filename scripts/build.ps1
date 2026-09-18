$ErrorActionPreference = "Stop"

python -m pip install --upgrade build twine
python -m build

Write-Host "Build completed. Files are in dist/"
