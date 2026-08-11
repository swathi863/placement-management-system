import os
import uuid
import logging
import threading
from functools import wraps
from flask import session, redirect, url_for, flash, request, current_app
from werkzeug.utils import secure_filename
from models import Student, Admin

def allowed_file(filename, allowed_set):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_set

def save_uploaded_file(file, folder_path, allowed_set):
    if not file or file.filename == '':
        return None, "No file selected."
    
    if not allowed_file(file.filename, allowed_set):
        ext_str = ", ".join(allowed_set)
        return None, f"Invalid file format. Only {ext_str} files are allowed."
    
    original_filename = secure_filename(file.filename)
    extension = original_filename.rsplit('.', 1)[1].lower()
    unique_filename = f"{uuid.uuid4().hex}_{original_filename}"
    
    os.makedirs(folder_path, exist_ok=True)
    full_path = os.path.join(folder_path, unique_filename)
    file.save(full_path)
    
    return unique_filename, None

def get_current_user():
    user_role = session.get('user_role')
    user_id = session.get('user_id')
    
    if not user_role or not user_id:
        return None, None
    
    if user_role == 'student':
        student = Student.query.get(user_id)
        return 'student', student
    elif user_role == 'admin':
        admin = Admin.query.get(user_id)
        return 'admin', admin
        
    return None, None

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.student_login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def student_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or session.get('user_role') != 'student':
            flash('Access restricted to Students only.', 'danger')
            return redirect(url_for('auth.student_login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or session.get('user_role') != 'admin':
            flash('Access restricted to Administrators only.', 'danger')
            return redirect(url_for('auth.admin_login'))
        return f(*args, **kwargs)
    return decorated_function


def _send_async_email(app, subject, recipient, body_text):
    """Background worker function for asynchronous email sending."""
    with app.app_context():
        try:
            from flask_mail import Message
            mail_extension = app.extensions.get('mail')
            
            if not app.config.get('MAIL_SERVER') or not mail_extension:
                logging.info(f"Mail notification skipped (MAIL_SERVER not set). To: {recipient}")
                return

            msg = Message(
                subject=subject,
                recipients=[recipient],
                body=body_text,
                sender=app.config.get('MAIL_DEFAULT_SENDER')
            )
            mail_extension.send(msg)
            logging.info(f"Asynchronous email sent successfully to {recipient}")
        except Exception as e:
            logging.warning(f"Failed to send async email to {recipient}: {str(e)}")


def send_notification_email(subject, recipient, body_text):
    """Dispatches email notification asynchronously in a background thread so the web page responds instantly."""
    app = current_app._get_current_object()
    thread = threading.Thread(target=_send_async_email, args=(app, subject, recipient, body_text))
    thread.daemon = True
    thread.start()
    return True
