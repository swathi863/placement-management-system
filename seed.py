from datetime import datetime, timedelta
from models import db, Student, Admin, Company, Job, Application, Interview

def seed_database():
    # Check if database is already seeded
    if Admin.query.first():
        print("Database already contains data. Skipping seed.")
        return

    print("Seeding database with initial sample data...")

    # 1. Admin Account
    admin = Admin(
        name="Placement Officer (Admin)",
        email="admin@placement.com"
    )
    admin.set_password("admin123")
    db.session.add(admin)

    # 2. Students
    s1 = Student(
        name="John Doe",
        email="john.doe@univ.edu",
        phone="+1 (555) 234-5678",
        branch="Computer Science",
        cgpa=8.8,
        grad_year=2026,
        bio="Passionate Full-Stack Developer interested in scalable web applications and AI systems.",
        skills="Python, Flask, JavaScript, SQL, React, Git, HTML/CSS"
    )
    s1.set_password("student123")

    s2 = Student(
        name="Jane Smith",
        email="jane.smith@univ.edu",
        phone="+1 (555) 345-6789",
        branch="Information Technology",
        cgpa=9.2,
        grad_year=2026,
        bio="Data Enthusiast & Backend Specialist with expertise in Cloud Native architectures.",
        skills="Java, Spring Boot, Python, PostgreSQL, AWS, Docker"
    )
    s2.set_password("student123")

    s3 = Student(
        name="Alex Vance",
        email="alex.vance@univ.edu",
        phone="+1 (555) 456-7890",
        branch="Electronics",
        cgpa=7.9,
        grad_year=2026,
        bio="Hardware & Embedded Systems Engineer keen on IoT and Signal Processing.",
        skills="C++, Embedded C, Microcontrollers, MATLAB, IoT, Python"
    )
    s3.set_password("student123")

    s4 = Student(
        name="Emily Clarke",
        email="emily.clarke@univ.edu",
        phone="+1 (555) 567-8901",
        branch="Mechanical",
        cgpa=8.4,
        grad_year=2026,
        bio="Robotics and Automotive enthusiast with strong CAD and simulations background.",
        skills="AutoCAD, SolidWorks, Python, Mechatronics, Finite Element Analysis"
    )
    s4.set_password("student123")

    db.session.add_all([s1, s2, s3, s4])
    db.session.commit()

    # 3. Companies
    c1 = Company(
        name="TechCorp Global",
        industry="Software & Enterprise Cloud",
        location="San Francisco, CA (Remote)",
        website="https://techcorp.example.com",
        contact_email="careers@techcorp.example.com",
        description="TechCorp Global builds enterprise SaaS applications serving millions of active users daily."
    )

    c2 = Company(
        name="DataPulse AI",
        industry="Artificial Intelligence & Analytics",
        location="New York, NY",
        website="https://datapulse.example.com",
        contact_email="jobs@datapulse.example.com",
        description="Leading AI research laboratory specializing in generative modeling and real-time data pipelines."
    )

    c3 = Company(
        name="Nexus Systems",
        industry="Cloud Infrastructure & Cyber Security",
        location="Austin, TX",
        website="https://nexussystems.example.com",
        contact_email="recruiting@nexussystems.example.com",
        description="Next-generation cloud infrastructure platform providing high-performance zero-trust security."
    )

    c4 = Company(
        name="Innovate Financial",
        industry="FinTech & Digital Payments",
        location="Boston, MA",
        website="https://innovatefin.example.com",
        contact_email="hr@innovatefin.example.com",
        description="Pioneering decentralized banking solutions, quantitative trading models, and fast payment rails."
    )

    db.session.add_all([c1, c2, c3, c4])
    db.session.commit()

    # 4. Jobs
    j1 = Job(
        company_id=c1.id,
        title="Associate Software Engineer",
        description="Join our core engineering team to build scalable microservices and high-throughput web backends.",
        requirements="Proficiency in Python/Java, understanding of REST APIs, relational databases, and modern git workflows.",
        job_type="Full-time",
        salary_package="$95,000 / yr",
        location="San Francisco, CA",
        min_cgpa=7.5,
        eligible_branches="Computer Science,Information Technology",
        deadline=datetime.utcnow() + timedelta(days=25),
        is_active=True
    )

    j2 = Job(
        company_id=c2.id,
        title="Data Science & ML Intern",
        description="Work alongside senior researchers training large language models and building data analytics pipelines.",
        requirements="Strong mathematical foundation, experience with Python (Pandas, NumPy, Scikit-learn) and SQL.",
        job_type="Internship",
        salary_package="$40 / hr",
        location="New York, NY",
        min_cgpa=8.0,
        eligible_branches="All",
        deadline=datetime.utcnow() + timedelta(days=18),
        is_active=True
    )

    j3 = Job(
        company_id=c3.id,
        title="Cloud Operations Engineer",
        description="Maintain critical cloud infrastructure, monitor system uptime, and automate deployment scripts.",
        requirements="Familiarity with Linux, Bash, Docker, AWS fundamentals, and network architecture.",
        job_type="Full-time",
        salary_package="$88,000 / yr",
        location="Austin, TX",
        min_cgpa=7.0,
        eligible_branches="Computer Science,Information Technology,Electronics",
        deadline=datetime.utcnow() + timedelta(days=30),
        is_active=True
    )

    j4 = Job(
        company_id=c4.id,
        title="FinTech Graduate Analyst",
        description="Analyze financial datasets, design algorithm workflows, and evaluate risk mitigation strategies.",
        requirements="Analytical mindset, problem-solving skills, basic programming in Python or R, strong communication.",
        job_type="Full-time",
        salary_package="$92,000 / yr",
        location="Boston, MA",
        min_cgpa=7.5,
        eligible_branches="All",
        deadline=datetime.utcnow() + timedelta(days=15),
        is_active=True
    )

    db.session.add_all([j1, j2, j3, j4])
    db.session.commit()

    # 5. Applications
    a1 = Application(
        job_id=j1.id,
        student_id=s1.id,
        cover_note="I am very excited about TechCorp's mission in cloud software and believe my experience in Flask and Python aligns closely.",
        status="Interview Scheduled",
        remarks="Candidate passed resume screening. Scheduled for Technical Round 1."
    )

    a2 = Application(
        job_id=j2.id,
        student_id=s2.id,
        cover_note="Extremely passionate about ML algorithms and big data pipelines.",
        status="Shortlisted",
        remarks="Impressive CGPA (9.2) and cloud projects."
    )

    a3 = Application(
        job_id=j3.id,
        student_id=s3.id,
        cover_note="Strong interest in embedded computing and cloud server communications.",
        status="Applied",
        remarks="Application received."
    )

    a4 = Application(
        job_id=j4.id,
        student_id=s4.id,
        cover_note="Interested in applying quantitative analysis to financial technologies.",
        status="Selected",
        remarks="Passed final HR round! Offer letter extended."
    )

    db.session.add_all([a1, a2, a3, a4])
    db.session.commit()

    # 6. Interview
    i1 = Interview(
        application_id=a1.id,
        round_name="Technical Round 1 - Data Structures & Algorithms",
        interview_date=(datetime.utcnow() + timedelta(days=3)).strftime("%Y-%m-%d"),
        interview_time="14:00",
        mode="Online",
        location_or_link="https://meet.google.com/abc-defg-hij",
        instructions="Please join 5 minutes before the scheduled time with your video camera enabled and IDE ready.",
        status="Scheduled"
    )

    db.session.add(i1)
    db.session.commit()

    print("Sample data seeded successfully!")
