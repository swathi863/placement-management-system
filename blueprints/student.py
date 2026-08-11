from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from models import db, Student, Company, Job, Application, Interview
from utils import student_required, save_uploaded_file, send_notification_email, calculate_resume_match_score

student_bp = Blueprint('student', __name__, url_prefix='/student')

@student_bp.route('/dashboard')
@student_required
def dashboard():
    student_id = session.get('user_id')
    student = Student.query.get_or_404(student_id)

    # Metrics
    my_applications = Application.query.filter_by(student_id=student_id).all()
    total_applied = len(my_applications)
    shortlisted_count = sum(1 for a in my_applications if a.status in ['Shortlisted', 'Interview Scheduled'])
    selected_count = sum(1 for a in my_applications if a.status == 'Selected')

    # Upcoming interviews
    app_ids = [a.id for a in my_applications]
    upcoming_interviews = []
    if app_ids:
        upcoming_interviews = Interview.query.filter(
            Interview.application_id.in_(app_ids),
            Interview.status == 'Scheduled'
        ).order_by(Interview.interview_date.asc(), Interview.interview_time.asc()).limit(5).all()

    # Active jobs relevant to student
    active_jobs = Job.query.filter_by(is_active=True).order_by(Job.created_at.desc()).limit(6).all()

    # Application status list
    recent_applications = Application.query.filter_by(student_id=student_id)\
        .order_by(Application.updated_at.desc()).limit(5).all()

    return render_template('student/dashboard.html',
                           student=student,
                           total_applied=total_applied,
                           shortlisted_count=shortlisted_count,
                           selected_count=selected_count,
                           upcoming_interviews=upcoming_interviews,
                           active_jobs=active_jobs,
                           recent_applications=recent_applications)


@student_bp.route('/profile', methods=['GET', 'POST'])
@student_required
def profile():
    student_id = session.get('user_id')
    student = Student.query.get_or_404(student_id)

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        phone = request.form.get('phone', '').strip()
        branch = request.form.get('branch', '').strip()
        cgpa_str = request.form.get('cgpa', '0.0').strip()
        grad_year_str = request.form.get('grad_year', '').strip()
        bio = request.form.get('bio', '').strip()
        skills = request.form.get('skills', '').strip()

        errors = []
        if not name or len(name) < 2:
            errors.append('Name is required.')
        
        try:
            cgpa = float(cgpa_str)
            if cgpa < 0.0 or cgpa > 10.0:
                errors.append('CGPA must be between 0.0 and 10.0.')
        except ValueError:
            errors.append('Invalid CGPA format.')
            cgpa = student.cgpa

        try:
            grad_year = int(grad_year_str) if grad_year_str else student.grad_year
        except ValueError:
            grad_year = student.grad_year

        if errors:
            for err in errors:
                flash(err, 'danger')
            return render_template('student/profile.html', student=student)

        student.name = name
        student.phone = phone
        student.branch = branch
        student.cgpa = cgpa
        student.grad_year = grad_year
        student.bio = bio
        student.skills = skills

        session['user_name'] = student.name
        db.session.commit()

        flash('Your profile details have been updated successfully!', 'success')
        return redirect(url_for('student.profile'))

    return render_template('student/profile.html', student=student)


@student_bp.route('/resume', methods=['GET', 'POST'])
@student_required
def resume():
    student_id = session.get('user_id')
    student = Student.query.get_or_404(student_id)

    if request.method == 'POST':
        if 'resume' not in request.files:
            flash('No file part selected.', 'danger')
            return redirect(url_for('student.resume'))

        file = request.files['resume']
        if file.filename == '':
            flash('Please select a file to upload.', 'danger')
            return redirect(url_for('student.resume'))

        filename, error = save_uploaded_file(
            file,
            current_app.config['RESUME_FOLDER'],
            current_app.config['ALLOWED_RESUME_EXTENSIONS']
        )

        if error:
            flash(error, 'danger')
            return redirect(url_for('student.resume'))

        student.resume_filename = filename
        db.session.commit()

        flash('Resume uploaded and attached to your profile successfully!', 'success')
        return redirect(url_for('student.resume'))

    return render_template('student/resume.html', student=student)


