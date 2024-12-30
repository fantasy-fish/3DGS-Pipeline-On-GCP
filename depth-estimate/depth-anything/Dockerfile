FROM nvcr.io/nvidia/pytorch:22.06-py3

# Prevent interactive prompts during package installation
# ENV DEBIAN_FRONTEND=noninteractive

# 设置工作目录
WORKDIR /app

# 安装 git 和 wget
RUN apt-get update && apt-get install -y git wget && rm -rf /var/lib/apt/lists/*

# 克隆 Depth-Anything-V2 仓库
RUN git clone https://github.com/DepthAnything/Depth-Anything-V2.git

# 进入仓库目录
WORKDIR /app/Depth-Anything-V2

# 安装项目依赖
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install matplotlib numpy
# 下载模型权重文件
RUN mkdir checkpoints && \
    wget -O checkpoints/depth_anything_v2_vits.pth https://huggingface.co/depth-anything/Depth-Anything-V2-Small/resolve/main/depth_anything_v2_vits.pth && \
    wget -O checkpoints/depth_anything_v2_vitb.pth https://huggingface.co/depth-anything/Depth-Anything-V2-Base/resolve/main/depth_anything_v2_vitb.pth && \
    wget -O checkpoints/depth_anything_v2_vitl.pth https://huggingface.co/depth-anything/Depth-Anything-V2-Large/resolve/main/depth_anything_v2_vitl.pth

# 设置环境变量
ENV PYTHONUNBUFFERED=1