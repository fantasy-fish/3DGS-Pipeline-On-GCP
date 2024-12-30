gcloud functions deploy http-trigger \
    --gen2 \
    --runtime=python312 \
    --region=us-central1 \
    --source=. \
    --entry-point=trigger_reconstruction \
    --trigger-http \
    --allow-unauthenticated

# gcloud firestore databases create --location=us-central1

curl -X POST https://us-central1-threed-reconstruction-431616.cloudfunctions.net/http-trigger \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $(gcloud auth print-identity-token)" \
    -d '{
        "session_id": "abcd-efgh-1234567"
    }'

