from fastapi import FastAPI, Request, HTTPException, Query, BackgroundTasks
from util import depth_generation, setup_google_cloud_logging
import logging
import uuid
import os
import json

JOB_UUID = str(uuid.uuid4())

app = FastAPI()
client, cloud_logger = setup_google_cloud_logging()

def get_job_status(request_id: str, callback_token: str):
    status_file = os.path.join('/output', request_id, f"{callback_token}-depth.json")
    if os.path.exists(status_file):
        with open(status_file, 'r') as f:
            return json.load(f)
    return None

def set_job_status(request_id: str, callback_token: str, status: str):
    status_file = os.path.join('/output', request_id, f"{callback_token}-depth.json")
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

def process_depth_async(cloud_logger, image_path, depth_path, request_id, callback_token):
    try:
        cloud_logger.info(f"Starting depth estimation for callback_token: {callback_token}")
        result = depth_generation(cloud_logger, image_path, depth_path, '/app/Depth-Anything-V2')
        cloud_logger.info(f"Depth estimation completed for callback_token: {callback_token}")
        set_job_status(request_id, callback_token, {"status": "COMPLETED", "output": result})
    except Exception as e:
        cloud_logger.error(f"Error during depth estimation for callback_token {callback_token}: {str(e)}")
        set_job_status(request_id, callback_token, {"status": "FAILED", "error": str(e)})
    finally:
        cloud_logger.info(f"Depth estimation task finished for callback_token: {callback_token}")

@app.post("/estimate-depth")
async def estimate_depth(request: Request, background_tasks: BackgroundTasks):
    try:
        body = await request.json()
        cloud_logger.info(f"Received body: {body}")

        callback_token = body['callback_token']
        request_id = body['request_id']

        cloud_logger.info(f"Received event: {body}")

        INPUT_FOLDER_PATH = os.path.join("/input", request_id)
        OUTPUT_FOLDER_PATH = os.path.join("/output", request_id)
        image_path = os.path.join(OUTPUT_FOLDER_PATH, "images")
        depth_path = os.path.join(OUTPUT_FOLDER_PATH, "depth")
        sparse_path = os.path.join(OUTPUT_FOLDER_PATH, "sparse", "0")

        if not os.path.exists(image_path):
            raise HTTPException(status_code=500, detail={"status": "error", "message": "Image path does not exist", "job_id": JOB_UUID})

        if not os.path.exists(sparse_path):
            raise HTTPException(status_code=500, detail={"status": "error", "message": "Sparse folder does not exist", "job_id": JOB_UUID})

        required_files = ['cameras.bin', 'images.bin', 'points3D.bin']
        missing_files = [file for file in required_files if not os.path.exists(os.path.join(sparse_path, file))]
        if missing_files:
            raise HTTPException(status_code=500, detail={"status": "error", "message": f"Missing required files: {', '.join(missing_files)}", "job_id": JOB_UUID})

        if os.path.exists(depth_path) and os.path.exists(os.path.join(sparse_path, 'depth_params.json')):
            image_count = len([f for f in os.listdir(image_path) if f.endswith('.jpg') or f.endswith('.png')])
            depth_count = len([f for f in os.listdir(depth_path) if f.endswith('.png')])
            if image_count == depth_count:
                set_job_status(request_id, callback_token, {"status": "COMPLETED", "output": depth_path})
                return {"status": "success", "message": "Files have already been processed", "job_id": JOB_UUID}

        os.makedirs(depth_path, exist_ok=True)

        cloud_logger.info(f"Starting depth estimation for job {JOB_UUID}")
        
        background_tasks.add_task(process_depth_async, cloud_logger, image_path, depth_path, request_id, callback_token)
        
        set_job_status(request_id, callback_token, {"status": "PROCESSING"})
        return {"status": "processing", "message": "Depth estimation started", "job_id": JOB_UUID}
    
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
    return {"message": "Depth estimation API is running"}

@app.on_event("shutdown")
async def shutdown_event():
    logging.info("Application shutting down")
    client.close()
