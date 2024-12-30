#!/bin/bash

# Create Redis instance in Cloud Memorystore
gcloud redis instances create request-queue-redis \
    --size=1 \
    --region=us-central1 \
    --redis-version=redis_6_x \
    --network=default

# Get Redis instance IP
REDIS_HOST=$(gcloud redis instances describe request-queue-redis \
    --region=us-central1 \
    --format='get(host)')

# Create the Pub/Sub topic for reconstruction requests
gcloud pubsub topics create reconstruction-requests \
    --project=threed-reconstruction-431616

# Deploy the request-queue service
gcloud run deploy request-queue \
    --source . \
    --region us-central1 \
    --platform managed \
    --allow-unauthenticated \
    --memory 1Gi \
    --cpu 1 \
    --min-instances 1 \
    --max-instances 10 \
    --service-account=916160520859-compute@developer.gserviceaccount.com \
    --set-env-vars="REDIS_HOST=${REDIS_HOST},REDIS_PORT=6379"

# Grant necessary permissions
gcloud projects add-iam-policy-binding threed-reconstruction-431616 \
    --member=serviceAccount:916160520859-compute@developer.gserviceaccount.com \
    --role=roles/pubsub.publisher

gcloud projects add-iam-policy-binding threed-reconstruction-431616 \
    --member=serviceAccount:916160520859-compute@developer.gserviceaccount.com \
    --role=roles/pubsub.subscriber 