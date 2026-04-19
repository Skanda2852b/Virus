from extensions import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # admin, teacher, student
    full_name = db.Column(db.String(100))
    parent_email = db.Column(db.String(120))
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    teacher_profile = db.relationship('Teacher', backref='user', uselist=False)
    student_profile = db.relationship('Student', backref='user', uselist=False)

class Teacher(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    department = db.Column(db.String(100))
    students = db.relationship('Student', backref='teacher', lazy=True)

class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    usn = db.Column(db.String(20), unique=True, nullable=False)
    class_name = db.Column(db.String(50))   # e.g., "5A", "10B"
    department = db.Column(db.String(100))  # NEW: e.g., "Computer Science"
    section = db.Column(db.String(10))      # NEW: e.g., "A", "B", "C"
    teacher_id = db.Column(db.Integer, db.ForeignKey('teacher.id'))
    
    attendances = db.relationship('Attendance', backref='student', lazy=True)
    behaviors = db.relationship('BehaviorLog', backref='student', lazy=True)

class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    subject = db.Column(db.String(100), nullable=False, default='General')
    status = db.Column(db.String(10), default='Absent')
    marked_by = db.Column(db.String(20), default='system')
    edited_by_teacher = db.Column(db.Boolean, default=False)
    
    __table_args__ = (db.UniqueConstraint('student_id', 'date', 'subject', name='unique_attendance'),)

class BehaviorLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False)
    behavior_type = db.Column(db.String(20))
    alert_sent = db.Column(db.Boolean, default=False)