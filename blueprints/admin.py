from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from models import db, Student, Company, Job, Application, Interview
from utils import admin_required, save_uploaded_file, send_notification_email

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    total_students = Student.query.count()
    total_companies = Company.query.count()
    total_jobs = Job.query.count()
    total_applications = Application.query.count()

    selected_students_count = Application.query.filter_by(status='Selected').distinct(Application.student_id).count()
    placement_rate = round((selected_students_count / total_students * 100), 1) if total_students > 0 else 0.0

    shortlisted_count = Application.query.filter_by(status='Shortlisted').count()
    interview_count = Interview.query.filter_by(status='Scheduled').count()

    # Branch wise count
    branches = ['Computer Science', 'Information Technology', 'Electronics', 'Mechanical', 'Civil']
    branch_stats = {}
    for b in branches:
        count = Student.query.filter_by(branch=b).count()
        placed = Application.query.join(Student).filter(Student.branch == b, Application.status == 'Selected').distinct(Student.id).count()
        branch_stats[b] = {'total': count, 'placed': placed}

    recent_applications = Application.query.order_by(Application.applied_at.desc()).limit(8).all()
    recent_jobs = Job.query.order_by(Job.created_at.desc()).limit(5).all()

    return render_template('admin/dashboard.html',
                           total_students=total_students,
                           total_companies=total_companies,
                           total_jobs=total_jobs,
                           total_applications=total_applications,
                           selected_students_count=selected_students_count,
                           placement_rate=placement_rate,
                           shortlisted_count=shortlisted_count,
                           interview_count=interview_count,
                           branch_stats=branch_stats,
                           recent_applications=recent_applications,
                           recent_jobs=recent_jobs)


# -------------------------
# MANAGE STUDENTS
# -------------------------
@admin_bp.route('/students')
@admin_required
def students():
    search = request.args.get('search', '').strip()
    branch = request.args.get('branch', '').strip()
    min_cgpa_str = request.args.get('min_cgpa', '').strip()

    query = Student.query

    if search:
        query = query.filter(
            Student.name.ilike(f'%{search}%') | 
            Student.email.ilike(f'%{search}%') |
            Student.skills.ilike(f'%{search}%')
        )

    if branch:
        query = query.filter_by(branch=branch)

    if min_cgpa_str:
        try:
            min_cgpa = float(min_cgpa_str)
            query = query.filter(Student.cgpa >= min_cgpa)
        except ValueError:
            pass

    students_list = query.order_by(Student.name.asc()).all()

    return render_template('admin/students.html', 
                           students=students_list, 
                           search=search, 
                           branch=branch, 
                           min_cgpa=min_cgpa_str)


@admin_bp.route('/student/<int:student_id>')
@admin_required
def student_detail(student_id):
    student = Student.query.get_or_404(student_id)
    applications = Application.query.filter_by(student_id=student.id).order_by(Application.applied_at.desc()).all()
    return render_template('admin/student_detail.html', student=student, applications=applications)


@admin_bp.route('/student/<int:student_id>/delete', methods=['POST'])
@admin_required
def delete_student(student_id):
    student = Student.query.get_or_404(student_id)
    name = student.name
    db.session.delete(student)
    db.session.commit()
    flash(f'Student record for "{name}" has been deleted.', 'success')
    return redirect(url_for('admin.students'))


# -------------------------
# MANAGE COMPANIES
# -------------------------
@admin_bp.route('/companies')
@admin_required
def companies():
    search = request.args.get('search', '').strip()
    query = Company.query
    if search:
        query = query.filter(Company.name.ilike(f'%{search}%') | Company.industry.ilike(f'%{search}%'))
    companies_list = query.order_by(Company.name.asc()).all()
    return render_template('admin/companies.html', companies=companies_list, search=search)


@admin_bp.route('/company/add', methods=['GET', 'POST'])
@admin_required
def add_company():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        industry = request.form.get('industry', '').strip()
        location = request.form.get('location', '').strip()
        website = request.form.get('website', '').strip()
        contact_email = request.form.get('contact_email', '').strip()
        description = request.form.get('description', '').strip()

        if not name:
            flash('Company name is required.', 'danger')
            return render_template('admin/company_form.html', company=None)

        logo_filename = None
        if 'logo' in request.files and request.files['logo'].filename != '':
            logo_filename, err = save_uploaded_file(
                request.files['logo'],
                current_app.config['LOGO_FOLDER'],
                current_app.config['ALLOWED_LOGO_EXTENSIONS']
            )
            if err:
                flash(err, 'danger')
                return render_template('admin/company_form.html', company=None)

        new_company = Company(
            name=name,
            industry=industry,
            location=location,
            website=website,
            contact_email=contact_email,
            description=description,
            logo_filename=logo_filename
        )
        db.session.add(new_company)
        db.session.commit()

        flash(f'Company "{name}" added successfully!', 'success')
        return redirect(url_for('admin.companies'))

    return render_template('admin/company_form.html', company=None)


