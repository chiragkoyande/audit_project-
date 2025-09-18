from datetime import datetime
from . import db

class Log(db.Model):
    """Model for storing system logs, errors, and technical events."""
    
    __tablename__ = 'system_logs'

    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    level = db.Column(db.String(20), nullable=False)  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    module = db.Column(db.String(100), nullable=False)  # Module/component that generated the log
    message = db.Column(db.Text, nullable=False)
    stack_trace = db.Column(db.Text, nullable=True)
    request_id = db.Column(db.String(50), nullable=True)  # For tracking related log entries
    additional_data = db.Column(db.JSON, nullable=True)  # For any extra contextual information

    def __init__(self, level, module, message, stack_trace=None, 
                 request_id=None, additional_data=None):
        self.level = level.upper()
        self.module = module
        self.message = message
        self.stack_trace = stack_trace
        self.request_id = request_id
        self.additional_data = additional_data

    def __repr__(self):
        return f'<Log {self.level} {self.module}: {self.message[:50]}...>'

    @classmethod
    def log(cls, level, module, message, stack_trace=None, 
            request_id=None, additional_data=None):
        """
        Create and save a new log entry.
        
        Args:
            level (str): Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            module (str): Name of the module/component generating the log
            message (str): Log message
            stack_trace (str, optional): Stack trace for errors
            request_id (str, optional): Request ID for tracking related logs
            additional_data (dict, optional): Any additional contextual data
        
        Returns:
            Log: The created log entry
        """
        log_entry = cls(
            level=level,
            module=module,
            message=message,
            stack_trace=stack_trace,
            request_id=request_id,
            additional_data=additional_data
        )
        db.session.add(log_entry)
        db.session.commit()
        return log_entry

    @classmethod
    def debug(cls, module, message, **kwargs):
        """Convenience method for debug level logs."""
        return cls.log('DEBUG', module, message, **kwargs)

    @classmethod
    def info(cls, module, message, **kwargs):
        """Convenience method for info level logs."""
        return cls.log('INFO', module, message, **kwargs)

    @classmethod
    def warning(cls, module, message, **kwargs):
        """Convenience method for warning level logs."""
        return cls.log('WARNING', module, message, **kwargs)

    @classmethod
    def error(cls, module, message, stack_trace=None, **kwargs):
        """Convenience method for error level logs."""
        return cls.log('ERROR', module, message, stack_trace=stack_trace, **kwargs)

    @classmethod
    def critical(cls, module, message, stack_trace=None, **kwargs):
        """Convenience method for critical level logs."""
        return cls.log('CRITICAL', module, message, stack_trace=stack_trace, **kwargs)

    def to_dict(self):
        """Convert the log entry to a dictionary."""
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat(),
            'level': self.level,
            'module': self.module,
            'message': self.message,
            'stack_trace': self.stack_trace,
            'request_id': self.request_id,
            'additional_data': self.additional_data
        }

    @classmethod
    def get_logs_by_level(cls, level, limit=100):
        """Retrieve logs by level."""
        return cls.query.filter_by(level=level.upper())\
                   .order_by(cls.timestamp.desc())\
                   .limit(limit).all()

    @classmethod
    def get_logs_by_module(cls, module, limit=100):
        """Retrieve logs by module."""
        return cls.query.filter_by(module=module)\
                   .order_by(cls.timestamp.desc())\
                   .limit(limit).all()

    @classmethod
    def get_logs_by_request(cls, request_id):
        """Retrieve all logs associated with a specific request."""
        return cls.query.filter_by(request_id=request_id)\
                   .order_by(cls.timestamp.asc()).all()
