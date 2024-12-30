FROM meshroom-base-image:latest

# Install Python and pip
RUN apt-get update && apt-get install -y python3 python3-pip

# Install Python dependencies
COPY requirements.txt .
RUN pip3 install -r requirements.txt

# Set up the application
WORKDIR /app
COPY . /app

# Run the FastAPI app
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080"]