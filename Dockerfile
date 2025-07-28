# Use Python base image
FROM python:3.10-slim

# Install Python dependencies
RUN pip install --no-cache-dir PyMuPDF

# Set working directory to project root
WORKDIR /project

# Copy source code and input/output folders
COPY src/ src/
COPY app/ app/

# Command to run the script
CMD ["python", "src/main.py"]
