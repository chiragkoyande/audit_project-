from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

# Initialize SQLAlchemy instance
db = SQLAlchemy()

# Import all models
from .user import User
from .audit import AuditLog
from .report import Report
from .log import Log

# List of all models for easy access
__all__ = [
    'User',
    'AuditLog',
    'Report',
    'Log',
    'db'
]
