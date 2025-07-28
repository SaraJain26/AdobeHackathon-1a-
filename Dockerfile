# Use Python base image
FROM python:3.10-slim

# Install required system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libglib2.0-0 \
    libgl1-mesa-glx \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir PyMuPDF

# Set working directory to project root
WORKDIR /project

# Copy source code and input/output folders
COPY src/ src/
COPY app/ app/

# Command to run the script
CMD ["python", "src/main.py"]
