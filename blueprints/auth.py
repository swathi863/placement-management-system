from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadTimeSignature
from models import db, Student, Admin
from utils import send_notification_email

auth_bp = Blueprint('auth', __name__)

def get_serializer():
    return URLSafeTimedSerializer(current_app.config['SECRET_KEY'])

@auth_bp.route('/login', methods=['GET', 'POST'])
def student_login():
    if session.get('user_role') == 'student':
        return redirect(url_for('student.dashboard'))
    elif session.get('user_role') == 'admin':
        return redirect(url_for('admin.dashboard'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '').strip()

        if not email or not password:
            flash('Please enter both email and password.', 'danger')
            return render_template('auth/student_login.html', email=email)

        student = Student.query.filter_by(email=email).first()
        if student and student.check_password(password):
            session.clear()
            session['user_id'] = student.id
            session['user_role'] = 'student'
            session['user_name'] = student.name
            session['user_email'] = student.email
            flash(f'Welcome back, {student.name}!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('student.dashboard'))

        flash('Invalid email or password. Please try again.', 'danger')
        return render_template('auth/student_login.html', email=email)

    return render_template('auth/student_login.html')


@auth_bp.route('/register', methods=['GET', 'POST'])
def student_register():
    if session.get('user_role') == 'student':
        return redirect(url_for('student.dashboard'))

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()
        phone = request.form.get('phone', '').strip()
        branch = request.form.get('branch', '').strip()
        cgpa_str = request.form.get('cgpa', '0.0').strip()
        grad_year_str = request.form.get('grad_year', '').strip()
        skills = request.form.get('skills', '').strip()

        errors = []
        if not name or len(name) < 2:
            errors.append('Name must be at least 2 characters long.')
        if not email or '@' not in email:
            errors.append('Please provide a valid email address.')
        if not password or len(password) < 6:
            errors.append('Password must be at least 6 characters long.')
        if password != confirm_password:
            errors.append('Passwords do not match.')
        
        try:
            cgpa = float(cgpa_str) if cgpa_str else 0.0
            if cgpa < 0.0 or cgpa > 10.0:
                errors.append('CGPA must be between 0.0 and 10.0.')
        except ValueError:
            errors.append('CGPA must be a valid number.')
            cgpa = 0.0

        try:
            grad_year = int(grad_year_str) if grad_year_str else datetime.utcnow().year
        except ValueError:
            grad_year = None

        existing_student = Student.query.filter_by(email=email).first()
        if existing_student:
            errors.append('An account with this email already exists.')

        if errors:
            for err in errors:
                flash(err, 'danger')
            return render_template('auth/student_register.html', 
                                   name=name, email=email, phone=phone, 
                                   branch=branch, cgpa=cgpa_str, 
                                   grad_year=grad_year_str, skills=skills)

        new_student = Student(
            name=name,
            email=email,
            phone=phone,
            branch=branch or 'Computer Science',
            cgpa=cgpa,
            grad_year=grad_year,
            skills=skills
        )
        new_student.set_password(password)
        
        db.session.add(new_student)
        db.session.commit()

        # Auto-login
        session.clear()
        session['user_id'] = new_student.id
        session['user_role'] = 'student'
        session['user_name'] = new_student.name
        session['user_email'] = new_student.email

        # Welcome Email Notification
        send_notification_email(
            subject="Welcome to University Placement Portal",
            recipient=new_student.email,
            body_text=f"Hello {new_student.name},\n\nWelcome to the University Placement Management System!\n\nYour account has been successfully created with the following details:\n- Email: {new_student.email}\n- Branch: {new_student.branch}\n- CGPA: {new_student.cgpa}\n\nYou can now log in, upload your resume, browse open recruitment drives, and apply for opportunities.\n\nBest regards,\nUniversity Placement Cell"
        )

        flash('Registration successful! Welcome to the Placement Portal.', 'success')
        return redirect(url_for('student.dashboard'))

    return render_template('auth/student_register.html')


@auth_bp.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if session.get('user_role') == 'admin':
        return redirect(url_for('admin.dashboard'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '').strip()

        if not email or not password:
            flash('Please enter both email and password.', 'danger')
            return render_template('auth/admin_login.html', email=email)

        admin = Admin.query.filter_by(email=email).first()
        if admin and admin.check_password(password):
            session.clear()
            session['user_id'] = admin.id
            session['user_role'] = 'admin'
            session['user_name'] = admin.name
            session['user_email'] = admin.email
            flash(f'Admin portal access granted. Welcome, {admin.name}!', 'success')
            return redirect(url_for('admin.dashboard'))

        flash('Invalid admin credentials. Please verify and try again.', 'danger')
        return render_template('auth/admin_login.html', email=email)

    return render_template('auth/admin_login.html')


@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        role = request.form.get('role', 'student').strip()

        if not email:
            flash('Please enter your registered email address.', 'danger')
            return render_template('auth/forgot_password.html', email=email, role=role)

        user = None
        if role == 'admin':
            user = Admin.query.filter_by(email=email).first()
        else:
            user = Student.query.filter_by(email=email).first()

        if user:
            serializer = get_serializer()
            token = serializer.dumps({'user_id': user.id, 'role': role}, salt='password-reset-salt')
            reset_url = url_for('auth.reset_password', token=token, _external=True)

            # Send Email
            send_notification_email(
                subject="Password Reset Request - Placement Portal",
                recipient=user.email,
                body_text=f"Hello {user.name},\n\nWe received a request to reset your password for the University Placement Portal.\n\nPlease click the link below (or paste it into your browser) to set a new password:\n{reset_url}\n\nThis password reset link is valid for 1 hour.\nIf you did not request a password reset, please ignore this email.\n\nBest regards,\nUniversity Placement Cell"
            )

        # Flash generic message for security
        flash(f'If an account with {email} exists, a password reset link has been sent to your email inbox.', 'info')
        return redirect(url_for('auth.student_login' if role == 'student' else 'auth.admin_login'))

    role_param = request.args.get('role', 'student')
    return render_template('auth/forgot_password.html', role=role_param)


@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    serializer = get_serializer()
    try:
        data = serializer.loads(token, salt='password-reset-salt', max_age=3600)
    except (SignatureExpired, BadTimeSignature):
        flash('The password reset link is invalid or has expired. Please request a new one.', 'danger')
        return redirect(url_for('auth.forgot_password'))

    user_id = data.get('user_id')
    role = data.get('role')

    user = None
    if role == 'admin':
        user = Admin.query.get(user_id)
    else:
        user = Student.query.get(user_id)

    if not user:
        flash('User account not found.', 'danger')
        return redirect(url_for('auth.forgot_password'))

    if request.method == 'POST':
        password = request.form.get('password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()

        if not password or len(password) < 6:
            flash('Password must be at least 6 characters long.', 'danger')
            return render_template('auth/reset_password.html', token=token)

        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('auth/reset_password.html', token=token)

        user.set_password(password)
        db.session.commit()

        flash('Your password has been reset successfully! Please sign in with your new password.', 'success')
        return redirect(url_for('auth.student_login' if role == 'student' else 'auth.admin_login'))

    return render_template('auth/reset_password.html', token=token, user=user, role=role)


@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('auth.student_login'))
