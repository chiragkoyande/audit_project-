"""
Services package for audit_project.

This package contains service layer implementations for business logic,
including AI services, compliance checks, and notification handling.
"""

# Import service classes for easy access
from .ai_service import AIService
from .compliance_service import ComplianceService
from .notification_service import NotificationService

# Define what gets imported with "from services import *"
__all__ = [
    "AIService",
    "ComplianceService",
    "NotificationService",
]

# Service configuration
SERVICE_CONFIG = {
    "ai_service": {
        "enabled": True,
        "timeout": 30,
        "max_retries": 3,
    },
    "compliance_service": {
        "enabled": True,
        "strict_mode": False,
        "cache_results": True,
    },
    "notification_service": {
        "enabled": True,
        "email_notifications": True,
        "slack_notifications": False,
    }
}

# Initialize services if needed
def get_ai_service():
    """Get configured AI service instance."""
    return AIService()

def get_compliance_service():
    """Get configured compliance service instance."""
    return ComplianceService()

def get_notification_service():
    """Get configured notification service instance."""
    return NotificationService()
