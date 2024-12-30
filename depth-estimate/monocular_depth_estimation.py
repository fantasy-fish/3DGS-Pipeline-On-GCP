import os
import time
import cv2
import torch
import sys
import matplotlib
import numpy as np

def mkdir(path, logger):
    """创建目录并记录日志"""
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)
        logger.info(f'创建目录 {path}')
    else:
        logger.info(f'{path} 已存在')

def convert_image_to_depth(model, logger, img_dir, depth_dir):
    """将图像转换为深度图"""
    assert os.path.exists(img_dir), f"图像文件夹 {img_dir} 应该存在"
    mkdir(depth_dir, logger)
    for image_name in sorted(os.listdir(img_dir)):
        image_path = os.path.join(img_dir, image_name)
        logger.info(f'推断深度图 {image_path}')
        image = cv2.imread(image_path)
        depth = model.infer_image(image)
        depth = (depth - depth.min()) / (depth.max() - depth.min()) * 255.0
        depth = depth.astype(np.uint8)
        
        depth = np.repeat(depth[..., np.newaxis], 3, axis=-1)
        depth_path = os.path.join(depth_dir, image_name.split('.')[0] + '.png')
        cv2.imwrite(depth_path, depth)

def monocular_depth_estimation(logger, img_dir, depth_dir, depth_anything_v2_base_path):
    """深度图生成函数"""
    start = time.time()

    logger.info(f'正在使用depth-anything-v2估计单目深度图')

    sys.path.append(depth_anything_v2_base_path)
    from depth_anything_v2.dpt import DepthAnythingV2

    DEVICE = 'cuda' if torch.cuda.is_available() else 'mps' if torch.backends.mps.is_available() else 'cpu'

    model_configs = {
        'vits': {'encoder': 'vits', 'features': 64, 'out_channels': [48, 96, 192, 384]},
        'vitb': {'encoder': 'vitb', 'features': 128, 'out_channels': [96, 192, 384, 768]},
        'vitl': {'encoder': 'vitl', 'features': 256, 'out_channels': [256, 512, 1024, 1024]},
        'vitg': {'encoder': 'vitg', 'features': 384, 'out_channels': [1536, 1536, 1536, 1536]}
    }

    encoder = 'vitl'  # or 'vits', 'vitb', 'vitg'

    model = DepthAnythingV2(**model_configs[encoder])
    model.load_state_dict(torch.load(os.path.join(depth_anything_v2_base_path, f'checkpoints/depth_anything_v2_{encoder}.pth'), map_location='cpu'))
    model = model.to(DEVICE).eval()
    convert_image_to_depth(model, logger, img_dir, depth_dir)
    end = time.time()
    logger.info(f'monocular_depth_estimation.py.monocular_depth_estimation 转换图像为深度图耗时 {end - start} 秒')