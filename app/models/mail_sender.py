import smtplib
import mimetypes
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email import encoders
import requests
from dotenv import load_dotenv
import os
from typing import Union, Tuple
from pathlib import Path
# Load environment variables
load_dotenv()

# Get SMTP credentials
smtp_user = os.getenv("SMTP_USER")
smtp_pass = os.getenv("SMTP_PASS")
smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
smtp_port = int(os.getenv("SMTP_PORT", "587"))

class EmailSender:
    def __init__(self):
        self.sender_email = smtp_user
        self.sender_password = smtp_pass
        
        # Supported file types
        self.supported_types = {
            'image': ['.jpg', '.jpeg', '.png', '.gif'],
            'document': ['.pdf', '.doc', '.docx', '.txt', '.csv', '.xlsx'],
            'other': ['.zip', '.rar']
        }

    def _create_smtp_server(self):
        """Create and return configured SMTP server"""
        try:
            print(f"Connecting to SMTP server {smtp_host}:{smtp_port}")
            server = smtplib.SMTP(smtp_host, smtp_port)
            server.set_debuglevel(1)  # Add this line for detailed SMTP interaction
            print("Starting TLS...")
            server.starttls()
            print(f"Logging in as {self.sender_email}...")
            server.login(self.sender_email, self.sender_password)
            print("SMTP login successful")
            return server
        except smtplib.SMTPAuthenticationError as e:
            print(f"SMTP Authentication Error: {str(e)}")
            raise ValueError("Failed to authenticate with SMTP server. Check your credentials.")
        except Exception as e:
            print(f"SMTP Connection Error: {str(e)}")
            raise ConnectionError(f"Failed to connect to SMTP server: {str(e)}")

    def send_text_email(self, to_email, subject, body):
        """Send a simple text email"""
        try:
            # Validate inputs
            if not all([to_email, subject, body]):
                raise ValueError("Missing required fields (to_email, subject, or body)")

            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.sender_email
            msg['To'] = to_email
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain'))

            # Send email
            with self._create_smtp_server() as server:
                server.send_message(msg)
                
            return True, "Email sent successfully!"
            
        except Exception as e:
            return False, f"Failed to send email: {str(e)}"

    def _get_mime_type(self, file_url):
        """Determine MIME type based on file extension"""
        extension = os.path.splitext(file_url)[1].lower()
        
        if extension in self.supported_types['image']:
            return 'image'
        elif extension in self.supported_types['document']:
            return 'document'
        elif extension in self.supported_types['other']:
            return 'other'
        else:
            return None

    def send_attachment_email(self, to_email: str, subject: str, body: str, file_path: str) -> Tuple[bool, str]:
        """Send email with attachment"""
        try:
            print(f"Starting to send email with attachment...")
            print(f"To: {to_email}")
            print(f"Subject: {subject}")
            print(f"File path: {file_path}")

            # Validate inputs
            if not all([to_email, subject, body, file_path]):
                raise ValueError("Missing required fields")

            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.sender_email
            msg['To'] = to_email
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain'))

            # Read the file directly
            try:
                print("Reading file...")
                with open(file_path, 'rb') as f:
                    file_data = f.read()
                print(f"Read file size: {len(file_data)} bytes")
                
                filename = os.path.basename(file_path)
                print(f"Using filename: {filename}")

            except Exception as e:
                print(f"File read error: {str(e)}")
                raise ValueError(f"Failed to read file: {str(e)}")

            # Determine MIME type
            mime_type, _ = mimetypes.guess_type(file_path)
            if not mime_type:
                mime_type = 'application/octet-stream'
            maintype, subtype = mime_type.split('/', 1)

            print(f"Detected MIME type: {mime_type}")
            print("Creating MIME part...")
            
            # Create attachment part
            part = MIMEBase(maintype, subtype)
            part.set_payload(file_data)
            encoders.encode_base64(part)

            # Add header with filename
            part.add_header(
                'Content-Disposition',
                'attachment',
                filename=filename
            )
            msg.attach(part)
            print("File attached to message")

            print("Connecting to SMTP server...")
            with self._create_smtp_server() as server:
                print("Sending message...")
                server.send_message(msg)
                print("Message sent successfully!")
                
            return True, "Email with attachment sent successfully!"
                
        except Exception as e:
            print(f"Error sending email: {str(e)}")
            return False, f"Failed to send email: {str(e)}"
def send_email_via_smtp(from_email, to_email, subject, body):
    email_sender = EmailSender()
    return email_sender.send_text_email(to_email, subject, body)[1]

def send_email_with_attachment(subject, body, to_email, file_url):
    email_sender = EmailSender()
    return email_sender.send_attachment_email(to_email, subject, body, file_url)[1]