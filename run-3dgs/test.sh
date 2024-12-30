docker build -t run-3dgs-image .

docker run -it -p 8080:8080 --gpus all -v /home/shyay1013/input:/input -v /home/shyay1013/input:/output run-3dgs-image

curl -X POST http://localhost:8080/run-3dgs \
  -d '{ "bucket": "once3d-upload", "name": "test9.mp4", "generation": "123", "callback_token": "abc" }'


docker run -it -p 8080:8080 \
  --gpus all -v /home/shyay1013/input:/input \
  -v /home/shyay1013/once3d-output:/output \
  run-3dgs-image:latest \
  /bin/bash

rm -rf /input/test9_123/output
python /workspace/gaussian-splatting/train.py \
  -s /output/test9 \
  -d /output/test9/depth \
  -m /output/test9/3dgs


curl -X POST https://run-3dgs-916160520859.us-central1.run.app/run-3dgs \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer $(gcloud auth print-access-token)" \
     -d '{
           "callback_token": "abcd-efg-hijk",
           "request_id": "test9"
         }'