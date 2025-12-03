"""
SMTP Email Handler for Attendance System
Handles sending email notifications for attendance events
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
import os
from typing import Optional, List


class SMTPHandler:
    """Handles SMTP email operations for the attendance system"""
    
    def __init__(self, smtp_server: str, smtp_port: int, sender_email: str, 
                 sender_password: str, use_tls: bool = True):
        """
        Initialize SMTP Handler
        
        Args:
            smtp_server: SMTP server address (e.g., 'smtp.gmail.com')
            smtp_port: SMTP port (e.g., 587 for TLS, 465 for SSL)
            sender_email: Email address to send from
            sender_password: Password or app-specific password
            use_tls: Whether to use TLS encryption
        """
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.sender_email = sender_email
        self.sender_password = sender_password
        self.use_tls = use_tls
        
    def send_email(self, recipient_email: str, subject: str, body: str, 
                   html_body: Optional[str] = None, 
                   attachments: Optional[List[str]] = None) -> tuple[bool, str]:
        """
        Send an email
        
        Args:
            recipient_email: Recipient's email address
            subject: Email subject
            body: Plain text email body
            html_body: Optional HTML version of the email body
            attachments: Optional list of file paths to attach
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = self.sender_email
            msg['To'] = recipient_email
            msg['Subject'] = subject
            msg['Date'] = datetime.now().strftime('%a, %d %b %Y %H:%M:%S %z')
            
            # Attach plain text version
            msg.attach(MIMEText(body, 'plain'))
            
            # Attach HTML version if provided
            if html_body:
                msg.attach(MIMEText(html_body, 'html'))
            
            # Attach files if provided
            if attachments:
                for file_path in attachments:
                    if os.path.exists(file_path):
                        with open(file_path, 'rb') as f:
                            part = MIMEBase('application', 'octet-stream')
                            part.set_payload(f.read())
                            encoders.encode_base64(part)
                            part.add_header(
                                'Content-Disposition',
                                f'attachment; filename={os.path.basename(file_path)}'
                            )
                            msg.attach(part)
            
            # Connect and send
            if self.use_tls:
                server = smtplib.SMTP(self.smtp_server, self.smtp_port)
                server.starttls()
            else:
                server = smtplib.SMTP_SSL(self.smtp_server, self.smtp_port)
            
            server.login(self.sender_email, self.sender_password)
            server.send_message(msg)
            server.quit()
            
            return True, f"Email sent successfully to {recipient_email}"
            
        except smtplib.SMTPAuthenticationError:
            return False, "SMTP Authentication failed. Check email/password."
        except smtplib.SMTPException as e:
            return False, f"SMTP error occurred: {str(e)}"
        except Exception as e:
            return False, f"Failed to send email: {str(e)}"
    
    def send_attendance_notification(self, person_name: str, person_id: str, 
                                    recipient_email: str, event_type: str, 
                                    timestamp: str) -> tuple[bool, str]:
        """
        Send attendance event notification
        
        Args:
            person_name: Name of the person
            person_id: Person's ID
            recipient_email: Email to send notification to
            event_type: Type of event ('arrival' or 'departure')
            timestamp: Timestamp of the event
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        subject = f"Attendance Alert: {event_type.capitalize()} - {person_name}"
        
        # Plain text body
        body = f"""
Attendance Notification

Name: {person_name}
ID: {person_id}
Event: {event_type.capitalize()}
Time: {timestamp}