@student_bp.route('/companies')
@student_required
def companies():
    search = request.args.get('search', '').strip()
    query = Company.query

    if search:
        query = query.filter(Company.name.ilike(f'%{search}%') | Company.industry.ilike(f'%{search}%'))

    companies_list = query.order_by(Company.name.asc()).all()
    return render_template('student/companies.html', companies=companies_list, search=search)


@student_bp.route('/jobs')
@student_required
def jobs():
    student_id = session.get('user_id')
    student = Student.query.get_or_404(student_id)

    search = request.args.get('search', '').strip()
    branch_filter = request.args.get('branch', '').strip()
    job_type = request.args.get('type', '').strip()
    eligible_only = request.args.get('eligible_only', '') == '1'

    query = Job.query.filter_by(is_active=True)

    if search:
        query = query.join(Company).filter(
            Job.title.ilike(f'%{search}%') | 
            Company.name.ilike(f'%{search}%') |
            Job.location.ilike(f'%{search}%')
        )

    if branch_filter:
        query = query.filter((Job.eligible_branches == 'All') | (Job.eligible_branches.ilike(f'%{branch_filter}%')))

    if job_type:
        query = query.filter_by(job_type=job_type)

    if eligible_only:
        query = query.filter(Job.min_cgpa <= student.cgpa)

    jobs_list = query.order_by(Job.created_at.desc()).all()

    # Get student's applied job IDs
    applied_job_ids = set(app.job_id for app in Application.query.filter_by(student_id=student_id).all())

    return render_template('student/jobs.html', 
                           jobs=jobs_list, 
                           student=student,
                           applied_job_ids=applied_job_ids,
                           search=search, 
                           branch_filter=branch_filter,
                           job_type=job_type,
                           eligible_only=eligible_only)


@student_bp.route('/job/<int:job_id>')
@student_required
def job_detail(job_id):
    student_id = session.get('user_id')
    student = Student.query.get_or_404(student_id)
    job = Job.query.get_or_404(job_id)

    existing_application = Application.query.filter_by(job_id=job.id, student_id=student.id).first()

    # Eligibility check
    is_cgpa_eligible = student.cgpa >= job.min_cgpa
    branches_list = job.get_branches_list()
    is_branch_eligible = ('All' in branches_list) or (student.branch in branches_list)
    is_eligible = is_cgpa_eligible and is_branch_eligible

    return render_template('student/job_detail.html',
                           job=job,
                           student=student,
                           application=existing_application,
                           is_eligible=is_eligible,
                           is_cgpa_eligible=is_cgpa_eligible,
                           is_branch_eligible=is_branch_eligible)


