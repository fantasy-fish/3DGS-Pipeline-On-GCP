# 3DGS-Pipeline-On-GCP

An event-driven microservices-based backend system for 3D reconstruction from video/image input to mesh/GS output, leveraging GLOMAP, Depth-Anything-V2 and Gaussian Splatting technologies.

## System Architecture

The system consists of several microservices deployed on Google Cloud Platform:

1. **Request Queue Service**
   - Handles request queuing and prioritization
   - Uses Redis for persistent queue storage
   - Manages request lifecycle and status tracking
   - Provides queue status monitoring
   - Endpoints:
     - POST `/enqueue`: Submit new reconstruction request
     - GET `/status/{request_id}`: Check request status
     - GET `/queue`: Get queue statistics
     - GET `/next`: Get next request in queue
     - PUT `/status/{request_id}`: Update request status

2. **HTTP Trigger Service**
   - Handles initial requests
   - Manages rate limiting and request deduplication

3. **GLOMAP Preprocessing Service**
   - Extracts frames from video input
   - Performs COLMAP/GLOMAP processing
   - Generates sparse reconstruction

4. **Depth Estimation Service**
   - Uses Depth-Anything-V2 for depth estimation
   - Processes extracted frames
   - Generates depth maps

5. **Image Filtering Service**
   - Filters and processes images for quality
   - Prepares images for 3D reconstruction

## Prerequisites

- Docker with NVIDIA GPU support
- Google Cloud Platform account with:
  - Cloud Run
  - Cloud Storage
  - Cloud Build
  - Artifact Registry
  - Cloud Logging
  - Eventarc
  - Cloud Memorystore (Redis)
- Python 3.8+

## Queue System

### Redis-based Queue Features
- Priority-based request handling
- Persistent queue storage
- Request status tracking
- Queue statistics and monitoring
- Atomic operations for queue management

### Request States
- QUEUED: Initial state when request is submitted
- PROCESSING: Request is being processed
- COMPLETED: Processing finished successfully
- FAILED: Processing encountered an error

### Queue Management

## API Documentation

### HTTP Trigger Endpoint
- `POST /trigger-reconstruction`
  - Rate limited to 10 requests per minute
  - Requires JSON payload with session_id
  - Returns request ID for tracking

### GLOMAP Preprocessing Endpoint
- `POST /preprocess-video`
  - Processes uploaded videos
  - Returns job status and ID

### Status Endpoint
- `GET /status`
  - Query parameter: callback_token
  - Returns current processing status

## Security

The system implements several security measures:

1. Authentication using Google Cloud IAM
2. Rate limiting on HTTP triggers
3. Request deduplication
4. Secure cloud storage access
