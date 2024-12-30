import os
import subprocess
import cv2
from google.cloud import logging as cloud_logging
import logging
import tempfile
import shutil
import asyncio
from utils.train_meshroom import set_env_variables, run_meshroom_pipeline


def setup_google_cloud_logging():
    # Initialize Google Cloud Logging client
    client = cloud_logging.Client()

    # Get the default handler and configure it to use Google Cloud Logging
    cloud_handler = client.get_default_handler()
    cloud_logger = logging.getLogger("cloudLogger")
    cloud_logger.setLevel(logging.INFO)
    cloud_logger.addHandler(cloud_handler)

    return client, cloud_logger



def extract_mesh(cloud_logger, INPUT_FILE_PATH, OUTPUT_FOLDER_PATH, save_temp_files=True):
    """
    提取Meshroom的3D网格。

    这个函数使用Meshroom工具从输入视频中提取3D网格，并将其保存到输出文件夹中。

    参数:
    - cloud_logger (logging.Logger): 用于记录日志的Logger对象。
    - INPUT_FILE_PATH (str): 输入视频文件的路径。
    - OUTPUT_FOLDER_PATH (str): 输出文件夹的路径，用于保存提取的3D网格。
    - save_temp_files (bool): 是否保存临时文件，默认为True。
    """
    
    # 设置环境变量
    set_env_variables(
        alicevision_install="./Meshroom-2023.3.0/aliceVision"
    )
    image_folder_path = os.path.join(OUTPUT_FOLDER_PATH, "images")
    colmap_input_path = os.path.join(OUTPUT_FOLDER_PATH, "sparse", "0")
    
    if save_temp_files:
        temp_dir = os.path.join(OUTPUT_FOLDER_PATH, "temp")
        os.makedirs(temp_dir, exist_ok=True)
    else:
        temp_dir = tempfile.TemporaryDirectory()
            
    cloud_logger.info(f"Starting mesh extraction for {INPUT_FILE_PATH}")
        
    meshroom_cache_path = os.path.join(temp_dir, "cache")
    meshroom_output_path = os.path.join(temp_dir, "output")
    os.makedirs(meshroom_cache_path, exist_ok=True)
    os.makedirs(meshroom_output_path, exist_ok=True)
    cloud_logger.info(f"Created meshroom cache directory: {meshroom_cache_path} and meshroom output directory: {meshroom_output_path}")
    try:
        cloud_logger.info("Starting meshroom pipeline")
        run_meshroom_pipeline(
            colmap_input_path=colmap_input_path, 
            image_folder_path=image_folder_path, 
            meshroom_cache_path=meshroom_cache_path, 
            meshroom_output_path=meshroom_output_path,
            logger=cloud_logger
        )
        cloud_logger.info(f"Meshroom pipeline completed")
        
        # Copy or move the results from output_path to publish_folder_path
        publish_folder_path = os.path.join(OUTPUT_FOLDER_PATH, "mesh")
        os.makedirs(publish_folder_path, exist_ok=True)
        for item in os.listdir(meshroom_output_path):
            s = os.path.join(meshroom_output_path, item)
            d = os.path.join(publish_folder_path, item)
            if os.path.isdir(s):
                shutil.copytree(s, d, dirs_exist_ok=True)
            else:
                shutil.copy2(s, d)
        cloud_logger.info("Mesh copied to the output bucket")
        
    except Exception as e:
        cloud_logger.error(f"Error during meshroom pipeline: {str(e)}")
        raise

    cloud_logger.info("Mesh extraction completed")
    return "Processing completed"