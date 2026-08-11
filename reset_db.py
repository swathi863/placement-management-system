import os
from app import app
from models import db, Student, Admin, Company, Job, Application, Interview

def reset_database():
    with app.app_context():
        print("Dropping all existing database tables...")
        db.drop_all()
        print("Recreating database tables...")
        db.create_all()

        print("Creating fresh default Admin account...")
        admin = Admin(
            name="Placement Officer (Admin)",
            email="admin@placement.com"
        )
        admin.set_password("admin123")
        db.session.add(admin)
        db.session.commit()

        print("\nDatabase reset complete!")
        print("----------------------------------------")
        print("Admin Login: admin@placement.com / admin123")
        print("All student accounts, companies, jobs, and applications have been cleared.")
        print("You can now register a fresh student account at http://127.0.0.1:5000/register !")

if __name__ == '__main__':
    reset_database()