This is an automated notification from the Face Recognition Attendance System.
"""
        
        # HTML body
        html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #4CAF50; color: white; padding: 20px; text-align: center; border-radius: 5px 5px 0 0; }}
        .content {{ background-color: #f9f9f9; padding: 20px; border: 1px solid #ddd; border-radius: 0 0 5px 5px; }}
        .info-row {{ margin: 10px 0; padding: 10px; background-color: white; border-left: 4px solid #4CAF50; }}
        .label {{ font-weight: bold; color: #555; }}
        .footer {{ margin-top: 20px; text-align: center; font-size: 12px; color: #777; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h2>Attendance Notification</h2>
        </div>
        <div class="content">
            <div class="info-row">
                <span class="label">Name:</span> {person_name}
            </div>
            <div class="info-row">
                <span class="label">ID:</span> {person_id}
            </div>
            <div class="info-row">
                <span class="label">Event:</span> {event_type.capitalize()}
            </div>
            <div class="info-row">
                <span class="label">Time:</span> {timestamp}
            </div>
        </div>
        <div class="footer">
            <p>This is an automated notification from the Face Recognition Attendance System.</p>
        </div>
    </div>
</body>
</html>
"""
        
        return self.send_email(recipient_email, subject, body, html_body)
    
    def send_daily_summary(self, recipient_email: str, summary_data: dict, 
                          attachment_path: Optional[str] = None) -> tuple[bool, str]:
        """
        Send daily attendance summary
        
        Args:
            recipient_email: Email to send summary to
            summary_data: Dictionary containing summary statistics
            attachment_path: Optional path to CSV export file
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        date_str = datetime.now().strftime('%Y-%m-%d')
        subject = f"Daily Attendance Summary - {date_str}"
        
        total = summary_data.get('total_registered', 0)
        present = summary_data.get('present_today', 0)
        absent = total - present
        
        # Plain text body
        body = f"""
Daily Attendance Summary - {date_str}

Total Registered: {total}
Present Today: {present}
Absent Today: {absent}
Attendance Rate: {(present/total*100) if total > 0 else 0:.1f}%

Please find the detailed attendance report attached.

---
Face Recognition Attendance System
"""
        
        # HTML body
        html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #2196F3; color: white; padding: 20px; text-align: center; border-radius: 5px 5px 0 0; }}
        .content {{ background-color: #f9f9f9; padding: 20px; border: 1px solid #ddd; }}
        .stats {{ display: flex; justify-content: space-around; margin: 20px 0; }}
        .stat-box {{ background-color: white; padding: 15px; border-radius: 5px; text-align: center; flex: 1; margin: 0 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .stat-number {{ font-size: 32px; font-weight: bold; color: #2196F3; }}
        .stat-label {{ font-size: 14px; color: #666; margin-top: 5px; }}
        .footer {{ background-color: #f9f9f9; padding: 15px; text-align: center; font-size: 12px; color: #777; border-radius: 0 0 5px 5px; border: 1px solid #ddd; border-top: none; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h2>Daily Attendance Summary</h2>
            <p>{date_str}</p>
        </div>
        <div class="content">
            <div class="stats">
                <div class="stat-box">
                    <div class="stat-number">{total}</div>
                    <div class="stat-label">Total Registered</div>
                </div>
                <div class="stat-box">
                    <div class="stat-number" style="color: #4CAF50;">{present}</div>
                    <div class="stat-label">Present Today</div>
                </div>
                <div class="stat-box">
                    <div class="stat-number" style="color: #f44336;">{absent}</div>
                    <div class="stat-label">Absent Today</div>
                </div>
            </div>
            <div style="text-align: center; margin-top: 20px;">
                <p style="font-size: 18px;">
                    Attendance Rate: <strong>{(present/total*100) if total > 0 else 0:.1f}%</strong>
                </p>
            </div>
        </div>
        <div class="footer">
            <p>Face Recognition Attendance System</p>
            <p>Automated Daily Report</p>
        </div>
    </div>
</body>
</html>
"""
        
        attachments = [attachment_path] if attachment_path else None
        return self.send_email(recipient_email, subject, body, html_body, attachments)
    
    def send_late_arrival_alert(self, person_name: str, person_id: str, 
                               recipient_email: str, arrival_time: str, 
                               expected_time: str) -> tuple[bool, str]:
        """
        Send late arrival alert
        
        Args:
            person_name: Name of the person
            person_id: Person's ID
            recipient_email: Email to send alert to
            arrival_time: Actual arrival time
            expected_time: Expected arrival time
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        subject = f"Late Arrival Alert: {person_name}"
        
        body = f"""
Late Arrival Alert

Name: {person_name}
ID: {person_id}
Expected Time: {expected_time}
Actual Arrival: {arrival_time}

