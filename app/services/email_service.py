"""Email service for sending notifications and verification emails."""

import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from ..core.config import settings

class EmailService:
    """Service for sending emails via Gmail SMTP."""
    
    def __init__(self):
        """Initialize email service with Gmail SMTP configuration."""
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587
        self.username = settings.gmail_user
        self.password = settings.gmail_app_password
        self.frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
    
    def send_verification_email(self, to_email: str, verification_token: str) -> bool:
        """Send email verification link to user.
        
        Args:
            to_email: Recipient email address
            verification_token: JWT token for verification
            
        Returns:
            True if email sent successfully, False otherwise
        """
        if not self.username or not self.password:
            print("Email credentials not configured")
            return False
            
        try:
            msg = MIMEMultipart()
            msg['From'] = self.username
            msg['To'] = to_email
            msg['Subject'] = "MedRAG - Email Verification"
            
            body = f"""
            Welcome to MedRAG!
            
            Please verify your email by clicking the link below:
            {self.frontend_url}/verify?token={verification_token}
            
            This link will expire in 24 hours.
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.username, self.password)
            server.send_message(msg)
            server.quit()
            
            return True
        except Exception as e:
            print(f"Email sending failed: {e}")
            return False
    
    def send_diagnosis_notification(self, to_email: str, patient_name: str) -> bool:
        """Send diagnosis completion notification.
        
        Args:
            to_email: Recipient email address
            patient_name: Patient identifier
            
        Returns:
            True if email sent successfully, False otherwise
        """
        if not self.username or not self.password:
            print("Email credentials not configured")
            return False
            
        try:
            msg = MIMEMultipart()
            msg['From'] = self.username
            msg['To'] = to_email
            msg['Subject'] = "MedRAG - Diagnosis Complete"
            
            body = f"""
            Hello,
            
            Your medical diagnosis for patient {patient_name} has been completed.
            Please log in to your MedRAG dashboard to view the results.
            
            Best regards,
            MedRAG Team
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.username, self.password)
            server.send_message(msg)
            server.quit()
            
            return True
        except Exception as e:
            print(f"Email sending failed: {e}")
            return False

email_service = EmailService()