#!/usr/bin/env bash
set -euo pipefail

# Small helper script to run on Render (or other CI) before installing requirements.
# It upgrades pip/setuptools/wheel so packages like Pillow use prebuilt wheels where
# possible and avoids PEP 517 build-time errors.

echo "Python info:"
python --version || true
python -m pip --version || true

echo "Upgrading pip, setuptools, wheel and build..."
python -m pip install --upgrade pip setuptools wheel build

echo "Installing requirements (prefer binary wheels, verbose)..."
# Prefer binary wheels when available to avoid source builds for packages like Pillow
python -m pip install --prefer-binary -v -r requirements.txt

echo "Done."
