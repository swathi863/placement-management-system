from models import db, Admin

def seed_database():
    """Ensures default Admin account exists. Does NOT create sample students, companies, or jobs."""
    if not Admin.query.first():
        print("Creating default Admin account...")
        admin = Admin(
            name="Placement Officer (Admin)",
            email="admin@placement.com"
        )
        admin.set_password("admin123")
        db.session.add(admin)
        db.session.commit()
        print("Default Admin account created successfully!")
    else:
        print("Admin account already exists. Skipping seed.")
