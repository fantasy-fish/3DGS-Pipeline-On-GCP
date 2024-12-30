import os
import subprocess
import cv2
from google.cloud import logging as cloud_logging
import logging
import tempfile
import shutil
import asyncio
import requests
from google.auth.transport.requests import Request
from google.oauth2 import id_token

def setup_google_cloud_logging():
    # Initialize Google Cloud Logging client
    client = cloud_logging.Client()

    # Get the default handler and configure it to use Google Cloud Logging
    cloud_handler = client.get_default_handler()
    cloud_logger = logging.getLogger("cloudLogger")
    cloud_logger.setLevel(logging.DEBUG)
    cloud_logger.addHandler(cloud_handler)

    return client, cloud_logger

# def run_3dgs(cloud_logger, colmap_path, depth_path, output_path):
#     cloud_logger.info("Starting 3D Gaussian Splatting process")
    
#     command = f"python /workspace/gaussian-splatting/train.py -s {colmap_path} -d {depth_path} -m {output_path} --iterations 2000 --save_iterations 2000"
    
#     try:
#         cloud_logger.info(f"Executing command: {command}")
#         result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
#         cloud_logger.info("3D Gaussian Splatting process completed successfully")
#         cloud_logger.info(f"Output: {result.stdout}")
#         return "Processing completed"
#     except subprocess.CalledProcessError as e:
#         cloud_logger.error(f"Error during 3D Gaussian Splatting process: {str(e)}")
#         cloud_logger.error(f"Error output: {e.stderr}")
#         raise

def run_3dgs(cloud_logger, colmap_path, depth_path, output_path):
    cloud_logger.info("Starting 3D Gaussian Splatting process")
    # TODO: the training progress gets stuck at iteration 2000
    command = (
        f"python /workspace/gaussian-splatting/train.py "
        f"--disable_viewer "
        f"-s {colmap_path} "
        f"-d {depth_path} "
        f"-m {output_path} "
        f"--iterations 30000 "
        f"--save_iterations $(seq 1000 1000 30000)"
    )
    try:
        cloud_logger.info(f"Executing command: {command}")
        # Use bufsize=1 and universal_newlines=True to disable buffering
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=1, universal_newlines=True)
        # Read output in real-time
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                cloud_logger.info(output.strip())
        # Finished reading, check for error output
        stderr_output = process.stderr.read()
        if stderr_output:
            cloud_logger.error(f"3D Gaussian Splatting error message: {stderr_output}")
        return_code = process.wait()
        if return_code != 0:
            raise RuntimeError(f"3D Gaussian Splatting failed, error code: {return_code}")
        cloud_logger.info("3D Gaussian Splatting process completed successfully")
        return "Processing completed"
    except Exception as e:
        cloud_logger.error(f"An error occurred during 3D Gaussian Splatting: {str(e)}")
        raise