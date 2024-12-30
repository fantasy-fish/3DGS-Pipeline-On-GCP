FROM python:3.9-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Run the FastAPI app
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080"] 