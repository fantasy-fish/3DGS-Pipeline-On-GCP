# Deploy the 3DGS pipeline
gcloud workflows deploy threed-reconstrunction-workflow-new \
    --source=workflow-new.yaml \
    --location=us-central1

# Deploy the Meshroom pipeline
gcloud workflows deploy threed-reconstrunction-workflow \
    --source=workflow.yaml \
    --location=us-central1

gcloud eventarc triggers update video-upload-trigger-new \
  --location=asia-northeast1 \
  --destination-workflow=threed-reconstrunction-workflow-new \
  --destination-workflow-location=us-central1 \
  --event-filters="type=google.cloud.storage.object.v1.finalized" \
  --event-filters="bucket=once3d-upload" \
  --service-account=916160520859-compute@developer.gserviceaccount.com

# Upload an object to trigger the workflow
curl -X POST --data-binary @/home/shyay1013/input/test9.mp4 \
  -H "Content-Type: video/mp4" \
  -H "Authorization: Bearer $(gcloud auth print-access-token)" \
  "https://storage.googleapis.com/upload/storage/v1/b/once3d-upload/o?uploadType=media&name=test9.mp4"


# Deploy the whole workflow triggered by pub/sub messages
gcloud eventarc triggers create http-trigger \
  --location=us-central1 \
  --service-account=916160520859-compute@developer.gserviceaccount.com \
  --transport-topic=projects/threed-reconstruction-431616/topics/http-trigger-topic \
  --destination-workflow=threed-reconstruction-workflow-whole \
  --destination-workflow-location=us-central1 \
  --event-filters="type=google.cloud.pubsub.topic.v1.messagePublished"


gcloud workflows deploy threed-reconstruction-workflow-whole \
  --source=workflow-whole.yaml \
  --location=us-central1

# Triggered by HTTP requests
curl -X POST https://us-central1-threed-reconstruction-431616.cloudfunctions.net/http-trigger \
    -H "Authorization: Bearer $(gcloud auth print-identity-token)" \
    -H "Content-Type: application/json" \
    -d '{
        "session_id": "test9"
    }'