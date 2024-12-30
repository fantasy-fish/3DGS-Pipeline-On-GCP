#!/bin/bash

# # Build the Docker image
# docker build -t glomap-preprocess-image .

# # Run the Docker container
# docker run -it -p 8080:8080 --gpus all \
#     -v ~/input:/input \
#     -v ~/output:/output \
#     glomap-preprocess-image


# PROJECT_NUMBER=$(gcloud projects describe threed-reconstruction-431616 --format="value(projectNumber)")
# echo $PROJECT_NUMBER

# Step 1: Build and push the glomap preprocessor image
# Option 1: Build in the cloud
# Grant the Artifact Registry Admin role
gcloud projects add-iam-policy-binding threed-reconstruction-431616 \
    --member=serviceAccount:916160520859-compute@developer.gserviceaccount.com \
    --role=roles/artifactregistry.admin

gcloud builds submit --config cloudbuild.yaml .

# Option 2: Build locally and push to container registry
docker build -t glomap-preprocess-image .
docker tag glomap-preprocess-image us-central1-docker.pkg.dev/threed-reconstruction-431616/gs-pipeline/glomap-preprocess-image:latest
# gcloud artifacts repositories create gs-pipeline \
#     --repository-format=docker \
#     --location=us-central1 \
#     --description="Repository for gs-pipeline"

# gcloud artifacts docker images delete us-central1-docker.pkg.dev/threed-reconstruction-431616/gs-pipeline/glomap-preprocess-image:latest
docker push us-central1-docker.pkg.dev/threed-reconstruction-431616/gs-pipeline/glomap-preprocess-image:latest

# Update the cloud run service
gcloud beta run deploy  glomap-preprocess \
  --image us-central1-docker.pkg.dev/threed-reconstruction-431616/gs-pipeline/glomap-preprocess-image:latest \
  --region us-central1

gcloud run services update-traffic glomap-preprocess --to-latest --region us-central1
# Step 2: Deploy the glomap preprocessor service
# Grant Storage Admin role
gcloud projects add-iam-policy-binding threed-reconstruction-431616 \
  --member=serviceAccount:916160520859-compute@developer.gserviceaccount.com \
  --role=roles/storage.admin

# Grant Logs Writer role
gcloud projects add-iam-policy-binding threed-reconstruction-431616 \
    --member=serviceAccount:916160520859-compute@developer.gserviceaccount.com \
    --role=roles/logging.admin

gcloud beta run deploy  glomap-preprocess \
  --image us-central1-docker.pkg.dev/threed-reconstruction-431616/gs-pipeline/glomap-preprocess-image \
  --project threed-reconstruction-431616 \
  --platform managed \
  --region us-central1 \
  --port 8080 \
  --cpu 8 \
  --memory 32Gi \
  --no-cpu-throttling \
  --no-allow-unauthenticated \
  --service-account=916160520859-compute@developer.gserviceaccount.com \
  --timeout=300s \
  --min-instances=0 \
  --max-instances=7

# Add the volume to the service
gcloud beta run services update  glomap-preprocess \
  --add-volume name=once3d-input-volume,type=cloud-storage,bucket=once3d-upload \
  --add-volume-mount volume=once3d-input-volume,mount-path=/input

gcloud beta run services update  glomap-preprocess \
  --add-volume name=once3d-output-volume,type=cloud-storage,bucket=once3d-output \
  --add-volume-mount volume=once3d-output-volume,mount-path=/output


# Step 3: Create an Eventarc trigger for the  glomap preprocess service 

# Grant Run Invoker role
gcloud run services add-iam-policy-binding glomap-preprocess \
  --member=serviceAccount:916160520859-compute@developer.gserviceaccount.com \
  --role="roles/run.invoker" \
  --region=us-central1

# Grant Eventarc EventReceiver role
gcloud projects add-iam-policy-binding threed-reconstruction-431616 \
  --member="serviceAccount:916160520859-compute@developer.gserviceaccount.com" \
  --role="roles/eventarc.eventReceiver"

# Grant permissions to the Cloud Storage service account
gcloud projects add-iam-policy-binding threed-reconstruction-431616 \
  --member="serviceAccount:service-916160520859@gs-project-accounts.iam.gserviceaccount.com" \
  --role="roles/pubsub.publisher"

# Grant permissions to the Compute Engine default service account
gcloud projects add-iam-policy-binding threed-reconstruction-431616 \
  --member="serviceAccount:916160520859-compute@developer.gserviceaccount.com" \
  --role="roles/pubsub.publisher"

# Grant permissions to the Eventarc service account
gcloud projects add-iam-policy-binding threed-reconstruction-431616 \
  --member="serviceAccount:service-916160520859@gcp-sa-eventarc.iam.gserviceaccount.com" \
  --role="roles/eventarc.eventReceiver"

# Grant permissions to the Cloud Run service account
gcloud projects add-iam-policy-binding threed-reconstruction-431616 \
  --member="serviceAccount:service-916160520859@serverless-robot-prod.iam.gserviceaccount.com" \
  --role="roles/run.invoker"

gcloud eventarc triggers create video-upload-trigger1 \
  --location=asia-northeast1 \
  --destination-run-service=glomap-preprocess \
  --destination-run-region=us-central1 \
  --event-filters="type=google.cloud.storage.object.v1.finalized" \
  --event-filters="bucket=once3d-upload" \
  --service-account=916160520859-compute@developer.gserviceaccount.com \
  --destination-run-path="/preprocess-video"

# projects/threed-reconstruction-431616/topics/eventarc-asia-northeast1-video-upload-trigger-076