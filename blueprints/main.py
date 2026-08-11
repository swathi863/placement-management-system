import os
from flask import Blueprint, render_template, redirect, url_for, session, send_from_directory, current_app, Response

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
    
    # If the requested resume/logo file does not exist on disk, return a clean preview fallback notice
    if not os.path.exists(file_path):
        fallback_html = """
        <!DOCTYPE html>
        <html>
        <head>
          <style>
            body { font-family: -apple-system, BlinkMacSystemFont, sans-serif; background: #f8fafc; color: #334155; display: flex; align-items: center; justify-content: center; height: 100vh; margin: 0; text-align: center; }
            .box { background: white; padding: 2.5rem; border-radius: 12px; border: 1px solid #e2e8f0; max-width: 420px; box-shadow: 0 4px 12px rgba(0,0,0,0.05); }
            h2 { color: #0f172a; margin-bottom: 0.5rem; font-size: 1.25rem; }
            p { font-size: 0.9rem; color: #64748b; line-height: 1.5; }
            .icon { font-size: 3rem; margin-bottom: 0.75rem; }
          </style>
        </head>
        <body>
          <div class="box">
            <div class="icon">📄</div>
            <h2>Resume File Not Found</h2>
            <p>The candidate has not uploaded a valid PDF file yet or the database was recently cleared.<br><br>Please ask the candidate to log in and upload their updated resume.</p>
          </div>
        </body>
        </html>
        """
        return Response(fallback_html, mimetype='text/html', status=200)

    directory = os.path.dirname(file_path)
    base_name = os.path.basename(file_path)
    return send_from_directory(directory, base_name)
