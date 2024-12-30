# Use the provided Dockerfile as base
# FROM 3dgs-base-image:latest
FROM us-central1-docker.pkg.dev/threed-reconstruction-431616/gs-pipeline/3dgs-base-image:original

# Set up the application
WORKDIR /app
COPY . /app

ENV INPUT_BUCKET once3d-upload
ENV OUTPUT_BUCKET once3d-output

# Install Python dependencies
COPY requirements.txt .
RUN pip3 install -r requirements.txt

# comment the tensorboard import command
RUN python /app/modify_train.py

# Run the FastAPI app
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080"]