# Build the image-filter-image
docker build -t image-filter-image .

# Run the container
docker run -p 8080:8080 \
  -v /home/shyay1013/input:/input \
  -v /home/shyay1013/output:/output \
  --user $(id -u):$(id -g) \
  image-filter-image
  
# Run the test curl command
rm -rf /home/shyay1013/output/C0072_images/source/
curl -X POST http://localhost:8080/filter-image \
  -d '{
    "callback_token": "abcd",
    "request_id": "C0072_images"
  }'

curl -X GET "http://localhost:8080/status" \
     -G \
     --data-urlencode "request_id=C0072_images" \
     --data-urlencode "callback_token=abcd"


