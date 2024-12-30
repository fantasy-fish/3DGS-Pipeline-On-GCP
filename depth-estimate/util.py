import os
from google.cloud import logging as cloud_logging
import logging
from monocular_depth_estimation import monocular_depth_estimation
from make_depth_scale import compute_depth_scales
import time

def setup_google_cloud_logging():
    # Initialize Google Cloud Logging client
    client = cloud_logging.Client()

    # Get the default handler and configure it to use Google Cloud Logging
    cloud_handler = client.get_default_handler()
    cloud_logger = logging.getLogger("cloudLogger")
    cloud_logger.setLevel(logging.DEBUG)
    cloud_logger.addHandler(cloud_handler)

    # Add a console handler to output logs to the console
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)  # Set level to DEBUG to capture all logs
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    cloud_logger.addHandler(console_handler)

    return client, cloud_logger

def depth_generation(cloud_logger, image_path, depth_path, depth_anything_v2_base_path):
    cloud_logger.info(f"Starting depth generation for {image_path}")
    
    start_time = time.time()
    monocular_depth_estimation(cloud_logger, image_path, depth_path, depth_anything_v2_base_path)
    end_time = time.time()
    cloud_logger.info(f"monocular_depth_estimation took {end_time - start_time:.2f} seconds")
    
    base_dir = os.path.dirname(depth_path)
    
    start_time = time.time()
    compute_depth_scales(base_dir, depth_path, 'bin')
    end_time = time.time()
    cloud_logger.info(f"compute_depth_scales took {end_time - start_time:.2f} seconds")
    cloud_logger.info("util.py.depth_generation Depth generation completed")
    return "Depth generation completed"