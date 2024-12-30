# Use the provided Dockerfile as base
ARG UBUNTU_VERSION=22.04
ARG NVIDIA_CUDA_VERSION=12.2.0

FROM nvidia/cuda:${NVIDIA_CUDA_VERSION}-devel-ubuntu${UBUNTU_VERSION}

# Set up the application
WORKDIR /app

# Install Python and pip
RUN apt-get update && apt-get install -y python3 python3-pip wget
RUN wget https://github.com/alicevision/Meshroom/releases/download/v2023.3.0/Meshroom-2023.3.0-linux.tar.gz
RUN tar -xzf Meshroom-2023.3.0-linux.tar.gz -C /app
RUN rm Meshroom-2023.3.0-linux.tar.gz

