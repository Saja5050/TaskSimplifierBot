import requests
import time
from config.settings import BOT_TOKEN
from app.models.mail_sender import EmailSender
from app.views import messages
import os

# Initialize EmailSender
email_sender = EmailSender()

# Store user sessions
user_sessions = {}

def handle_command(data):
    """Process incoming message and execute corresponding command"""
    try:
        message = data['message']
        chat_id = message['chat']['id']

        # Check for cancel command first
        if 'text' in message and message['text'] == '/cancel':
            if chat_id in user_sessions:
                del user_sessions[chat_id]
                return send_message(chat_id, "Operation cancelled. You can start again with /send_mail")

        # Handle ongoing session
        if chat_id in user_sessions:
            session = user_sessions[chat_id]

            # Handle each state
            if session['step'] == 'waiting_for_email':
                if 'text' not in message:
                    return send_message(chat_id, "Please enter a valid email address.")
                return ask_for_content_type(chat_id, message['text'])
                
            elif session['step'] == 'waiting_for_content_type':
                if 'text' not in message:
                    return send_message(chat_id, "Please enter a number between 1 and 3.")
                return ask_for_subject(chat_id, message['text'])
                
            elif session['step'] == 'waiting_for_text_message':
                if 'text' not in message:
                    return send_message(chat_id, "Please enter your message text.")
                return handle_text_message(chat_id, message['text'])

            elif session['step'] == 'waiting_for_rename':
                return handle_rename_choice(chat_id, message)

            elif session['step'] == 'waiting_for_new_name':
                return handle_new_name(chat_id, message)
                
            elif session['step'] == 'waiting_for_file':
                return handle_file_upload(chat_id, message)
                
            elif session['step'] == 'waiting_for_description':
                return handle_description(chat_id, message)
                
            elif session['step'] == 'waiting_for_subject':
                if 'text' not in message:
                    return send_message(chat_id, "Please enter a subject for your email.")
                return send_content(chat_id, message['text'])

        # Handle initial commands
        if 'text' in message:
            text = message['text']
            if text.startswith('/start'):
                return handle_start(chat_id)
            elif text.startswith('/help'):
                return handle_help(chat_id)
            elif text.startswith('/send_mail'):
                return initiate_send_mail(chat_id)
            else:
                return send_message(chat_id, "Sorry, I don't recognize that command. Type /help for a list of commands.")
        
        return send_message(chat_id, "Please send a text message or use /help for available commands.")
            
    except Exception as e:
        print(f"Error in handle_command: {str(e)}")
        return f"An error occurred. Please try again with /send_mail"

def handle_start(chat_id):
    """Send welcome message"""
    start_text = (
        "Welcome to TaskSimplifierBot!\n"
        "I can help you send emails with text, photos, and files.\n"
        "Type /help for a list of commands."
    )
    return send_message(chat_id, start_text)

def handle_help(chat_id):
    """Send help message"""
    help_message = (
        "Available commands:\n\n"
        "/start - Start the bot\n"
        "/help - Show this help message\n"
        "/send_mail - Send an email\n"
        "/cancel - Cancel current operation\n\n"
        "When sending mail, you can:\n"
        "1. Send text messages\n"
        "2. Send photos\n"
        "3. Send files (PDF, DOC, etc.)"
    )
    return send_message(chat_id, help_message)

def initiate_send_mail(chat_id):
    """Start email sending process"""
    user_sessions[chat_id] = {
        'step': 'waiting_for_email',
        'start_time': time.time()
    }
    return send_message(chat_id, "Please enter the recipient's email address:")

def ask_for_content_type(chat_id, email):
    """Handle email input and ask for content type"""
    if '@' not in email or '.' not in email:
        return send_message(chat_id, "Please enter a valid email address.")

    user_sessions[chat_id].update({
        'email': email,
        'step': 'waiting_for_content_type'
    })

    content_message = (
        "What type of content would you like to send?\n"
        "1. Text message\n"
        "2. Photo\n"
        "3. File\n"
        "Please enter the number (1-3):"
    )
    return send_message(chat_id, content_message)

def ask_for_subject(chat_id, content_type):
    """Process content type selection"""
    try:
        choice = content_type.strip()
        if choice not in ['1', '2', '3']:
            return send_message(chat_id, "Invalid choice. Please enter a number between 1 and 3.")

        content_types = {
            '1': ('text', 'waiting_for_text_message', "Please enter the text message you want to send:"),
            '2': ('photo', 'waiting_for_rename', "Would you like to rename your photo?\n1. Yes\n2. No (use original name)"),
            '3': ('file', 'waiting_for_rename', "Would you like to rename your file?\n1. Yes\n2. No (use original name)")
        }

        content_type, step, message = content_types[choice]
        user_sessions[chat_id].update({
            'content_type': content_type,
            'step': step
        })
        return send_message(chat_id, message)

    except Exception as e:
        print(f"Error in ask_for_subject: {str(e)}")
        return send_message(chat_id, "Invalid choice. Please enter a number between 1 and 3.")

def handle_text_message(chat_id, message):
    """Handle text message input"""
    user_sessions[chat_id].update({
        'text_message': message,
        'step': 'waiting_for_subject'
    })
    return send_message(chat_id, "Please enter the subject for your email (or type 'skip' for default subject):")

