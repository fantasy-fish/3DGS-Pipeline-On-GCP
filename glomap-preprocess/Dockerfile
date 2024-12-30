# Use the provided Dockerfile as base
FROM glomap:latest

# Keep all the existing setup from the base Dockerfile

# Additional setup for the FastAPI app
RUN apt-get update && apt-get install -y \
    python3-pip \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Install Python packages
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Set up the application
WORKDIR /app
COPY . /app

ENV INPUT_BUCKET once3d-upload
ENV OUTPUT_BUCKET once3d-output

# Run the FastAPI app
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080"]