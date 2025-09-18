"""
Notification Service for audit project.

Handles various notification channels including email, SMS, Slack,
and in-app notifications for audit events and alerts.
"""

import logging
import json
import smtplib
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from enum import Enum
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Configure logging
logger = logging.getLogger(__name__)


class NotificationType(Enum):
    """Notification type enumeration."""
    AUDIT_ALERT = "audit_alert"
    COMPLIANCE_WARNING = "compliance_warning"
    SYSTEM_ERROR = "system_error"
    REPORT_READY = "report_ready"
    DEADLINE_REMINDER = "deadline_reminder"
    USER_ACTION_REQUIRED = "user_action_required"


class NotificationChannel(Enum):
    """Notification channel enumeration."""
    EMAIL = "email"
    SMS = "sms"
    SLACK = "slack"
    IN_APP = "in_app"
    WEBHOOK = "webhook"


class NotificationPriority(Enum):
    """Notification priority levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class NotificationServiceError(Exception):
    """Custom exception for notification service errors."""
    pass


class NotificationService:
    """
    Notification Service for multi-channel messaging.
    
    Supports email, SMS, Slack, and in-app notifications
    with priority-based delivery and retry logic.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize Notification Service.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or self._get_default_config()
        self.enabled_channels = self._get_enabled_channels()
        self.notification_queue = []
        self.sent_notifications = []
        
        logger.info(f"Notification Service initialized with channels: {list(self.enabled_channels)}")
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration for notification service."""
        return {
            'email': {
                'enabled': True,
                'smtp_server': 'localhost',
                'smtp_port': 587,
                'use_tls': True,
                'sender_email': 'audit@company.com',
                'sender_name': 'Audit System'
            },
            'sms': {
                'enabled': False,
                'provider': 'twilio',
                'sender_number': '+1234567890'
            },
            'slack': {
                'enabled': False,
                'webhook_url': None,
                'default_channel': '#audit-alerts'
            },
            'in_app': {
                'enabled': True,
                'retention_days': 30
            },
            'webhook': {
                'enabled': False,
                'endpoints': []
            },
            'retry': {
                'max_attempts': 3,
                'backoff_factor': 2,
                'initial_delay_seconds': 1
            }
        }
    
    def _get_enabled_channels(self) -> set:
        """Get set of enabled notification channels."""
        enabled = set()
        for channel, config in self.config.items():
            if isinstance(config, dict) and config.get('enabled', False):
                enabled.add(channel)
        return enabled
    
    def send_notification(self, notification: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send notification through specified channels.
        
        Args:
            notification: Notification data with channels, content, and recipients
            
        Returns:
            Notification delivery results
            
        Raises:
            NotificationServiceError: If notification sending fails
        """
        try:
            # Validate notification data
            self._validate_notification(notification)
            
            # Add metadata
            notification_id = f"notif_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
            notification['id'] = notification_id
            notification['created_at'] = datetime.now().isoformat()
            notification['status'] = 'pending'
            
            logger.info(f"Sending notification {notification_id} via channels: {notification.get('channels', [])}")
            
            # Send through each specified channel
            results = {}
            channels = notification.get('channels', [])
            
            for channel in channels:
                if channel not in self.enabled_channels:
                    logger.warning(f"Channel {channel} is not enabled, skipping")
                    results[channel] = {'status': 'disabled', 'message': 'Channel not enabled'}
                    continue
                
                try:
                    channel_result = self._send_via_channel(notification, channel)
                    results[channel] = channel_result
                except Exception as e:
                    logger.error(f"Failed to send via {channel}: {str(e)}")
                    results[channel] = {'status': 'failed', 'error': str(e)}
            
            # Update notification status
            notification['status'] = 'sent' if any(r.get('status') == 'success' for r in results.values()) else 'failed'
            notification['results'] = results
            notification['sent_at'] = datetime.now().isoformat()
            
            # Store notification record
            self.sent_notifications.append(notification)
            
            logger.info(f"Notification {notification_id} processed with status: {notification['status']}")
            return notification
            
        except Exception as e:
            logger.error(f"Notification sending failed: {str(e)}")
            raise NotificationServiceError(f"Failed to send notification: {str(e)}")
    
    def send_audit_alert(self, alert_data: Dict[str, Any], recipients: List[str], 
                        priority: str = NotificationPriority.HIGH.value) -> Dict[str, Any]:
        """
        Send audit-specific alert notification.
        
        Args:
            alert_data: Alert information
            recipients: List of recipient addresses/IDs
            priority: Alert priority level
            
        Returns:
            Notification delivery results
        """
        notification = {
            'type': NotificationType.AUDIT_ALERT.value,
            'priority': priority,
            'recipients': recipients,
            'channels': self._get_channels_for_priority(priority),
            'subject': f"Audit Alert: {alert_data.get('title', 'Unknown Alert')}",
            'content': self._format_audit_alert(alert_data),
            'data': alert_data
        }
        
        return self.send_notification(notification)
    
    def send_compliance_warning(self, compliance_data: Dict[str, Any], recipients: List[str]) -> Dict[str, Any]:
        """
        Send compliance warning notification.
        
        Args:
            compliance_data: Compliance check results
            recipients: List of recipient addresses/IDs
            
        Returns:
            Notification delivery results
        """
        notification = {
            'type': NotificationType.COMPLIANCE_WARNING.value,
            'priority': NotificationPriority.HIGH.value,
            'recipients': recipients,
            'channels': [NotificationChannel.EMAIL.value, NotificationChannel.IN_APP.value],
            'subject': 'Compliance Warning Detected',
            'content': self._format_compliance_warning(compliance_data),
            'data': compliance_data
        }
        
        return self.send_notification(notification)
    
    def send_report_ready_notification(self, report_info: Dict[str, Any], recipients: List[str]) -> Dict[str, Any]:
        """
        Send report ready notification.
        
        Args:
            report_info: Report information
            recipients: List of recipient addresses/IDs
            
        Returns:
            Notification delivery results
        """
        notification = {
            'type': NotificationType.REPORT_READY.value,
            'priority': NotificationPriority.MEDIUM.value,
            'recipients': recipients,
            'channels': [NotificationChannel.EMAIL.value, NotificationChannel.IN_APP.value],
            'subject': f"Report Ready: {report_info.get('report_name', 'Audit Report')}",
            'content': self._format_report_ready(report_info),
            'data': report_info
        }
        
        return self.send_notification(notification)
    
    def send_deadline_reminder(self, deadline_info: Dict[str, Any], recipients: List[str], 
                             days_until: int) -> Dict[str, Any]:
        """
        Send deadline reminder notification.
        
        Args:
            deadline_info: Deadline information
            recipients: List of recipient addresses/IDs
            days_until: Number of days until deadline
            
        Returns:
            Notification delivery results
        """
        priority = NotificationPriority.CRITICAL.value if days_until <= 1 else NotificationPriority.HIGH.value
        
        notification = {
            'type': NotificationType.DEADLINE_REMINDER.value,
            'priority': priority,
            'recipients': recipients,
            'channels': self._get_channels_for_priority(priority),
            'subject': f"Deadline Reminder: {days_until} days remaining",
            'content': self._format_deadline_reminder(deadline_info, days_until),
            'data': {**deadline_info, 'days_until': days_until}
        }
        
        return self.send_notification(notification)
    
    def _validate_notification(self, notification: Dict[str, Any]) -> None:
        """Validate notification data."""
        required_fields = ['recipients', 'subject', 'content']
        for field in required_fields:
            if field not in notification:
                raise NotificationServiceError(f"Missing required field: {field}")
        
        if not notification['recipients']:
            raise NotificationServiceError("Recipients list cannot be empty")
    
    def _send_via_channel(self, notification: Dict[str, Any], channel: str) -> Dict[str, Any]:
        """Send notification via specific channel."""
        channel_handlers = {
            NotificationChannel.EMAIL.value: self._send_email,
            NotificationChannel.SMS.value: self._send_sms,
            NotificationChannel.SLACK.value: self._send_slack,
            NotificationChannel.IN_APP.value: self._send_in_app,
            NotificationChannel.WEBHOOK.value: self._send_webhook
        }
        
        handler = channel_handlers.get(channel)
        if not handler:
            raise NotificationServiceError(f"Unsupported notification channel: {channel}")
        
        return handler(notification)
    
    def _send_email(self, notification: Dict[str, Any]) -> Dict[str, Any]:
        """Send email notification."""
        try:
            email_config = self.config.get('email', {})
            
            # TODO: Implement actual email sending
            # This is a placeholder implementation
            logger.info(f"Sending email to {len(notification['recipients'])} recipients")
            
            # Simulate email sending
            for recipient in notification['recipients']:
                logger.debug(f"Email sent to: {recipient}")
            
            return {
                'status': 'success',
                'sent_count': len(notification['recipients']),
                'sent_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Email sending failed: {str(e)}")
            return {'status': 'failed', 'error': str(e)}
    
    def _send_sms(self, notification: Dict[str, Any]) -> Dict[str, Any]:
        """Send SMS notification."""
        try:
            sms_config = self.config.get('sms', {})
            
            # TODO: Implement actual SMS sending (e.g., Twilio)
            logger.info(f"Sending SMS to {len(notification['recipients'])} recipients")
            
            return {
                'status': 'success',
                'sent_count': len(notification['recipients']),
                'sent_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"SMS sending failed: {str(e)}")
            return {'status': 'failed', 'error': str(e)}
    
    def _send_slack(self, notification: Dict[str, Any]) -> Dict[str, Any]:
        """Send Slack notification."""
        try:
            slack_config = self.config.get('slack', {})
            
            # TODO: Implement actual Slack webhook integration
            logger.info(f"Sending Slack notification to channel")
            
            return {
                'status': 'success',
                'channel': slack_config.get('default_channel'),
                'sent_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Slack sending failed: {str(e)}")
            return {'status': 'failed', 'error': str(e)}
    
    def _send_in_app(self, notification: Dict[str, Any]) -> Dict[str, Any]:
        """Send in-app notification."""
        try:
            # TODO: Store notification in database for in-app display
            logger.info(f"Creating in-app notifications for {len(notification['recipients'])} users")
            
            return {
                'status': 'success',
                'stored_count': len(notification['recipients']),
                'stored_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"In-app notification failed: {str(e)}")
            return {'status': 'failed', 'error': str(e)}
    
    def _send_webhook(self, notification: Dict[str, Any]) -> Dict[str, Any]:
        """Send webhook notification."""
        try:
            webhook_config = self.config.get('webhook', {})
            
            # TODO: Implement actual webhook posting
            logger.info(f"Sending webhook notifications to {len(webhook_config.get('endpoints', []))} endpoints")
            
            return {
                'status': 'success',
                'endpoints_notified': len(webhook_config.get('endpoints', [])),
                'sent_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Webhook sending failed: {str(e)}")
            return {'status': 'failed', 'error': str(e)}
    
    def _get_channels_for_priority(self, priority: str) -> List[str]:
        """Get appropriate channels based on priority level."""
        if priority == NotificationPriority.CRITICAL.value:
            return [NotificationChannel.EMAIL.value, NotificationChannel.SMS.value, 
                   NotificationChannel.SLACK.value, NotificationChannel.IN_APP.value]
        elif priority == NotificationPriority.HIGH.value:
            return [NotificationChannel.EMAIL.value, NotificationChannel.IN_APP.value]
        else:
            return [NotificationChannel.IN_APP.value]
    
    def _format_audit_alert(self, alert_data: Dict[str, Any]) -> str:
        """Format audit alert content."""
        return f"""
AUDIT ALERT

Alert Type: {alert_data.get('type', 'Unknown')}
Severity: {alert_data.get('severity', 'Medium')}
Description: {alert_data.get('description', 'No description provided')}

Please review this alert and take appropriate action.

Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """.strip()
    
    def _format_compliance_warning(self, compliance_data: Dict[str, Any]) -> str:
        """Format compliance warning content."""
        return f"""
COMPLIANCE WARNING

Compliance Score: {compliance_data.get('compliance_score', 0.0):.2f}
Overall Status: {compliance_data.get('overall_status', 'Unknown')}

Frameworks Checked: {', '.join(compliance_data.get('frameworks_checked', []))}

Please review the compliance issues and address any violations.

Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """.strip()
    
    def _format_report_ready(self, report_info: Dict[str, Any]) -> str:
        """Format report ready notification content."""
        return f"""
REPORT READY

Report: {report_info.get('report_name', 'Audit Report')}
Type: {report_info.get('report_type', 'Unknown')}
Generated: {report_info.get('generated_at', datetime.now().isoformat())}

Your requested report is now available for download.

Report ID: {report_info.get('report_id', 'N/A')}
        """.strip()
    
    def _format_deadline_reminder(self, deadline_info: Dict[str, Any], days_until: int) -> str:
        """Format deadline reminder content."""
        urgency = "URGENT" if days_until <= 1 else "REMINDER"
        
        return f"""
{urgency}: DEADLINE APPROACHING

Task: {deadline_info.get('task_name', 'Audit Task')}
Deadline: {deadline_info.get('deadline_date', 'Not specified')}
Days Remaining: {days_until}

{'IMMEDIATE ACTION REQUIRED' if days_until <= 1 else 'Please ensure timely completion.'}

Task ID: {deadline_info.get('task_id', 'N/A')}
        """.strip()
    
    def get_notification_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent notification history."""
        return self.sent_notifications[-limit:]
    
    def get_notification_stats(self) -> Dict[str, Any]:
        """Get notification service statistics."""
        total_sent = len(self.sent_notifications)
        if not self.sent_notifications:
            return {
                'total_sent': 0,
                'success_rate': 0.0,
                'channels_used': [],
                'last_sent': None
            }
        
        successful = sum(1 for n in self.sent_notifications if n.get('status') == 'sent')
        channels_used = set()
        for notification in self.sent_notifications:
            channels_used.update(notification.get('channels', []))
        
        return {
            'total_sent': total_sent,
            'success_rate': (successful / total_sent) * 100 if total_sent > 0 else 0.0,
            'channels_used': list(channels_used),
            'last_sent': self.sent_notifications[-1].get('sent_at') if self.sent_notifications else None
        }
    
    def health_check(self) -> Dict[str, Any]:
        """Check notification service health."""
        try:
            return {
                'status': 'healthy',
                'enabled_channels': list(self.enabled_channels),
                'queue_size': len(self.notification_queue),
                'total_sent': len(self.sent_notifications),
                'last_check': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Notification service health check failed: {str(e)}")
            return {
                'status': 'unhealthy',
                'error': str(e),
                'last_check': datetime.now().isoformat()
            }
