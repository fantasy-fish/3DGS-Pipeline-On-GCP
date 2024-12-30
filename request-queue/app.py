from fastapi import FastAPI, HTTPException, BackgroundTasks
from google.cloud import pubsub_v1
from google.cloud import storage
import uuid
import json
import os
from util import setup_google_cloud_logging, get_redis_client
from models import ProcessingRequest, QueueStatus, RequestStatus
from datetime import datetime

app = FastAPI()
client, cloud_logger = setup_google_cloud_logging()

# Initialize clients
publisher = pubsub_v1.PublisherClient()
storage_client = storage.Client()
redis_client = get_redis_client()

# Configure topic path
project_id = os.getenv('PROJECT_ID', 'threed-reconstruction-431616')
topic_path = publisher.topic_path(project_id, 'reconstruction-requests')

@app.post("/enqueue")
async def enqueue_request(request: ProcessingRequest, background_tasks: BackgroundTasks):
    """Enqueue a new reconstruction request"""
    try:
        request_id = str(uuid.uuid4())
        
        # Create request metadata
        request_data = {
            "status": "QUEUED",
            "created_at": datetime.utcnow().isoformat(),
            "session_id": request.session_id,
            "callback_token": request.callback_token,
            "priority": request.priority
        }
        
        # Store in Redis
        redis_client.hset(f"request:{request_id}", mapping=request_data)
        
        # Add to priority queue
        redis_client.zadd("request_queue", {request_id: request.priority})
        
        # Publish message to start processing
        message = {
            "request_id": request_id,
            "session_id": request.session_id,
            "callback_token": request.callback_token
        }
        
        data = json.dumps(message).encode("utf-8")
        future = publisher.publish(topic_path, data)
        
        cloud_logger.info(f"Request {request_id} enqueued for session {request.session_id}")
        
        return {
            "request_id": request_id,
            "status": "QUEUED",
            "message": "Request has been queued for processing"
        }

    except Exception as e:
        cloud_logger.error(f"Error enqueueing request: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/status/{request_id}")
async def get_status(request_id: str):
    """Get the status of a queued request"""
    try:
        request_data = redis_client.hgetall(f"request:{request_id}")
        if not request_data:
            raise HTTPException(status_code=404, detail="Request not found")
        
        # Convert bytes to strings if necessary
        request_data = {k.decode('utf-8') if isinstance(k, bytes) else k: 
                       v.decode('utf-8') if isinstance(v, bytes) else v 
                       for k, v in request_data.items()}
        
        return RequestStatus(**request_data)

    except Exception as e:
        cloud_logger.error(f"Error getting status for request {request_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/queue")
async def get_queue_status():
    """Get overall queue status"""
    try:
        # Get all request keys
        request_keys = redis_client.keys("request:*")
        
        # Initialize counters
        total_requests = len(request_keys)
        status_counts = {"QUEUED": 0, "PROCESSING": 0, "COMPLETED": 0, "FAILED": 0}
        
        # Count requests by status
        for key in request_keys:
            status = redis_client.hget(key, "status")
            if status:
                status = status.decode('utf-8') if isinstance(status, bytes) else status
                status_counts[status] = status_counts.get(status, 0) + 1

        return QueueStatus(
            total_requests=total_requests,
            queued_requests=status_counts["QUEUED"],
            processing_requests=status_counts["PROCESSING"],
            completed_requests=status_counts["COMPLETED"],
            failed_requests=status_counts["FAILED"]
        )

    except Exception as e:
        cloud_logger.error(f"Error getting queue status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/status/{request_id}")
async def update_status(request_id: str, status: str):
    """Update the status of a request (internal use)"""
    try:
        if not redis_client.exists(f"request:{request_id}"):
            raise HTTPException(status_code=404, detail="Request not found")
        
        redis_client.hset(f"request:{request_id}", 
                         mapping={
                             "status": status,
                             "updated_at": datetime.utcnow().isoformat()
                         })
        
        # If completed or failed, remove from queue
        if status in ["COMPLETED", "FAILED"]:
            redis_client.zrem("request_queue", request_id)
        
        return {"message": f"Status updated to {status}"}

    except Exception as e:
        cloud_logger.error(f"Error updating status for request {request_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/next")
async def get_next_request():
    """Get the next request from the priority queue"""
    try:
        # Get highest priority request
        next_request = redis_client.zrange("request_queue", 0, 0, withscores=True)
        if not next_request:
            raise HTTPException(status_code=404, detail="No requests in queue")
        
        request_id = next_request[0][0].decode('utf-8')
        request_data = await get_status(request_id)
        
        return request_data

    except Exception as e:
        cloud_logger.error(f"Error getting next request: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.on_event("shutdown")
async def shutdown_event():
    cloud_logger.info("Shutting down request queue service")
    redis_client.close()
    client.close() 