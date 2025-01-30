# email_sender.py
from email.mime.base import MIMEBase
from email import encoders
import os

def prepare_attachment(file_path):
    """
    Prepares the attachment for the email.
    """
    try:
        with open(file_path, "rb") as file:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(file.read())  # Read the file content
            encoders.encode_base64(part)  # Encode the file in base64
            part.add_header('Content-Disposition', f'attachment; filename={os.path.basename(file_path)}')
            return part
    except Exception as e:
        print(f"Error preparing attachment: {str(e)}")
        return f"Error preparing attachment: {str(e)}"