@admin_bp.route('/company/edit/<int:company_id>', methods=['GET', 'POST'])
@admin_required
def edit_company(company_id):
    company = Company.query.get_or_404(company_id)

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        industry = request.form.get('industry', '').strip()
        location = request.form.get('location', '').strip()
        website = request.form.get('website', '').strip()
        contact_email = request.form.get('contact_email', '').strip()
        description = request.form.get('description', '').strip()

        if not name:
            flash('Company name is required.', 'danger')
            return render_template('admin/company_form.html', company=company)

        if 'logo' in request.files and request.files['logo'].filename != '':
            logo_filename, err = save_uploaded_file(
                request.files['logo'],
                current_app.config['LOGO_FOLDER'],
                current_app.config['ALLOWED_LOGO_EXTENSIONS']
            )
            if err:
                flash(err, 'danger')
                return render_template('admin/company_form.html', company=company)
            company.logo_filename = logo_filename

        company.name = name
        company.industry = industry
        company.location = location
        company.website = website
        company.contact_email = contact_email
        company.description = description

        db.session.commit()
        flash(f'Company "{name}" updated successfully!', 'success')
        return redirect(url_for('admin.companies'))

    return render_template('admin/company_form.html', company=company)


@admin_bp.route('/company/delete/<int:company_id>', methods=['POST'])
@admin_required
def delete_company(company_id):
    company = Company.query.get_or_404(company_id)
    name = company.name
    db.session.delete(company)
    db.session.commit()
    flash(f'Company "{name}" and all associated job postings deleted.', 'success')
    return redirect(url_for('admin.companies'))


# -------------------------
# MANAGE JOBS
# -------------------------
@admin_bp.route('/jobs')
@admin_required
def jobs():
    search = request.args.get('search', '').strip()
    company_id = request.args.get('company_id', '').strip()

    query = Job.query.join(Company)
    if search:
        query = query.filter(Job.title.ilike(f'%{search}%') | Company.name.ilike(f'%{search}%'))

    if company_id:
        try:
            query = query.filter(Job.company_id == int(company_id))
        except ValueError:
            pass

    jobs_list = query.order_by(Job.created_at.desc()).all()
    companies = Company.query.order_by(Company.name.asc()).all()

    return render_template('admin/jobs.html', jobs=jobs_list, companies=companies, search=search, company_id=company_id)


@admin_bp.route('/job/add', methods=['GET', 'POST'])
@admin_required
def add_job():
    companies = Company.query.order_by(Company.name.asc()).all()
    if not companies:
        flash('Please add at least one company before creating job postings.', 'warning')
        return redirect(url_for('admin.add_company'))

    if request.method == 'POST':
        company_id = request.form.get('company_id')
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        requirements = request.form.get('requirements', '').strip()
        job_type = request.form.get('job_type', 'Full-time')
        salary_package = request.form.get('salary_package', '').strip()
        location = request.form.get('location', '').strip()
        min_cgpa_str = request.form.get('min_cgpa', '0.0').strip()
        branches_list = request.form.getlist('branches')
        deadline_str = request.form.get('deadline', '').strip()

        errors = []
        if not company_id:
            errors.append('Please select a company.')
        if not title:
            errors.append('Job title is required.')
        if not description:
            errors.append('Job description is required.')

        try:
            min_cgpa = float(min_cgpa_str) if min_cgpa_str else 0.0
        except ValueError:
            errors.append('Invalid minimum CGPA format.')
            min_cgpa = 0.0

        deadline = None
        if deadline_str:
            try:
                deadline = datetime.strptime(deadline_str, '%Y-%m-%dT%H:%M')
            except ValueError:
                try:
                    deadline = datetime.strptime(deadline_str, '%Y-%m-%d')
                except ValueError:
                    errors.append('Invalid deadline date format.')

        eligible_branches = ','.join(branches_list) if branches_list else 'All'

        if errors:
            for err in errors:
                flash(err, 'danger')
            return render_template('admin/job_form.html', job=None, companies=companies)

        new_job = Job(
            company_id=int(company_id),
            title=title,
            description=description,
            requirements=requirements,
            job_type=job_type,
            salary_package=salary_package,
            location=location,
            min_cgpa=min_cgpa,
            eligible_branches=eligible_branches,
            deadline=deadline,
            is_active=True
        )
        db.session.add(new_job)
        db.session.commit()

        flash(f'Job posting "{title}" created successfully!', 'success')
        return redirect(url_for('admin.jobs'))

    return render_template('admin/job_form.html', job=None, companies=companies)


