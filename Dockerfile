# Use Python 3.12 as the base image
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libxcb-xinerama0 \
    wget \
    unzip \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Install Lc0
RUN wget https://github.com/LeelaChessZero/lc0/releases/download/v0.29.0/lc0-v0.29.0-linux-x64.tar.gz \
    && tar -xzf lc0-v0.29.0-linux-x64.tar.gz \
    && mv lc0 /usr/local/bin/ \
    && rm lc0-v0.29.0-linux-x64.tar.gz

# Copy the current directory contents into the container at /app
COPY . /app

# Upgrade pip and install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Make port 80 available to the world outside this container
EXPOSE 80

# Run chess_gui.py when the container launches
CMD ["python", "chess_gui.py"]