def handle_rename_choice(chat_id, message):
    """Handle file rename choice"""
    if 'text' not in message:
        return send_message(chat_id, "Please enter 1 for Yes or 2 for No.")

    choice = message['text'].strip()
    if choice not in ['1', '2']:
        return send_message(chat_id, "Invalid choice. Please enter 1 for Yes or 2 for No.")

    if choice == '1':
        user_sessions[chat_id].update({
            'step': 'waiting_for_new_name'
        })
        content_type = user_sessions[chat_id]['content_type']
        message = "Please enter the new name for your photo:" if content_type == 'photo' else "Please enter the new name for your file:"
        return send_message(chat_id, message)
    else:
        user_sessions[chat_id].update({
            'step': 'waiting_for_file'
        })
        content_type = user_sessions[chat_id]['content_type']
        message = "Please upload the photo:" if content_type == 'photo' else "Please upload the file:"
        return send_message(chat_id, message)

def handle_new_name(chat_id, message):
    """Handle new filename input"""
    if 'text' not in message:
        return send_message(chat_id, "Please enter a valid name.")

    new_name = message['text'].strip()
    user_sessions[chat_id].update({
        'new_filename': new_name,
        'step': 'waiting_for_file'
    })
    
    content_type = user_sessions[chat_id]['content_type']
    message = "Please upload the photo:" if content_type == 'photo' else "Please upload the file:"
    return send_message(chat_id, message)

def handle_file_upload(chat_id, message):
    """Process file or photo upload"""
    try:
        print(f"Message data: {message}")  # Debug print
        
        file_id = None
        file_type = None
        file_extension = None

        if 'photo' in message:
            file_id = message['photo'][-1]['file_id']
            file_type = 'photo'
            file_extension = '.jpg'
            original_filename = f'photo_{int(time.time())}.jpg'
        elif 'document' in message:
            file_id = message['document']['file_id']
            file_type = 'document'
            original_filename = message['document']['file_name']
            file_extension = os.path.splitext(original_filename)[1]
        else:
            return send_message(chat_id, "Please send a valid file or photo.")

        # Use custom filename if provided
        session = user_sessions[chat_id]
        if 'new_filename' in session:
            # Add original extension to new filename if needed
            if not session['new_filename'].endswith(file_extension):
                filename = session['new_filename'] + file_extension
            else:
                filename = session['new_filename']
        else:
            filename = original_filename

        # Get file info from Telegram
        file_info_url = f'https://api.telegram.org/bot{BOT_TOKEN}/getFile?file_id={file_id}'
        file_info = requests.get(file_info_url).json()
        
        print(f"File info: {file_info}")  # Debug print
        
        if file_info.get('ok'):
            file_path = file_info['result']['file_path']
            file_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_path}"
            
            print(f"File URL: {file_url}")  # Debug print
            
            # Download the file
            response = requests.get(file_url)
            file_content = response.content
            
            # Create temp directory if it doesn't exist
            os.makedirs('temp_files', exist_ok=True)
            
            # Save file locally with absolute path
            local_filename = os.path.abspath(os.path.join('temp_files', filename))
            with open(local_filename, 'wb') as f:
                f.write(file_content)
            
            user_sessions[chat_id].update({
                'file_path': local_filename,
                'file_type': file_type,
                'step': 'waiting_for_description'
            })

            return send_message(chat_id, f"{file_type.title()} received! Would you like to add a description? (or type 'skip' to proceed without description):")
        else:
            return send_message(chat_id, "Failed to process the file. Please try again.")

    except Exception as e:
        print(f"Error in handle_file_upload: {str(e)}")  # Debug print
        return send_message(chat_id, "Failed to process the file. Please try again.")

def handle_description(chat_id, message):
    """Handle file/photo description input"""
    if 'text' not in message:
        return send_message(chat_id, "Please enter a description or type 'skip'.")

    description = message['text']
    user_sessions[chat_id].update({
        'description': None if description.lower() == 'skip' else description,
        'step': 'waiting_for_subject'
    })

    return send_message(chat_id, "Please enter the subject for your email (or type 'skip' for default subject):")

def send_content(chat_id, subject):
    """Send the email with content"""
    try:
        session = user_sessions[chat_id]
        to_email = session['email']
        
        # Use default subject if skipped
        if subject.lower() == 'skip':
            subject = "Message from TaskSimplifier Bot"

        # Send based on content type
        if session['content_type'] == 'text':
            success, message = email_sender.send_text_email(
                to_email,
                subject,
                session['text_message']
            )
        else:
            file_path = session.get('file_path')
            if not file_path or not os.path.exists(file_path):
                return send_message(chat_id, "Error: File not found")

            # Create email body with description if provided
            description = session.get('description')
            body = f"Please see the attached {session['file_type']}"
            if description:
                body += f"\n\nDescription: {description}"

            success, message = email_sender.send_attachment_email(
                to_email,
                subject,
                body,
                file_path
            )
            try:
                if file_path and os.path.exists(file_path):
                    os.remove(file_path)
            except Exception as e:
                print(f"Error cleaning up file: {str(e)}")
        del user_sessions[chat_id]
        
        status = "sent successfully to" if success else "failed to send to"
        return send_message(chat_id, f"Content {status} {to_email}\n{message}")

    except Exception as e:
        print(f"Error in send_content: {str(e)}")
        return send_message(chat_id, f"Failed to send email: {str(e)}")

def send_message(chat_id, text):
    """Send message via Telegram API"""
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {"chat_id": chat_id, "text": text}
        response = requests.post(url, json=payload)
        response.raise_for_status()
        return "Message sent successfully."
    except Exception as e:
        print(f"Error sending message: {str(e)}")
        return "Failed to send message."