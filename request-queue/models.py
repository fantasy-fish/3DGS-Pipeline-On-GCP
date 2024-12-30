from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ProcessingRequest(BaseModel):
    session_id: str
    callback_token: str
    priority: Optional[int] = 0

class QueueStatus(BaseModel):
    total_requests: int
    queued_requests: int
    processing_requests: int
    completed_requests: int
    failed_requests: int

class RequestStatus(BaseModel):
    status: str
    created_at: str
    updated_at: Optional[str] = None
    session_id: str
    callback_token: str
    priority: Optional[int] = 0 