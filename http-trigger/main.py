import functions_framework
from google.cloud import pubsub_v1, firestore
import json
import uuid
from datetime import datetime, timedelta

PROJECT_ID = "threed-reconstruction-431616"
TOPIC_ID = "http-trigger-topic"
DATABASE_ID = "once3d-db"

publisher = pubsub_v1.PublisherClient()
topic_path = publisher.topic_path(PROJECT_ID, TOPIC_ID)
db = firestore.Client(project=PROJECT_ID, database=DATABASE_ID)

RATE_LIMIT = 10  # requests per minute
RATE_LIMIT_WINDOW = 60  # seconds

@functions_framework.http
def trigger_reconstruction(request):
    if request.method != 'POST':    
        return 'Send a POST request', 405
    
    content = request.get_json(silent=True)
    if not content:
        return 'No JSON data provided', 400

    request_id = content['session_id']

    # Check rate limit
    if is_rate_limited():
        return 'Rate limit exceeded', 429

    # Check for duplication
    if is_duplicate(request_id):
        return 'Duplicate request', 409

    data = json.dumps(content).encode('utf-8')
    future = publisher.publish(
        topic_path,
        data,
        request_id=request_id  # Add this line to include request_id as an attribute
    )
    
    try:
        future.result()
    except Exception as e:
        return f'An error occurred: {e}', 500

    return f'Reconstruction triggered. Request ID: {request_id}', 200

def is_rate_limited():
    rate_ref = db.collection('rate_limits').document('global')
    
    now = datetime.utcnow()
    window_start = now - timedelta(seconds=RATE_LIMIT_WINDOW)
    
    rate_doc = rate_ref.get()
    if not rate_doc.exists:
        rate_ref.set({'count': 1, 'window_start': now})
        return False
    
    data = rate_doc.to_dict()
    stored_window_start = data['window_start']
    
    # Convert stored_window_start to offset-naive datetime if it's offset-aware
    if stored_window_start.tzinfo is not None:
        stored_window_start = stored_window_start.replace(tzinfo=None)
    
    if stored_window_start < window_start:
        rate_ref.set({'count': 1, 'window_start': now})
        return False
    
    if data['count'] >= RATE_LIMIT:
        return True
    
    rate_ref.update({'count': firestore.Increment(1)})
    return False

def is_duplicate(request_id):
    doc_ref = db.collection('processed_requests').document(request_id)
    doc = doc_ref.get()
    
    if doc.exists:
        return True
    
    doc_ref.set({'timestamp': datetime.utcnow()})
    return False