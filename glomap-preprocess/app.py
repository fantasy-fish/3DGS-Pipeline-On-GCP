from fastapi import FastAPI, Request, HTTPException, Query, BackgroundTasks
from util import run_glomap, setup_google_cloud_logging
import logging
import uuid
import os
import asyncio
import json

JOB_UUID = str(uuid.uuid4())

app = FastAPI()
client, cloud_logger = setup_google_cloud_logging()

def get_job_status(request_id: str, callback_token: str):
    status_file = os.path.join('/output', request_id, f"{callback_token}-glomap-preprocess.json")
    if os.path.exists(status_file):
        with open(status_file, 'r') as f:
            return json.load(f)
    return None

def set_job_status(request_id: str, callback_token: str, status: str):
    status_file = os.path.join('/output', request_id, f"{callback_token}-glomap-preprocess.json")
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

def run_glomap_async(cloud_logger, INPUT_FILE_PATH, OUTPUT_FOLDER_PATH, request_id, callback_token):
    try:
        cloud_logger.info(f"Starting glomap processing for callback_token: {callback_token}")
        result = run_glomap(cloud_logger, INPUT_FILE_PATH, OUTPUT_FOLDER_PATH)
        cloud_logger.info(f"Glomap processing completed for callback_token: {callback_token}")
        set_job_status(request_id, callback_token, {"status": "COMPLETED", "output": result})
    except Exception as e:
        cloud_logger.error(f"Error during glomap processing for callback_token {callback_token}: {str(e)}")
        set_job_status(request_id, callback_token, {"status": "FAILED", "error": str(e)})
    finally:
        cloud_logger.info(f"Glomap processing task finished for callback_token: {callback_token}")

@app.post("/preprocess-glomap")
async def preprocess_glomap(request: Request, background_tasks: BackgroundTasks):
    try:
        body = await request.json()
        cloud_logger.info(f"Received body: {body}")

        callback_token = body['callback_token']
        request_id = body['request_id']

        cloud_logger.info(f"Received event: {body}")

        INPUT_FILE_PATH = os.path.join("/input", request_id)
        OUTPUT_FOLDER_PATH = os.path.join("/output", request_id)
        image_path = os.path.join(OUTPUT_FOLDER_PATH, "images")

        if os.path.exists(image_path):
            cloud_logger.info(f"Output image folder already exists for job {JOB_UUID}")
            set_job_status(request_id, callback_token, {"status": "COMPLETED"})
            return {"status": "success", "message": "File has already been processed", "job_id": JOB_UUID}
        else:
            os.makedirs(OUTPUT_FOLDER_PATH, exist_ok=True)

        cloud_logger.info(f"Starting glomap preprocessing for job {JOB_UUID}")
        
        background_tasks.add_task(run_glomap_async, cloud_logger, INPUT_FILE_PATH, OUTPUT_FOLDER_PATH, request_id, callback_token)
        
        set_job_status(request_id, callback_token, {"status": "PROCESSING"})
        return {"status": "processing", "message": "Glomap preprocessing started", "job_id": JOB_UUID}
    
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
