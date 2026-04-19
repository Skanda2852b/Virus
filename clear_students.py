import os
import shutil
from app import create_app
from extensions import db
from models import Student, User, Attendance, BehaviorLog

app = create_app()
with app.app_context():
    # Delete all students
    students = Student.query.all()
    for student in students:
        # Delete face image folder
        folder_name = f"{student.usn}_{student.user.full_name.replace(' ', '_')}"
        folder_path = os.path.join('dataset', folder_name)
        if os.path.exists(folder_path):
            shutil.rmtree(folder_path)
        # Delete behavior logs and attendance
        BehaviorLog.query.filter_by(student_id=student.id).delete()
        Attendance.query.filter_by(student_id=student.id).delete()
        # Delete the student record
        db.session.delete(student)
    db.session.commit()
    
    # Delete all users with role 'student'
    User.query.filter_by(role='student').delete()
    db.session.commit()
    
    print("All students, their face images, attendance, and behavior logs have been cleared.")