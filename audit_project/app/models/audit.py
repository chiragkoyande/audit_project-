from datetime import datetime
from . import db
from sqlalchemy.dialects.postgresql import JSONB
import os
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

class AuditLog(db.Model):
    """Model for storing audit logs of system activities and changes."""
    
    __tablename__ = 'audit_logs'

    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    action = db.Column(db.String(50), nullable=False)
    resource_type = db.Column(db.String(50), nullable=False)
    resource_id = db.Column(db.String(50), nullable=True)
    description = db.Column(db.Text, nullable=True)
    changes = db.Column(JSONB, nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)
    status = db.Column(db.String(20), nullable=False, default='success')

    # Relationships
    user = db.relationship('User', backref=db.backref('audit_logs', lazy='dynamic'))

    def __init__(self, action, resource_type, user_id=None, resource_id=None, 
                 description=None, changes=None, ip_address=None, status='success'):
        self.action = action
        self.resource_type = resource_type
        self.user_id = user_id
        self.resource_id = resource_id
        self.description = description
        self.changes = changes
        self.ip_address = ip_address
        self.status = status

    def __repr__(self):
        return f'<AuditLog {self.action} {self.resource_type}:{self.resource_id} by User:{self.user_id}>'

    @classmethod
    def log_event(cls, action, resource_type, user_id=None, resource_id=None, 
                  description=None, changes=None, ip_address=None, status='success'):
        """
        Create and save a new audit log entry.
        
        Args:
            action (str): The action performed (e.g., 'create', 'update', 'delete')
            resource_type (str): Type of resource being audited (e.g., 'user', 'report')
            user_id (int, optional): ID of the user performing the action
            resource_id (str, optional): ID of the resource being affected
            description (str, optional): Detailed description of the action
            changes (dict, optional): JSON-serializable dict of changes made
            ip_address (str, optional): IP address of the user
            status (str, optional): Status of the action ('success' or 'failure')
        
        Returns:
            AuditLog: The created audit log entry
        """
        log = cls(
            action=action,
            resource_type=resource_type,
            user_id=user_id,
            resource_id=resource_id,
            description=description,
            changes=changes,
            ip_address=ip_address,
            status=status
        )
        db.session.add(log)
        db.session.commit()
        return log

    def to_dict(self):
        """Convert the audit log entry to a dictionary."""
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat(),
            'user_id': self.user_id,
            'action': self.action,
            'resource_type': self.resource_type,
            'resource_id': self.resource_id,
            'description': self.description,
            'changes': self.changes,
            'ip_address': self.ip_address,
            'status': self.status
        }

def log_audit_event(
    action,
    resource_type,
    user_id=None,
    resource_id=None,
    description=None,
    changes=None,
    ip_address=None,
    status='success'
):
    """
    Create and save a new audit log entry in Supabase.

    Args:
        action (str): The action performed (e.g., 'create', 'update', 'delete')
        resource_type (str): Type of resource being audited (e.g., 'user', 'report')
        user_id (int, optional): ID of the user performing the action
        resource_id (str, optional): ID of the resource being affected
        description (str, optional): Detailed description of the action
        changes (dict, optional): JSON-serializable dict of changes made
        ip_address (str, optional): IP address of the user
        status (str, optional): Status of the action ('success' or 'failure')

    Returns:
        dict: The created audit log entry or error info
    """
    data = {
        "action": action,
        "resource_type": resource_type,
        "user_id": user_id,
        "resource_id": resource_id,
        "description": description,
        "changes": changes,
        "ip_address": ip_address,
        "status": status
    }
    result = supabase.table("audit_logs").insert(data).execute()
    return result.data if hasattr(result, "data") else result
