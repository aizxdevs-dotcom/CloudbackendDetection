#!/usr/bin/env bash
set -euo pipefail

# Small helper script to run on Render (or other CI) before installing requirements.
# It upgrades pip/setuptools/wheel so packages like Pillow use prebuilt wheels where
# possible and avoids PEP 517 build-time errors.

echo "Upgrading pip, setuptools, wheel and build..."
python -m pip install --upgrade pip setuptools wheel build

echo "Installing requirements..."
python -m pip install -r requirements.txt

echo "Done."
