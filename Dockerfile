# Use Python 3.12 so prebuilt wheels for packages like Pillow are available
FROM python:3.12-slim

# Install minimal OS packages useful for building Python wheels and common
# native deps for Pillow. If you prefer smaller images and your packages
# already provide wheels for Python 3.12, you can remove some of these.
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      build-essential \
      pkg-config \
      libjpeg-dev \
      zlib1g-dev \
      libtiff-dev \
      libopenjp2-7-dev \
      libfreetype6-dev \
      liblcms2-dev \
      libwebp-dev \
      # Libraries required by OpenCV (prevents libGL.so.1 missing errors)
      libgl1 \
      libglib2.0-0 \
      libsm6 \
      libxrender1 \
      libxext6 && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy only requirements first to leverage Docker layer caching
COPY requirements.txt /app/requirements.txt

# Upgrade packaging tools and install dependencies (prefer binary wheels)
RUN python -m pip install --upgrade pip setuptools wheel build && \
    python -m pip install --prefer-binary -r requirements.txt

# Copy the rest of the app
COPY . /app

# Expose a default port (for docs/dev). Render provides $PORT at runtime.
EXPOSE 8000

# Default command - use PORT env var if present (fallback to 8000).
# Use sh -c so environment variable expansion works in the CMD.
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
