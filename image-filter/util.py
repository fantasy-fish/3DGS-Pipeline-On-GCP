import os
import glob
import shutil
import subprocess
import cv2
from google.cloud import logging as cloud_logging
import logging
import tempfile
import concurrent.futures

def setup_google_cloud_logging():
    # Initialize Google Cloud Logging client
    client = cloud_logging.Client()

    # Get the default handler and configure it to use Google Cloud Logging
    cloud_handler = client.get_default_handler()
    cloud_logger = logging.getLogger("cloudLogger")
    cloud_logger.setLevel(logging.DEBUG)
    cloud_logger.addHandler(cloud_handler)

    return client, cloud_logger

def process_image(cloud_logger, INPUT_FOLDER_PATH, OUTPUT_FOLDER_PATH):
    target_count = 300

    input_path = os.path.join(INPUT_FOLDER_PATH, "captured_image")
    
    # Create a temporary directory for extracted frames or scaled images
    with tempfile.TemporaryDirectory() as temp_dir:
        if not os.path.exists(input_path):
            video_folder_path = os.path.join(INPUT_FOLDER_PATH, "captured_video")
            # Find all video files
            video_files = glob.glob(os.path.join(video_folder_path, "*.mp4"))
            assert len(video_files) == 1, f"Expected exactly one video file, found {len(video_files)}"
            video_path = video_files[0]
            cloud_logger.info(f"No images found, using video at {video_path}")
            extract_frames(video_path, temp_dir)  # Use temp_dir for extracted frames
            input_path = temp_dir  # Update input_path to point to temp_dir
        else:
            # Handle image input - scale existing images
            cloud_logger.info("Scaling existing images to 1024px on long edge")
            scale_images_ffmpeg(cloud_logger, input_path, temp_dir)  # Use temp_dir for scaled images
            input_path = temp_dir  # Update input_path to point to temp_dir

        # Count initial number of images
        initial_image_count = len(glob.glob(os.path.join(input_path, "*.png")))
        cloud_logger.info(f"Initial image count: {initial_image_count}")
        
        # If less than or equal to {target_count} images, copy directly to output
        if initial_image_count <= target_count:
            cloud_logger.info(f"Less than or equal to {target_count} images, copying directly to output")
            shutil.copytree(input_path, OUTPUT_FOLDER_PATH, dirs_exist_ok=True)
            return "Processing completed - direct copy"

        cloud_logger.info(f"Starting image processing for {input_path}")
        
        # Get the directory of the current script
        current_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Path to the 01_filter_raw_data.py script
        filter_script = os.path.join(current_dir, "nerf_dataset_preprocessing_helper", "01_filter_raw_data.py")
        
        # Single filter command
        filter_command = f"""
        python3 {filter_script} \
            --input_path {input_path} \
            --output_path {OUTPUT_FOLDER_PATH} \
            --target_count {target_count} \
            --scalar 1 \
            --yes
        """
        
        cloud_logger.info(f"Start filtering to retain {target_count} images")
        try:
            subprocess.run(filter_command, shell=True, check=True)
            cloud_logger.info(f"Finish filtering to retain {target_count} images")
        except subprocess.CalledProcessError as e:
            cloud_logger.error(f"Error during filtering: {str(e)}")
            raise

        cloud_logger.info(f"Filtered images saved to {OUTPUT_FOLDER_PATH}")
        return "Processing completed"

def extract_frames(input_vid, output_path):
    if not os.path.exists(output_path):
        os.makedirs(output_path)
    cmd = [
        'ffmpeg',
        '-i', input_vid,
        '-v', 'quiet',
        '-vf', "fps=3,scale='min(1024,iw)':min'(1024,ih)':force_original_aspect_ratio=decrease",
        '-pix_fmt', 'rgb24',
        os.path.join(output_path, '%04d.png')
    ]
    subprocess.run(cmd)

def scale_image(img_path, output_path):
    cmd = [
        'ffmpeg',
        '-i', img_path,
        '-v', 'quiet',
        '-vf', "scale='min(1024,iw)':min'(1024,ih)':force_original_aspect_ratio=decrease",
        '-y',  # Overwrite output files without asking
        os.path.join(output_path, os.path.basename(img_path))  # Save to temp_dir
    ]
    subprocess.run(cmd, check=True)

def scale_images_ffmpeg(cloud_logger, input_path, output_path):
    image_paths = glob.glob(os.path.join(input_path, "*"))
    
    # Use ThreadPoolExecutor or ProcessPoolExecutor for parallel processing
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = {executor.submit(scale_image, img_path, output_path): img_path for img_path in image_paths}
        
        for future in concurrent.futures.as_completed(futures):
            img_path = futures[future]
            try:
                future.result()  # This will raise an exception if the subprocess failed
                cloud_logger.info(f"Successfully processed {img_path}")
            except Exception as e:
                cloud_logger.error(f"Error processing {img_path}: {e}")