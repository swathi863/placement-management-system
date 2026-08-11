import os
from flask import Blueprint, render_template, redirect, url_for, session, send_from_directory, current_app, abort

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    user_role = session.get('user_role')
    if user_role == 'student':
        return redirect(url_for('student.dashboard'))
    elif user_role == 'admin':
        return redirect(url_for('admin.dashboard'))
    return render_template('index.html')


@main_bp.route('/uploads/<path:filename>')
def uploaded_file(filename):
    file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
    if not os.path.exists(file_path):
        abort(404)
    directory = os.path.dirname(file_path)
    base_name = os.path.basename(file_path)
    return send_from_directory(directory, base_name)
