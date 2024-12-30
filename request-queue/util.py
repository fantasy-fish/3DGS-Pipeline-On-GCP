from google.cloud import logging as cloud_logging
import logging
import redis
import os

def setup_google_cloud_logging():
    """Set up Google Cloud Logging"""
    client = cloud_logging.Client()
    cloud_handler = client.get_default_handler()
    cloud_logger = logging.getLogger("cloudLogger")
    cloud_logger.setLevel(logging.DEBUG)
    cloud_logger.addHandler(cloud_handler)

    # Add console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    cloud_logger.addHandler(console_handler)

    return client, cloud_logger

def get_redis_client():
    """Get Redis client instance"""
    redis_host = os.getenv('REDIS_HOST', 'localhost')
    redis_port = int(os.getenv('REDIS_PORT', 6379))
    redis_password = os.getenv('REDIS_PASSWORD', None)
    
    return redis.Redis(
        host=redis_host,
        port=redis_port,
        password=redis_password,
        decode_responses=False  # Keep raw bytes for compatibility
    ) 