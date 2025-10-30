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
      libwebp-dev && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy only requirements first to leverage Docker layer caching
COPY requirements.txt /app/requirements.txt

# Upgrade packaging tools and install dependencies (prefer binary wheels)
RUN python -m pip install --upgrade pip setuptools wheel build && \
    python -m pip install --prefer-binary -r requirements.txt

# Copy the rest of the app
COPY . /app

# Expose port used by Uvicorn/ASGI
EXPOSE 8000

# Default command - run with uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
