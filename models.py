from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Student(db.Model):
    __tablename__ = 'student'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    phone = db.Column(db.String(20))
    branch = db.Column(db.String(50))
    cgpa = db.Column(db.Float, default=0.0)
    grad_year = db.Column(db.Integer)
    bio = db.Column(db.Text)
    skills = db.Column(db.Text)  # Comma-separated list of skills
    resume_filename = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    applications = db.relationship('Application', backref='student', lazy=True, cascade='all, delete-orphan')

    @property
    def resume_url(self):
        return self.resume_filename

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_skills_list(self):
        if not self.skills:
            return []
        return [s.strip() for s in self.skills.split(',') if s.strip()]

    def __repr__(self):
        return f'<Student {self.email}>'


class Admin(db.Model):
    __tablename__ = 'admin'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<Admin {self.email}>'


class Company(db.Model):
    __tablename__ = 'company'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    industry = db.Column(db.String(100))
    location = db.Column(db.String(100))
    website = db.Column(db.String(150))
    contact_email = db.Column(db.String(120))
    description = db.Column(db.Text)
    logo_filename = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    jobs = db.relationship('Job', backref='company', lazy=True, cascade='all, delete-orphan')

    @property
    def logo_url(self):
        return self.logo_filename

    def __repr__(self):
        return f'<Company {self.name}>'


class Job(db.Model):
    __tablename__ = 'job'
    
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('company.id', ondelete='CASCADE'), nullable=False)
    title = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=False)
    requirements = db.Column(db.Text)
    job_type = db.Column(db.String(50), default='Full-time')  # Full-time, Internship, Contract
    salary_package = db.Column(db.String(100))
    location = db.Column(db.String(100))
    min_cgpa = db.Column(db.Float, default=0.0)
    eligible_branches = db.Column(db.String(255), default='All')  # Comma-separated or 'All'
    deadline = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    applications = db.relationship('Application', backref='job', lazy=True, cascade='all, delete-orphan')

    def get_branches_list(self):
        if not self.eligible_branches or self.eligible_branches == 'All':
            return ['All']
        return [b.strip() for b in self.eligible_branches.split(',') if b.strip()]

    def is_expired(self):
        if not self.deadline:
            return False
        return datetime.utcnow() > self.deadline

    def __repr__(self):
        return f'<Job {self.title}>'


class Application(db.Model):
    __tablename__ = 'application'
    __table_args__ = (db.UniqueConstraint('job_id', 'student_id', name='unique_job_student_app'),)
    
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey('job.id', ondelete='CASCADE'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id', ondelete='CASCADE'), nullable=False)
    cover_note = db.Column(db.Text)
    status = db.Column(db.String(50), default='Applied')  # Applied, Under Review, Shortlisted, Selected, Rejected
    match_score = db.Column(db.Float, default=0.0)
    screening_result = db.Column(db.String(20), default='Pending')  # Passed, Failed, Pending
    remarks = db.Column(db.Text)
    applied_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    interviews = db.relationship('Interview', backref='application', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Application Job:{self.job_id} Student:{self.student_id} Score:{self.match_score} Status:{self.status}>'


class Interview(db.Model):
    __tablename__ = 'interview'
    
    id = db.Column(db.Integer, primary_key=True)
    application_id = db.Column(db.Integer, db.ForeignKey('application.id', ondelete='CASCADE'), nullable=False)
    round_name = db.Column(db.String(100), nullable=False)  # e.g., Technical Round 1, HR Interview
    interview_date = db.Column(db.String(20), nullable=False)  # YYYY-MM-DD
    interview_time = db.Column(db.String(20), nullable=False)  # HH:MM
    mode = db.Column(db.String(50), default='Online')  # Online, In-Person
    location_or_link = db.Column(db.String(255))
    instructions = db.Column(db.Text)
    status = db.Column(db.String(50), default='Scheduled')  # Scheduled, Completed, Cancelled
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Interview {self.round_name} App:{self.application_id}>'
