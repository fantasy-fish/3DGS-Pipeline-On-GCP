docker build -t meshroom-base-image meshroom_base

docker build -t run-meshroom-image .

docker run -p 8080:8080 --gpus all -v /home/zhangwenniu/disk-2dgs-added/github/docker_test/meshroom_test/input:/input -v /home/zhangwenniu/disk-2dgs-added/github/docker_test/meshroom_test/output:/output run-meshroom-image:latest

curl -X POST http://localhost:8080/extract-mesh \
  -d '{
    "callback_token": "def",
    "input": {
      "bucket": "once3d-upload",
      "name": "test9.mp4",
      "generation": "123sdsa"
    }
  }'

curl -X POST http://localhost:8080/extract-mesh \
  -d '{
    "callback_token": "def",
    "input": {
      "bucket": "once3d-upload",
      "name": "test8.mp4",
      "generation": "12345"
    }
  }'