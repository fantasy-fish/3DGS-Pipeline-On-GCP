# Build the base image glomap
cd glomap
docker build -t glomap .

# Build the glomap-preprocess-image
cd ..
docker build -t glomap-preprocess-image .


# Run the container
docker run -p 8080:8080 --gpus all -v /home/shyay1013/input:/input -v /home/shyay1013/output:/output glomap-preprocess-image

# Run the test curl command
curl -X POST http://localhost:8080/preprocess-video \
  -d '{
    "bucket": "once3d-upload",
    "name": "test7.mp4",
    "generation": "12345"
  }'

curl -X POST http://localhost:8090/preprocess-video \
  -d '{
    "bucket": "once3d-upload",
    "name": "test1.mp4",
    "generation": "12345"
  }'