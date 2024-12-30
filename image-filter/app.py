from fastapi import FastAPI, Request, HTTPException, Query, BackgroundTasks
from util import process_image, setup_google_cloud_logging
import logging
import uuid
import os
import asyncio
import json

JOB_UUID = str(uuid.uuid4())

app = FastAPI()
client, cloud_logger = setup_google_cloud_logging()

def get_job_status(request_id: str, callback_token: str):
    status_file = os.path.join('/output', request_id, f"{callback_token}-image-filter.json")
    if os.path.exists(status_file):
        with open(status_file, 'r') as f:
            return json.load(f)
    return None

def set_job_status(request_id: str, callback_token: str, status: str):
    # Create the status file using both request_id and callback_token
    status_file = os.path.join('/output', request_id, f"{callback_token}-image-filter.json")
    
    # Write the status to the file
    with open(status_file, 'w') as f:
        json.dump(status, f)

    cloud_logger.info(f"Status updated for request_id: {request_id}, callback_token: {callback_token}")

@app.get("/status")
async def check_status(
    request_id: str = Query(..., description="Request ID for the job"),
    callback_token: str = Query(..., description="Callback token for job status")):
    cloud_logger.info(f"Checking status for callback_token: {callback_token}, request_id: {request_id}")

    status = get_job_status(request_id, callback_token)
    if status is None:
        raise HTTPException(status_code=404, detail="Job not found")
    
    cloud_logger.info(f"The status is: {status}")
    return status

def process_image_async(cloud_logger, INPUT_FOLDER_PATH, OUTPUT_FOLDER_PATH, request_id, callback_token):
    try:
        cloud_logger.info(f"Starting image processing for callback_token: {callback_token}")
        result = process_image(cloud_logger, INPUT_FOLDER_PATH, OUTPUT_FOLDER_PATH)
        cloud_logger.info(f"Image processing completed for callback_token: {callback_token}")
        set_job_status(request_id, callback_token, {"status": "COMPLETED", "output": result})
    except Exception as e:
        cloud_logger.error(f"Error during image processing for callback_token {callback_token}: {str(e)}")
        set_job_status(request_id, callback_token, {"status": "FAILED", "error": str(e)})
    finally:
        cloud_logger.info(f"Image processing task finished for callback_token: {callback_token}")

@app.post("/filter-image")
async def filter_image(request: Request, background_tasks: BackgroundTasks):
    try:
        body = await request.json()
        cloud_logger.info(f"Received body: {body}")

        # This is a new preprocessing request
        callback_token = body['callback_token']
        request_id = body['request_id']

        cloud_logger.info(f"Received event: {body}")

        INPUT_FOLDER_PATH = os.path.join("/input", request_id)
        OUTPUT_FOLDER_PATH = os.path.join("/output", request_id)
        output_path = os.path.join(OUTPUT_FOLDER_PATH, "source")
            
        if os.path.exists(output_path):
            cloud_logger.info(f"Output image folder already exists for job {JOB_UUID}")
            set_job_status(request_id, callback_token, {"status": "COMPLETED"})
            return {"status": "success", "message": "File has already been processed", "job_id": JOB_UUID}
        else:
            os.makedirs(output_path, exist_ok=True)

        cloud_logger.info(f"Starting image filtering for job {JOB_UUID}")
        
        background_tasks.add_task(process_image_async, cloud_logger, INPUT_FOLDER_PATH, output_path, request_id, callback_token)
        
        set_job_status(request_id, callback_token, {"status": "PROCESSING"})
        return {"status": "processing", "message": "Image filtering started", "job_id": JOB_UUID}
    
    except Exception as e:
        cloud_logger.error(f"Error processing request: {str(e)}")
        raise HTTPException(status_code=500, detail={
            "status": "error", 
            "message": str(e), 
            "job_id": JOB_UUID
        })

@app.get("/")
async def root():
    logging.info("Root endpoint accessed")
    return {"message": "Video processing API is running"}

@app.on_event("shutdown")
async def shutdown_event():
    logging.info("Application shutting down")
    client.close()