This person has arrived late today.

---
Face Recognition Attendance System
"""
        
        html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #ff9800; color: white; padding: 20px; text-align: center; border-radius: 5px 5px 0 0; }}
        .content {{ background-color: #fff3e0; padding: 20px; border: 1px solid #ffe0b2; border-radius: 0 0 5px 5px; }}
        .info-row {{ margin: 10px 0; padding: 10px; background-color: white; border-left: 4px solid #ff9800; }}
        .label {{ font-weight: bold; color: #555; }}
        .warning {{ color: #f57c00; font-weight: bold; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h2>⚠️ Late Arrival Alert</h2>
        </div>
        <div class="content">
            <div class="info-row">
                <span class="label">Name:</span> {person_name}
            </div>
            <div class="info-row">
                <span class="label">ID:</span> {person_id}
            </div>
            <div class="info-row">
                <span class="label">Expected Time:</span> {expected_time}
            </div>
            <div class="info-row">
                <span class="label">Actual Arrival:</span> <span class="warning">{arrival_time}</span>
            </div>
            <p style="margin-top: 20px; text-align: center;">
                This person has arrived late today.
            </p>
        </div>
    </div>
</body>
</html>
"""
        
        return self.send_email(recipient_email, subject, body, html_body)
    
    def send_absence_alert(self, person_name: str, person_id: str, 
                          recipient_email: str, date: str, 
                          department: str = None) -> tuple[bool, str]:
        """
        Send absence alert notification
        
        Args:
            person_name: Name of the person
            person_id: Person's ID
            recipient_email: Email to send alert to
            date: Date of absence
            department: Optional department name
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        subject = f"Absence Alert: {person_name} - {date}"
        
        dept_info = f"\nDepartment: {department}" if department else ""
        
        body = f"""
Absence Alert

Name: {person_name}
ID: {person_id}{dept_info}
Date: {date}

This person is absent today and has not marked attendance.

---
Face Recognition Attendance System
"""
        
        html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #f44336; color: white; padding: 20px; text-align: center; border-radius: 5px 5px 0 0; }}
        .content {{ background-color: #ffebee; padding: 20px; border: 1px solid #ffcdd2; border-radius: 0 0 5px 5px; }}
        .info-row {{ margin: 10px 0; padding: 10px; background-color: white; border-left: 4px solid #f44336; }}
        .label {{ font-weight: bold; color: #555; }}
        .alert {{ color: #c62828; font-weight: bold; }}
        .footer {{ margin-top: 20px; text-align: center; font-size: 12px; color: #777; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h2>🚫 Absence Alert</h2>
        </div>
        <div class="content">
            <div class="info-row">
                <span class="label">Name:</span> {person_name}
            </div>
            <div class="info-row">
                <span class="label">ID:</span> {person_id}
            </div>
            {f'<div class="info-row"><span class="label">Department:</span> {department}</div>' if department else ''}
            <div class="info-row">
                <span class="label">Date:</span> <span class="alert">{date}</span>
            </div>
            <p style="margin-top: 20px; text-align: center; color: #c62828;">
                This person is absent today and has not marked attendance.
            </p>
        </div>
        <div class="footer">
            <p>This is an automated notification from the Face Recognition Attendance System.</p>
        </div>
    </div>
</body>
</html>
"""
        
        return self.send_email(recipient_email, subject, body, html_body)
    
    def test_connection(self) -> tuple[bool, str]:
        """
        Test SMTP connection
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            if self.use_tls:
                server = smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=10)
                server.starttls()
            else:
                server = smtplib.SMTP_SSL(self.smtp_server, self.smtp_port, timeout=10)
            
            server.login(self.sender_email, self.sender_password)
            server.quit()
            
            return True, "SMTP connection successful"
            
        except smtplib.SMTPAuthenticationError:
            return False, "Authentication failed. Check email/password."
        except smtplib.SMTPException as e:
            return False, f"SMTP error: {str(e)}"
        except Exception as e:
            return False, f"Connection failed: {str(e)}"
