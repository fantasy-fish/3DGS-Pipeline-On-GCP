from fastapi import FastAPI, Request, HTTPException, Query, BackgroundTasks
from util import extract_mesh, setup_google_cloud_logging
import logging
import uuid
import os
import json

JOB_UUID = str(uuid.uuid4())

app = FastAPI()
client, cloud_logger = setup_google_cloud_logging()

def get_job_status(request_id: str, callback_token: str):
    status_file = os.path.join('/output', request_id, f"{callback_token}-mesh.json")
    if os.path.exists(status_file):
        with open(status_file, 'r') as f:
            return json.load(f)
    return None

def set_job_status(request_id: str, callback_token: str, status: dict):
    status_file = os.path.join('/output', request_id, f"{callback_token}-mesh.json")
    os.makedirs(os.path.dirname(status_file), exist_ok=True)
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

def extract_mesh_async(cloud_logger, INPUT_FOLDER_PATH, OUTPUT_FOLDER_PATH, request_id, callback_token, save_temp_files=True):
    try:
        cloud_logger.info(f"Starting mesh extraction for callback_token: {callback_token}")
        result = extract_mesh(cloud_logger, INPUT_FOLDER_PATH, OUTPUT_FOLDER_PATH, save_temp_files)
        cloud_logger.info(f"Mesh extraction completed for callback_token: {callback_token}")
        set_job_status(request_id, callback_token, {"status": "COMPLETED", "output": result})
    except Exception as e:
        cloud_logger.error(f"Error during mesh extraction for callback_token {callback_token}: {str(e)}")
        set_job_status(request_id, callback_token, {"status": "FAILED", "error": str(e)})
    finally:
        cloud_logger.info(f"Mesh extraction task finished for callback_token: {callback_token}")

@app.post("/extract-mesh")
async def extract_mesh_app(request: Request, background_tasks: BackgroundTasks):
    try:
        body = await request.json()
        cloud_logger.info(f"Received body: {body}")

        callback_token = body['callback_token']
        request_id = body['request_id']
        try:
            save_temp_files = body.get('save_temp_files', True)
            cloud_logger.info(f"From request: Meshroom save_temp_files flag equals {save_temp_files}")
        except:
            save_temp_files = True
            cloud_logger.info(f"From request: Meshroom save_temp_files flag equals {save_temp_files}")

        cloud_logger.info(f"Received event: {body}")

        INPUT_FOLDER_PATH = os.path.join("/input", request_id)
        OUTPUT_FOLDER_PATH = os.path.join("/output", request_id)
        mesh_path = os.path.join(OUTPUT_FOLDER_PATH, "mesh")

        if os.path.exists(mesh_path):
            cloud_logger.info(f"Output mesh folder already exists for job {JOB_UUID}")
            set_job_status(request_id, callback_token, {"status": "COMPLETED", "output": mesh_path})
            return {"status": "success", "message": "File has already been processed", "job_id": JOB_UUID}

        os.makedirs(OUTPUT_FOLDER_PATH, exist_ok=True)

        # Check for required files and directories
        images_path = os.path.join(OUTPUT_FOLDER_PATH, "images")
        sparse_path = os.path.join(OUTPUT_FOLDER_PATH, "sparse", "0")
        cameras_bin_path = os.path.join(sparse_path, "cameras.bin")
        images_bin_path = os.path.join(sparse_path, "images.bin")
        points3D_bin_path = os.path.join(sparse_path, "points3D.bin")

        required_paths = [cameras_bin_path, images_bin_path, points3D_bin_path, images_path, sparse_path]
        missing_paths = [path for path in required_paths if not os.path.exists(path)]

        if missing_paths:
            return {"status": "error", "message": f"Missing required files or directories: {missing_paths}", "job_id": JOB_UUID}

        cloud_logger.info(f"Starting mesh extraction for job {JOB_UUID}")
        
        background_tasks.add_task(extract_mesh_async, cloud_logger, INPUT_FOLDER_PATH, OUTPUT_FOLDER_PATH, request_id, callback_token, save_temp_files)
        
        set_job_status(request_id, callback_token, {"status": "PROCESSING"})
        return {"status": "processing", "message": "Mesh extraction started", "job_id": JOB_UUID}
    
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
    return {"message": "Mesh extraction API is running"}

@app.on_event("shutdown")
async def shutdown_event():
    logging.info("Application shutting down")
    client.close()
