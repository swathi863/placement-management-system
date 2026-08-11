import os
import re
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


def calculate_resume_match_score(student, job, cover_note=""):
    """
    Automated Applicant Tracking System (ATS) Resume & Profile Match Algorithm (0.0% - 100.0%).
    """
    score = 0.0

    # 1. CGPA Alignment Score (Max 25 points)
    min_cgpa = job.min_cgpa if job.min_cgpa > 0 else 5.0
    student_cgpa = student.cgpa if student.cgpa else 0.0
    
    if student_cgpa >= min_cgpa:
        cgpa_score = 25.0
        # Bonus for high CGPA
        if student_cgpa >= min_cgpa + 1.0:
            cgpa_score = 25.0
    else:
        cgpa_score = max(0.0, (student_cgpa / min_cgpa) * 25.0)
    score += cgpa_score

    # 2. Branch Alignment Score (Max 20 points)
    eligible_branches = job.get_branches_list()
    if 'All' in eligible_branches or (student.branch and student.branch in eligible_branches):
        branch_score = 20.0
    else:
        branch_score = 5.0
    score += branch_score

    # 3. Keyword & Skills Overlap Score (Max 40 points)
    job_text = f"{job.title} {job.description} {job.requirements or ''}".lower()
    student_skills = (student.skills or '').lower()
    student_bio = (student.bio or '').lower()
    student_cover = (cover_note or '').lower()
    student_text = f"{student_skills} {student_bio} {student_cover}".lower()

    # Extract alphanumeric words (> 2 chars)
    job_words = set(re.findall(r'\b[a-z0-9+#]{2,}\b', job_text))
    student_words = set(re.findall(r'\b[a-z0-9+#]{2,}\b', student_text))

    # Common technical & professional keywords to prioritize
    tech_keywords = {'python', 'java', 'javascript', 'html', 'css', 'sql', 'react', 'flask', 'django', 
                     'node', 'aws', 'cloud', 'docker', 'git', 'c++', 'embedded', 'autocad', 'robotics',
                     'analytics', 'data', 'finance', 'engineering', 'backend', 'frontend', 'developer'}
    
    matched_tech = tech_keywords.intersection(job_words).intersection(student_words)
    common_all = job_words.intersection(student_words)

    if job_words:
        keyword_overlap_ratio = len(common_all) / max(10, len(job_words))
        skill_score = min(40.0, (keyword_overlap_ratio * 30.0) + (len(matched_tech) * 5.0))
        # Ensure a baseline if candidate has explicitly listed skills
        if len(student.get_skills_list()) >= 3:
            skill_score = max(20.0, skill_score)
    else:
        skill_score = 25.0
    score += skill_score

    # 4. Profile & Resume File Completeness Score (Max 15 points)
    completeness_score = 0.0
    if student.resume_filename:
        completeness_score += 10.0
    if student.phone and len(student.phone) > 5:
        completeness_score += 2.5
    if cover_note and len(cover_note.strip()) > 10:
        completeness_score += 2.5
    score += completeness_score

    # Round final score to 1 decimal place (capped between 0.0 and 100.0)
    final_score = round(min(100.0, max(0.0, score)), 1)
    return final_score