@student_bp.route('/apply/<int:job_id>', methods=['POST'])
@student_required
def apply_job(job_id):
    student_id = session.get('user_id')
    student = Student.query.get_or_404(student_id)
    job = Job.query.get_or_404(job_id)

    if not job.is_active or job.is_expired():
        flash('This job posting is no longer active or applications have closed.', 'danger')
        return redirect(url_for('student.job_detail', job_id=job.id))

    # File Upload inside Apply Modal
    if 'resume' in request.files and request.files['resume'].filename != '':
        filename, error = save_uploaded_file(
            request.files['resume'],
            current_app.config['RESUME_FOLDER'],
            current_app.config['ALLOWED_RESUME_EXTENSIONS']
        )
        if error:
            flash(error, 'danger')
            return redirect(url_for('student.job_detail', job_id=job.id))
        student.resume_filename = filename
        db.session.commit()

    if not student.resume_filename:
        flash('Please attach your PDF/DOCX resume file before applying for this job.', 'warning')
        return redirect(url_for('student.job_detail', job_id=job.id))

    # Verify eligibility
    branches_list = job.get_branches_list()
    is_branch_eligible = ('All' in branches_list) or (student.branch in branches_list)
    if student.cgpa < job.min_cgpa or not is_branch_eligible:
        flash('You do not meet the minimum eligibility criteria for this position.', 'danger')
        return redirect(url_for('student.job_detail', job_id=job.id))

    # Check duplicate application
    existing_app = Application.query.filter_by(job_id=job.id, student_id=student.id).first()
    if existing_app:
        flash('You have already applied for this job opportunity.', 'info')
        return redirect(url_for('student.job_detail', job_id=job.id))

    cover_note = request.form.get('cover_note', '').strip()

    # Calculate Automated ATS Resume Match Score (0.0 to 100.0%)
    match_score = calculate_resume_match_score(student, job, cover_note)
    cutoff = 60.0  # 60.0% cutoff for passing initial ATS screening

    if match_score >= cutoff:
        screening_result = 'Passed'
        status = 'Shortlisted'
        remarks = f"PASSED Automated ATS Resume Screening with Match Score of {match_score}%."
        
        email_subject = f"🎉 CONGRATULATIONS: Resume Passed Screening for {job.title} at {job.company.name}"
        email_body = f"Hello {student.name},\n\nGreat news! Your resume and profile successfully PASSED our automated ATS screening for '{job.title}' at {job.company.name} with a Resume Match Score of {match_score}%!\n\nYour application has been automatically Shortlisted. The placement team will schedule your interview round shortly.\n\nBest regards,\nUniversity Placement Cell"
        flash_msg = f'🎉 Congratulations! Your resume score ({match_score}%) PASSED screening. Your application has been Shortlisted!'
        flash_category = 'success'
    else:
        screening_result = 'Failed'
        status = 'Rejected'
        remarks = f"FAILED Automated ATS Resume Screening with Match Score of {match_score}% (Cutoff: {cutoff}%)."
        
        email_subject = f"Application Status Update: {job.title} at {job.company.name}"
        email_body = f"Hello {student.name},\n\nThank you for applying for '{job.title}' at {job.company.name}.\n\nYour automated ATS Resume Match Score for this position was {match_score}%, which did not meet the minimum screening cutoff of {cutoff}%.\n\nWe encourage you to update your skills profile, upload an updated resume, and apply for future opportunities.\n\nBest regards,\nUniversity Placement Cell"
        flash_msg = f'Notice: Your resume match score for this position was {match_score}%, which did not meet the {cutoff}% screening cutoff. Status: Rejected.'
        flash_category = 'warning'

    new_app = Application(
        job_id=job.id,
        student_id=student.id,
        cover_note=cover_note,
        status=status,
        match_score=match_score,
        screening_result=screening_result,
        remarks=remarks
    )
    db.session.add(new_app)
    db.session.commit()

    # Dispatch Automated Pass/Fail Email Notification
    send_notification_email(
        subject=email_subject,
        recipient=student.email,
        body_text=email_body
    )

    flash(flash_msg, flash_category)
    return redirect(url_for('student.applications'))


@student_bp.route('/applications')
@student_required
def applications():
    student_id = session.get('user_id')
    status_filter = request.args.get('status', '').strip()

    query = Application.query.filter_by(student_id=student_id)
    if status_filter:
        query = query.filter_by(status=status_filter)

    apps_list = query.order_by(Application.updated_at.desc()).all()
    return render_template('student/applications.html', applications=apps_list, current_status=status_filter)


@student_bp.route('/application/<int:app_id>')
@student_required
def application_detail(app_id):
    student_id = session.get('user_id')
    app = Application.query.filter_by(id=app_id, student_id=student_id).first_or_404()
    interviews = Interview.query.filter_by(application_id=app.id).order_by(Interview.created_at.desc()).all()

    return render_template('student/application_detail.html', application=app, interviews=interviews)


@student_bp.route('/interviews')
@student_required
def interviews():
    student_id = session.get('user_id')
    my_app_ids = [a.id for a in Application.query.filter_by(student_id=student_id).all()]

    interviews_list = []
    if my_app_ids:
        interviews_list = Interview.query.filter(Interview.application_id.in_(my_app_ids))\
            .order_by(Interview.interview_date.asc(), Interview.interview_time.asc()).all()

    return render_template('student/interviews.html', interviews=interviews_list)