@admin_bp.route('/job/edit/<int:job_id>', methods=['GET', 'POST'])
@admin_required
def edit_job(job_id):
    job = Job.query.get_or_404(job_id)
    companies = Company.query.order_by(Company.name.asc()).all()

    if request.method == 'POST':
        company_id = request.form.get('company_id')
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        requirements = request.form.get('requirements', '').strip()
        job_type = request.form.get('job_type', 'Full-time')
        salary_package = request.form.get('salary_package', '').strip()
        location = request.form.get('location', '').strip()
        min_cgpa_str = request.form.get('min_cgpa', '0.0').strip()
        branches_list = request.form.getlist('branches')
        deadline_str = request.form.get('deadline', '').strip()
        is_active = request.form.get('is_active') == '1'

        errors = []
        if not title:
            errors.append('Job title is required.')

        try:
            min_cgpa = float(min_cgpa_str) if min_cgpa_str else 0.0
        except ValueError:
            errors.append('Invalid minimum CGPA format.')
            min_cgpa = job.min_cgpa

        deadline = None
        if deadline_str:
            try:
                deadline = datetime.strptime(deadline_str, '%Y-%m-%dT%H:%M')
            except ValueError:
                try:
                    deadline = datetime.strptime(deadline_str, '%Y-%m-%d')
                except ValueError:
                    errors.append('Invalid deadline date format.')

        eligible_branches = ','.join(branches_list) if branches_list else 'All'

        if errors:
            for err in errors:
                flash(err, 'danger')
            return render_template('admin/job_form.html', job=job, companies=companies)

        job.company_id = int(company_id)
        job.title = title
        job.description = description
        job.requirements = requirements
        job.job_type = job_type
        job.salary_package = salary_package
        job.location = location
        job.min_cgpa = min_cgpa
        job.eligible_branches = eligible_branches
        job.deadline = deadline
        job.is_active = is_active

        db.session.commit()
        flash(f'Job posting "{title}" updated successfully!', 'success')
        return redirect(url_for('admin.jobs'))

    return render_template('admin/job_form.html', job=job, companies=companies)


@admin_bp.route('/job/toggle/<int:job_id>', methods=['POST'])
@admin_required
def toggle_job(job_id):
    job = Job.query.get_or_404(job_id)
    job.is_active = not job.is_active
    db.session.commit()
    status_str = "activated" if job.is_active else "deactivated"
    flash(f'Job "{job.title}" has been {status_str}.', 'info')
    return redirect(url_for('admin.jobs'))


@admin_bp.route('/job/delete/<int:job_id>', methods=['POST'])
@admin_required
def delete_job(job_id):
    job = Job.query.get_or_404(job_id)
    title = job.title
    db.session.delete(job)
    db.session.commit()
    flash(f'Job posting "{title}" and related applications removed.', 'success')
    return redirect(url_for('admin.jobs'))


# -------------------------
# MANAGE APPLICATIONS
# -------------------------
@admin_bp.route('/applications')
@admin_required
def applications():
    status_filter = request.args.get('status', '').strip()
    job_id = request.args.get('job_id', '').strip()
    search = request.args.get('search', '').strip()

    query = Application.query.join(Student).join(Job).join(Company)

    if status_filter:
        query = query.filter(Application.status == status_filter)

    if job_id:
        try:
            query = query.filter(Application.job_id == int(job_id))
        except ValueError:
            pass

    if search:
        query = query.filter(
            Student.name.ilike(f'%{search}%') | 
            Student.email.ilike(f'%{search}%') |
            Job.title.ilike(f'%{search}%') |
            Company.name.ilike(f'%{search}%')
        )

    apps_list = query.order_by(Application.updated_at.desc()).all()
    all_jobs = Job.query.order_by(Job.title.asc()).all()

    return render_template('admin/applications.html', 
                           applications=apps_list, 
                           jobs=all_jobs, 
                           status_filter=status_filter, 
                           job_id=job_id,
                           search=search)


