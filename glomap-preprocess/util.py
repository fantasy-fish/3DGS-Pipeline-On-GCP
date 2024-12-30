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

def run_glomap(cloud_logger, INPUT_FILE_PATH, OUTPUT_FOLDER_PATH, save_temp_files=True):
    cloud_logger.info(f"Starting glomap processing for {INPUT_FILE_PATH}")
    
    # Set up working directories in OUTPUT_FOLDER_PATH
    source_image_path = os.path.join(INPUT_FILE_PATH, "source")
    
    # Handle temporary directory
    if save_temp_files:
        temp_dir = os.path.join(OUTPUT_FOLDER_PATH, "temp")
        os.makedirs(temp_dir, exist_ok=True)
    else:
        temp_dir = tempfile.TemporaryDirectory().name
    
    # Set up paths using temp_dir
    image_path = os.path.join(temp_dir, "source")
    database_path = os.path.join(temp_dir, "database.db")
    distorted_folder = os.path.join(temp_dir, "distorted")
    
    # Create necessary directories
    os.makedirs(image_path, exist_ok=True)
    os.makedirs(distorted_folder, exist_ok=True)
    
    try:
        # Copy images from source to working directory
        shutil.copytree(source_image_path, image_path, dirs_exist_ok=True)
        cloud_logger.info(f"Successfully copied images from {source_image_path} to {image_path}")

        # Set environment variables for the commands
        os.environ['BASE_FOLDER'] = OUTPUT_FOLDER_PATH
        os.environ['IMAGE_PATH'] = image_path
        os.environ['DATABASE_PATH'] = database_path
        os.environ['DISTORTED_FOLDER'] = distorted_folder
        os.environ['MATCHER_TYPE'] = 'exhaustive_matcher'
        cloud_logger.info("Environment variables set for COLMAP and GLOMAP")
        
        # Run COLMAP and GLOMAP commands
        command = f"""
        colmap feature_extractor --image_path $IMAGE_PATH --database_path $DATABASE_PATH --ImageReader.single_camera 1 --ImageReader.camera_model PINHOLE --SiftExtraction.use_gpu 1 && \
        colmap $MATCHER_TYPE --database_path $DATABASE_PATH && \
        glomap mapper --database_path $DATABASE_PATH --image_path $IMAGE_PATH --output_path $DISTORTED_FOLDER/sparse --TrackEstablishment.max_num_tracks 5000 &&
        colmap image_undistorter --image_path $IMAGE_PATH --input_path $DISTORTED_FOLDER/sparse/0 --output_path $BASE_FOLDER --output_type COLMAP
        """
        
        subprocess.run(command, shell=True, check=True)
        cloud_logger.info("COLMAP and GLOMAP processing completed successfully")

        # Move files to their final locations
        cloud_logger.info(f"Moving files to their final locations in {OUTPUT_FOLDER_PATH}")
        sparse_zero_folder = os.path.join(OUTPUT_FOLDER_PATH, "sparse", "0")
        sparse_folder = os.path.join(OUTPUT_FOLDER_PATH, "sparse")
        os.makedirs(sparse_zero_folder, exist_ok=True)
        
        for file_name in ['cameras.bin', 'images.bin', 'points3D.bin']:
            source_file = os.path.join(sparse_folder, file_name)
            dest_file = os.path.join(sparse_zero_folder, file_name)
            if os.path.exists(source_file):
                shutil.move(source_file, dest_file)
        
        # Clean up temporary files if not saving them
        if not save_temp_files and os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
        
        cloud_logger.info("Processing completed")
        return "Processing completed"
        
    except Exception as e:
        cloud_logger.error(f"Error during processing: {str(e)}")
        # Clean up temp dir on error if not saving
        if not save_temp_files and os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
        raise