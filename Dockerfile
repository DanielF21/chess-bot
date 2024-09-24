# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies for building Lc0
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libxcb-xinerama0 \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Download Lc0 source code
RUN wget https://github.com/LeelaChessZero/lc0/archive/refs/tags/v0.31.1.tar.gz \
    && tar -xzf v0.31.1.tar.gz \
    && mv lc0-0.31.1 lc0 \
    && rm v0.31.1.tar.gz

# Build Lc0 from source
WORKDIR /app/lc0/build  # Change directory to build folder
RUN mkdir build && cd build && cmake .. && make  # Build process

# Copy requirements.txt and install Python dependencies if needed
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the current directory contents into the container at /app
COPY . /app

# Make port 10000 available to the world outside this container
EXPOSE 10000

# Set environment variables
ENV PORT=10000

# Run app.py when the container launches (adjust as necessary)
CMD ["gunicorn", "app:app"]