@admin_bp.route('/application/<int:app_id>/status', methods=['POST'])
@admin_required
def update_application_status(app_id):
    app = Application.query.get_or_404(app_id)
    new_status = request.form.get('status', '').strip()
    remarks = request.form.get('remarks', '').strip()

    valid_statuses = ['Applied', 'Under Review', 'Shortlisted', 'Interview Scheduled', 'Selected', 'Rejected']
    if new_status not in valid_statuses:
        flash('Invalid status selection.', 'danger')
        return redirect(url_for('admin.applications'))

    app.status = new_status
    if remarks:
        app.remarks = remarks
    app.updated_at = datetime.utcnow()

    db.session.commit()

    # Send email notification to student
    send_notification_email(
        subject=f"Application Update: {app.job.title} at {app.job.company.name}",
        recipient=app.student.email,
        body_text=f"Hello {app.student.name},\n\nYour application status for '{app.job.title}' at {app.job.company.name} has been updated to '{new_status}'.\n\nRemarks: {remarks or 'No additional remarks.'}\n\nPlease log in to the Placement Portal for complete details."
    )

    flash(f'Application status updated to "{new_status}" for student {app.student.name}.', 'success')
    return redirect(request.referrer or url_for('admin.applications'))


# -------------------------
# SCHEDULE INTERVIEWS
# -------------------------
@admin_bp.route('/interviews')
@admin_required
def interviews():
    interviews_list = Interview.query.join(Application).join(Student).join(Job)\
        .order_by(Interview.interview_date.asc(), Interview.interview_time.asc()).all()
    
    # Candidates eligible for interview scheduling
    eligible_apps = Application.query.filter(Application.status.in_(['Shortlisted', 'Interview Scheduled', 'Applied']))\
        .order_by(Application.applied_at.desc()).all()

    return render_template('admin/interviews.html', interviews=interviews_list, eligible_apps=eligible_apps)


@admin_bp.route('/interview/schedule/<int:app_id>', methods=['POST'])
@admin_required
def schedule_interview(app_id):
    app = Application.query.get_or_404(app_id)
    
    round_name = request.form.get('round_name', 'Technical Interview').strip()
    interview_date = request.form.get('interview_date', '').strip()
    interview_time = request.form.get('interview_time', '').strip()
    mode = request.form.get('mode', 'Online').strip()
    location_or_link = request.form.get('location_or_link', '').strip()
    instructions = request.form.get('instructions', '').strip()

    if not round_name or not interview_date or not interview_time:
        flash('Please fill in Round Name, Date, and Time for the interview.', 'danger')
        return redirect(url_for('admin.interviews'))

    new_interview = Interview(
        application_id=app.id,
        round_name=round_name,
        interview_date=interview_date,
        interview_time=interview_time,
        mode=mode,
        location_or_link=location_or_link,
        instructions=instructions,
        status='Scheduled'
    )

    if app.status in ['Applied', 'Under Review', 'Shortlisted']:
        app.status = 'Interview Scheduled'
        app.updated_at = datetime.utcnow()

    db.session.add(new_interview)
    db.session.commit()

    # Send email notification to student
    send_notification_email(
        subject=f"Interview Scheduled: {round_name} - {app.job.company.name}",
        recipient=app.student.email,
        body_text=f"Hello {app.student.name},\n\nAn interview round ({round_name}) has been scheduled for your application to '{app.job.title}' at {app.job.company.name}.\n\n📅 Date: {interview_date}\n⏰ Time: {interview_time}\n💻 Mode: {mode}\n📍 Venue/Link: {location_or_link or 'Check Portal'}\n\nInstructions: {instructions or 'None'}\n\nPlease log in to the portal to view complete details."
    )

    flash(f'Interview "{round_name}" scheduled for {app.student.name} on {interview_date} at {interview_time}!', 'success')
    return redirect(url_for('admin.interviews'))


@admin_bp.route('/interview/delete/<int:interview_id>', methods=['POST'])
@admin_required
def delete_interview(interview_id):
    interview = Interview.query.get_or_404(interview_id)
    student_name = interview.application.student.name
    round_name = interview.round_name

    db.session.delete(interview)
    db.session.commit()

    flash(f'Interview round "{round_name}" for {student_name} deleted.', 'info')
    return redirect(url_for('admin.interviews'))
