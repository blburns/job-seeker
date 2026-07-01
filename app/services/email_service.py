"""
Email Service
Handles all email sending functionality with support for multiple providers
"""

import logging
import os
from typing import Optional, Dict, Any
from flask import current_app, render_template_string

logger = logging.getLogger(__name__)


class EmailService:
    """Email service for sending transactional emails"""
    
    def __init__(self, app=None):
        self.app = app
        self.provider = None
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize email service with Flask app"""
        self.app = app
        email_provider = app.config.get('EMAIL_PROVIDER', 'console')
        
        if email_provider == 'sendgrid':
            self.provider = SendGridProvider(app)
        elif email_provider == 'mailgun':
            self.provider = MailgunProvider(app)
        elif email_provider == 'smtp':
            self.provider = SMTPProvider(app)
        else:
            self.provider = ConsoleProvider(app)
        
        logger.info(f"Email service initialized with provider: {email_provider}")
    
    def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
        from_email: Optional[str] = None,
        from_name: Optional[str] = None
    ) -> bool:
        """
        Send an email
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            html_content: HTML email content
            text_content: Plain text email content (optional)
            from_email: Sender email (optional, uses default if not provided)
            from_name: Sender name (optional)
        
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        try:
            if not self.provider:
                logger.error("Email provider not initialized")
                return False
            
            # Use default from_email if not provided
            if not from_email:
                from_email = self.app.config.get('EMAIL_FROM', 'noreply@example.com')
            
            if not from_name:
                from_name = self.app.config.get('EMAIL_FROM_NAME', 'Application')
            
            return self.provider.send(
                to_email=to_email,
                subject=subject,
                html_content=html_content,
                text_content=text_content,
                from_email=from_email,
                from_name=from_name
            )
        
        except Exception as e:
            logger.exception(f"Error sending email to {to_email}: {e}")
            return False
    
    def send_template_email(
        self,
        to_email: str,
        subject: str,
        template_name: str,
        template_data: Dict[str, Any],
        from_email: Optional[str] = None,
        from_name: Optional[str] = None
    ) -> bool:
        """
        Send an email using a template
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            template_name: Name of the email template
            template_data: Data to pass to the template
            from_email: Sender email (optional)
            from_name: Sender name (optional)
        
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        try:
            # Load template
            template_path = os.path.join(
                self.app.root_path,
                'templates',
                'emails',
                f'{template_name}.html'
            )
            
            if not os.path.exists(template_path):
                logger.error(f"Email template not found: {template_path}")
                return False
            
            with open(template_path, 'r') as f:
                template_content = f.read()
            
            # Render template
            html_content = render_template_string(template_content, **template_data)
            
            return self.send_email(
                to_email=to_email,
                subject=subject,
                html_content=html_content,
                from_email=from_email,
                from_name=from_name
            )
        
        except Exception as e:
            logger.exception(f"Error sending template email to {to_email}: {e}")
            return False


class ConsoleProvider:
    """Console email provider for development (prints to console)"""
    
    def __init__(self, app):
        self.app = app
    
    def send(self, to_email, subject, html_content, text_content=None, from_email=None, from_name=None):
        """Print email to console"""
        logger.info("=" * 80)
        logger.info("EMAIL (Console Provider)")
        logger.info(f"From: {from_name} <{from_email}>")
        logger.info(f"To: {to_email}")
        logger.info(f"Subject: {subject}")
        logger.info("-" * 80)
        logger.info(html_content)
        logger.info("=" * 80)
        return True


class SendGridProvider:
    """SendGrid email provider"""
    
    def __init__(self, app):
        self.app = app
        self.api_key = app.config.get('SENDGRID_API_KEY')
        
        if not self.api_key:
            logger.warning("SENDGRID_API_KEY not configured")
    
    def send(self, to_email, subject, html_content, text_content=None, from_email=None, from_name=None):
        """Send email via SendGrid"""
        try:
            import sendgrid
            from sendgrid.helpers.mail import Mail, Email, To, Content
            
            sg = sendgrid.SendGridAPIClient(api_key=self.api_key)
            
            message = Mail(
                from_email=Email(from_email, from_name),
                to_emails=To(to_email),
                subject=subject,
                html_content=Content("text/html", html_content)
            )
            
            if text_content:
                message.add_content(Content("text/plain", text_content))
            
            response = sg.send(message)
            
            if response.status_code in [200, 201, 202]:
                logger.info(f"Email sent successfully to {to_email} via SendGrid")
                return True
            else:
                logger.error(f"SendGrid error: {response.status_code} - {response.body}")
                return False
        
        except Exception as e:
            logger.exception(f"SendGrid error: {e}")
            return False


class MailgunProvider:
    """Mailgun email provider"""
    
    def __init__(self, app):
        self.app = app
        self.api_key = app.config.get('MAILGUN_API_KEY')
        self.domain = app.config.get('MAILGUN_DOMAIN')
        
        if not self.api_key or not self.domain:
            logger.warning("MAILGUN_API_KEY or MAILGUN_DOMAIN not configured")
    
    def send(self, to_email, subject, html_content, text_content=None, from_email=None, from_name=None):
        """Send email via Mailgun"""
        try:
            import requests
            
            url = f"https://api.mailgun.net/v3/{self.domain}/messages"
            
            data = {
                "from": f"{from_name} <{from_email}>",
                "to": to_email,
                "subject": subject,
                "html": html_content
            }
            
            if text_content:
                data["text"] = text_content
            
            response = requests.post(
                url,
                auth=("api", self.api_key),
                data=data
            )
            
            if response.status_code == 200:
                logger.info(f"Email sent successfully to {to_email} via Mailgun")
                return True
            else:
                logger.error(f"Mailgun error: {response.status_code} - {response.text}")
                return False
        
        except Exception as e:
            logger.exception(f"Mailgun error: {e}")
            return False


class SMTPProvider:
    """SMTP email provider"""
    
    def __init__(self, app):
        self.app = app
        self.host = app.config.get('SMTP_HOST', 'localhost')
        self.port = app.config.get('SMTP_PORT', 587)
        self.username = app.config.get('SMTP_USERNAME')
        self.password = app.config.get('SMTP_PASSWORD')
        self.use_tls = app.config.get('SMTP_USE_TLS', True)
    
    def send(self, to_email, subject, html_content, text_content=None, from_email=None, from_name=None):
        """Send email via SMTP"""
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{from_name} <{from_email}>"
            msg['To'] = to_email
            
            if text_content:
                part1 = MIMEText(text_content, 'plain')
                msg.attach(part1)
            
            part2 = MIMEText(html_content, 'html')
            msg.attach(part2)
            
            with smtplib.SMTP(self.host, self.port) as server:
                if self.use_tls:
                    server.starttls()
                
                if self.username and self.password:
                    server.login(self.username, self.password)
                
                server.send_message(msg)
            
            logger.info(f"Email sent successfully to {to_email} via SMTP")
            return True
        
        except Exception as e:
            logger.exception(f"SMTP error: {e}")
            return False


# Global email service instance
email_service = EmailService()
