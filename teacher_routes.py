from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from extensions import db
from models import User, Student, Teacher, Attendance, BehaviorLog
import pandas as pd
import os
import cv2
import numpy as np
import shutil

teacher_bp = Blueprint('teacher', __name__)

def has_face_samples(usn):
    if not os.path.exists('dataset'):
        return False
    for item in os.listdir('dataset'):
        if os.path.isdir(os.path.join('dataset', item)) and item.startswith(usn):
            folder_path = os.path.join('dataset', item)
            for f in os.listdir(folder_path):
                if f.endswith('.jpg'):
                    return True
    return False

@teacher_bp.route('/dashboard')
@login_required
def teacher_dashboard():
    if current_user.role != 'teacher':
        flash('Unauthorized')
        return redirect(url_for('auth.dashboard'))
    teacher = current_user.teacher_profile
    students = teacher.students
    for s in students:
        s.has_faces = has_face_samples(s.usn)
    return render_template('teacher_dashboard.html', students=students)

@teacher_bp.route('/add_students', methods=['GET', 'POST'])
@login_required
def add_students():
    if current_user.role != 'teacher':
        flash('Unauthorized')
        return redirect(url_for('auth.dashboard'))
    teacher = current_user.teacher_profile
    
    if request.method == 'POST':
        # Bulk CSV upload
        if 'csv_file' in request.files:
            file = request.files['csv_file']
            if file.filename.endswith('.csv'):
                df = pd.read_csv(file)
                added = 0
                skipped_dup_usn = []
                skipped_dup_email = []
                skipped_dup_username = []
                
                # Expected CSV columns: name, usn, class_name, department, section, parent_email
                for _, row in df.iterrows():
                    name = row['name']
                    usn = row['usn']
                    class_name = row.get('class_name', '')
                    department = row.get('department', '')
                    section = row.get('section', '')
                    parent_email = row['parent_email']
                    
                    if Student.query.filter_by(usn=usn).first():
                        skipped_dup_usn.append(usn)
                        continue
                    if User.query.filter_by(username=usn).first():
                        skipped_dup_username.append(usn)
                        continue
                    if User.query.filter_by(email=parent_email).first():
                        skipped_dup_email.append(parent_email)
                        continue
                    
                    user = User(username=usn, email=parent_email, role='student', 
                                full_name=name, parent_email=parent_email)
                    user.set_password(usn)
                    db.session.add(user)
                    db.session.flush()
                    student = Student(user_id=user.id, usn=usn, class_name=class_name,
                                      department=department, section=section, teacher_id=teacher.id)
                    db.session.add(student)
                    added += 1
                
                db.session.commit()
                
                if added > 0:
                    flash(f'{added} students added successfully. Default password is their USN.')
                if skipped_dup_usn:
                    flash(f'Skipped (USN already exists as student): {", ".join(skipped_dup_usn)}', 'warning')
                if skipped_dup_username:
                    flash(f'Skipped (USN already used as username): {", ".join(skipped_dup_username)}', 'warning')
                if skipped_dup_email:
                    flash(f'Skipped (email already registered): {", ".join(skipped_dup_email)}', 'warning')
                    
                return redirect(url_for('teacher.teacher_dashboard'))
        
        # Single student addition
        name = request.form['name']
        usn = request.form['usn']
        class_name = request.form['class_name']
        department = request.form['department']
        section = request.form['section']
        parent_email = request.form['parent_email']
        
        if Student.query.filter_by(usn=usn).first():
            flash('USN already exists as a student.')
        elif User.query.filter_by(username=usn).first():
            flash('USN already used as a username (by another user).')
        elif User.query.filter_by(email=parent_email).first():
            flash('Email already registered. Each student must have a unique email.')
        else:
            user = User(username=usn, email=parent_email, role='student', 
                        full_name=name, parent_email=parent_email)
            user.set_password(usn)
            db.session.add(user)
            db.session.flush()
            student = Student(user_id=user.id, usn=usn, class_name=class_name,
                              department=department, section=section, teacher_id=teacher.id)
            db.session.add(student)
            db.session.commit()
            flash(f'Student {name} added. Default password is USN: {usn}')
        
        return redirect(url_for('teacher.add_students'))
    
    return render_template('add_students.html')

@teacher_bp.route('/capture_faces/<int:student_id>', methods=['GET', 'POST'])
@login_required
def capture_faces(student_id):
    if current_user.role != 'teacher':
        flash('Unauthorized')
        return redirect(url_for('auth.dashboard'))
    student = Student.query.get_or_404(student_id)
    teacher = current_user.teacher_profile
    if student.teacher_id != teacher.id:
        flash('You can only capture faces for your own students.')
        return redirect(url_for('teacher.teacher_dashboard'))
    return render_template('capture_faces.html', student=student)

@teacher_bp.route('/save_face_image', methods=['POST'])
@login_required
def save_face_image():
    if current_user.role != 'teacher':
        return jsonify({'success': False, 'error': 'Unauthorized'})
    student_id = request.form.get('student_id')
    student = Student.query.get_or_404(student_id)
    teacher = current_user.teacher_profile
    if student.teacher_id != teacher.id:
        return jsonify({'success': False, 'error': 'Not your student'})
    if 'image' not in request.files:
        return jsonify({'success': False, 'error': 'No image'})
    file = request.files['image']
    img_array = np.frombuffer(file.read(), np.uint8)
    frame = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, 1.3, 5)
    if len(faces) == 0:
        return jsonify({'success': False, 'error': 'No face detected'})
    (x, y, w, h) = faces[0]
    face_roi = gray[y:y+h, x:x+w]
    folder_name = f"{student.usn}_{student.user.full_name.replace(' ', '_')}"
    folder_path = os.path.join('dataset', folder_name)
    os.makedirs(folder_path, exist_ok=True)
    existing = [f for f in os.listdir(folder_path) if f.endswith('.jpg')]
    count = len(existing) + 1
    filename = os.path.join(folder_path, f"{count}.jpg")
    cv2.imwrite(filename, face_roi)
    return jsonify({'success': True, 'count': count})

@teacher_bp.route('/delete_student/<int:student_id>', methods=['POST'])
@login_required
def delete_student(student_id):
    if current_user.role != 'teacher':
        flash('Unauthorized')
        return redirect(url_for('auth.dashboard'))
    student = Student.query.get_or_404(student_id)
    teacher = current_user.teacher_profile
    if student.teacher_id != teacher.id:
        flash('You can only delete your own students.')
        return redirect(url_for('teacher.teacher_dashboard'))
    folder_name = f"{student.usn}_{student.user.full_name.replace(' ', '_')}"
    folder_path = os.path.join('dataset', folder_name)
    if os.path.exists(folder_path):
        shutil.rmtree(folder_path)
    BehaviorLog.query.filter_by(student_id=student.id).delete()
    Attendance.query.filter_by(student_id=student.id).delete()
    user = student.user
    db.session.delete(student)
    db.session.delete(user)
    db.session.commit()
    flash(f'Student {student.user.full_name} ({student.usn}) removed successfully.')
    return redirect(url_for('teacher.teacher_dashboard'))

@teacher_bp.route('/train_model')
@login_required
def train_model():
    if current_user.role != 'teacher':
        flash('Unauthorized')
        return redirect(url_for('auth.dashboard'))
    from face_utils import train_model
    recognizer, label_map = train_model()
    if recognizer:
        flash('Model trained successfully!', 'success')
    else:
        flash('No face images found. Please capture faces first.', 'danger')
    return redirect(url_for('teacher.teacher_dashboard'))