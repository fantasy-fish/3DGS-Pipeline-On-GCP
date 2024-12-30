echo "构建 depth-anything-v2 Docker 镜像..."
docker build -t depth-anything-v2 ./depth-anything

echo "depth-anything-v2 镜像构建完成。"

echo "构建 depth-estimate Docker 镜像..."
docker build -t depth-estimate .  
echo "depth-estimate 镜像构建完成。"


echo "运行 Docker 容器..."
docker run -p 8080:8080 \
 --gpus all \
 --shm-size 32G \
 -v /home/shyay1013/input:/input \
 -v /home/shyay1013/output:/output \
 depth-estimate


echo "发送 POST 请求到 preprocess-depth..."
curl -X POST http://localhost:8080/preprocess-depth \
  -d '{ "bucket": "once3d-upload", "name": "test7.mp4", "generation": "21345" }'

curl -X POST http://localhost:8080/preprocess-depth \
  -d '{ "bucket": "once3d-upload", "name": "test1.mp4", "generation": "12345" }'

echo "脚本执行完成。"
