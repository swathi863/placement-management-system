import os
from datetime import datetime
from flask import Flask, render_template, session
from flask_mail import Mail
from config import Config
from models import db, Student, Admin
from seed import seed_database

mail = Mail()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Ensure upload directories exist
    os.makedirs(app.config['RESUME_FOLDER'], exist_ok=True)
    os.makedirs(app.config['LOGO_FOLDER'], exist_ok=True)

    # Initialize extensions
    db.init_app(app)
    mail.init_app(app)

    # Register Blueprints
    from blueprints.main import main_bp
    from blueprints.auth import auth_bp
    from blueprints.student import student_bp
    from blueprints.admin import admin_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(student_bp)
    app.register_blueprint(admin_bp)

    # Context Processors & Filters
    @app.context_processor
    def inject_globals():
        role = session.get('user_role')
        user_id = session.get('user_id')
        current_user = None
        
        if role == 'student' and user_id:
            current_user = Student.query.get(user_id)
        elif role == 'admin' and user_id:
            current_user = Admin.query.get(user_id)

        return {
            'user_role': role,
            'current_user': current_user,
            'now': datetime.utcnow()
        }

    @app.template_filter('format_date')
    def format_date_filter(dt, fmt='%b %d, %Y'):
        if not dt:
            return 'N/A'
        if isinstance(dt, str):
            return dt
        return dt.strftime(fmt)

    @app.template_filter('status_badge')
    def status_badge_filter(status):
        status_map = {
            'Applied': 'badge-applied',
            'Under Review': 'badge-review',
            'Shortlisted': 'badge-shortlisted',
            'Interview Scheduled': 'badge-interview',
            'Selected': 'badge-selected',
            'Rejected': 'badge-rejected',
            'Active': 'badge-selected',
            'Inactive': 'badge-rejected',
            'Scheduled': 'badge-interview',
            'Completed': 'badge-selected',
            'Cancelled': 'badge-rejected'
        }
        return status_map.get(status, 'badge-secondary')

    # Error Handlers
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('errors/404.html'), 404

    @app.errorhandler(403)
    def forbidden(e):
        return render_template('errors/403.html'), 403

    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('errors/500.html'), 500

    @app.errorhandler(413)
    def request_entity_too_large(e):
        return render_template('errors/413.html'), 413

    # Database Initialization & Auto-Migration for Render PostgreSQL
    with app.app_context():
        db.create_all()
        try:
            with db.engine.connect() as conn:
                conn.execute(db.text("ALTER TABLE application ADD COLUMN IF NOT EXISTS match_score FLOAT DEFAULT 0.0;"))
                conn.execute(db.text("ALTER TABLE application ADD COLUMN IF NOT EXISTS screening_result VARCHAR(20) DEFAULT 'Pending';"))
                conn.commit()
        except Exception as e:
            app.logger.info(f"Auto-migration notice: {e}")
        seed_database()

    return app

app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
