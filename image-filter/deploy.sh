# Option 2: Build locally and push to container registry
docker build -t image-filter-image .
docker tag image-filter-image us-central1-docker.pkg.dev/threed-reconstruction-431616/gs-pipeline/image-filter-image:latest
# gcloud artifacts repositories create gs-pipeline \
#     --repository-format=docker \
#     --location=us-central1 \
#     --description="Repository for gs-pipeline"

# gcloud artifacts docker images delete us-central1-docker.pkg.dev/threed-reconstruction-431616/gs-pipeline/image-filter-image:latest
docker push us-central1-docker.pkg.dev/threed-reconstruction-431616/gs-pipeline/image-filter-image:latest

# Build the cloud run service
gcloud beta run deploy image-filter \
  --image us-central1-docker.pkg.dev/threed-reconstruction-431616/gs-pipeline/image-filter-image \
  --project threed-reconstruction-431616 \
  --platform managed \
  --region us-central1 \
  --port 8080 \
  --cpu 8 \
  --memory 32Gi \
  --no-cpu-throttling \
  --allow-unauthenticated \
  --service-account=916160520859-compute@developer.gserviceaccount.com \
  --timeout=300s \
  --min-instances=0

# Mount the volumes
gcloud beta run services update image-filter \
  --add-volume name=once3d-input-volume,type=cloud-storage,bucket=once3d-upload \
  --add-volume-mount volume=once3d-input-volume,mount-path=/input \
  --region us-central1

gcloud beta run services update image-filter \
  --add-volume name=once3d-output-volume,type=cloud-storage,bucket=once3d-output \
  --add-volume-mount volume=once3d-output-volume,mount-path=/output \
  --region us-central1

# Use the latest image
gcloud beta run services update image-filter \
  --image us-central1-docker.pkg.dev/threed-reconstruction-431616/gs-pipeline/image-filter-image \
  --region us-central1

# Test with the curl command
curl -X POST https://image-filter-916160520859.us-central1.run.app/filter-image \
  -d '{
    "callback_token": "abcd",
    "request_id": "C0072_images"
  }'