from datetime import datetime
from typing import Optional, Dict
from pydantic import BaseModel

class User(BaseModel):
    id: int
    email: str
    full_name: str
    created_at: datetime
    is_active: bool = True

class AuditLog(BaseModel):
    id: int
    timestamp: str
    user_id: Optional[int]
    action: str
    resource_type: str
    resource_id: Optional[str]
    description: Optional[str]
    changes: Optional[Dict]
    ip_address: Optional[str]
    status: str

class Report(BaseModel):
    id: int
    title: str
    content: str
    created_at: datetime
    updated_at: datetime
    user_id: int
    status: str
    metadata: Optional[Dict]

class Log(BaseModel):
    id: int
    timestamp: datetime
    level: str
    module: str
    message: str
    stack_trace: Optional[str]
    request_id: Optional[str]
    additional_data: Optional[Dict]

# List of all models for easy access
__all__ = [
    'User',
    'AuditLog',
    'Report',
    'Log'
]
