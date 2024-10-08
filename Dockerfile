# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    meson \
    ninja-build \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libxcb-xinerama0 \
    wget \
    git \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Lc0 (update this URL to the latest version)
RUN wget https://github.com/LeelaChessZero/lc0/archive/refs/tags/v0.31.1.tar.gz \
    && tar -xzf v0.31.1.tar.gz \
    && mv lc0-0.31.1 lc0 \
    && cd lc0 \
    && meson setup build \
    && meson compile -C build \
    && cp build/lc0 /usr/local/bin/  \
    && cd /app \
    && rm v0.31.1.tar.gz

# Verify Lc0 installation
RUN which lc0 && lc0 --version

# Copy requirements.txt and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the model file into the container
COPY model.pb.gz /app/

# Copy the current directory contents into the container at /app
COPY . /app

# Make port 10000 available to the world outside this container
EXPOSE 10000

# Set environment variables
ENV PORT=10000

# Run app.py when the container launches
CMD ["gunicorn", "app:app"]