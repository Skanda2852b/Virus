import cv2
import numpy as np
from datetime import datetime, date
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from extensions import db
from models import Student, Attendance
from face_utils import load_recognizer, recognize_face

attendance_bp = Blueprint('attendance', __name__)

@attendance_bp.route('/start_session', methods=['GET', 'POST'])
@login_required
def start_session():
    if current_user.role != 'teacher':
        flash('Unauthorized')
        return redirect(url_for('auth.dashboard'))
    teacher = current_user.teacher_profile
    students = teacher.students
    if request.method == 'POST':
        selected_date = datetime.strptime(request.form['date'], '%Y-%m-%d').date()
        subject = request.form['subject'].strip()
        if not subject:
            flash('Subject is required.')
            return redirect(url_for('attendance.start_session'))
        # Mark all absent initially for this subject and date
        for student in students:
            att = Attendance.query.filter_by(student_id=student.id, date=selected_date, subject=subject).first()
            if not att:
                att = Attendance(student_id=student.id, date=selected_date, subject=subject, status='Absent', marked_by='system')
                db.session.add(att)
        db.session.commit()
        # Store subject in session for the camera page
        from flask import session
        session['attendance_subject'] = subject
        session['attendance_date'] = selected_date.isoformat()
        return render_template('camera_mark.html', students=students, date=selected_date, subject=subject)
    return render_template('start_attendance.html', students=students)

@attendance_bp.route('/mark_present', methods=['POST'])
@login_required
def mark_present():
    if current_user.role != 'teacher':
        return jsonify({'success': False, 'error': 'Unauthorized'})
    date_str = request.form.get('date')
    # Get subject from session (set during start_session)
    from flask import session
    subject = session.get('attendance_subject', 'General')
    if 'image' not in request.files:
        return jsonify({'success': False})
    file = request.files['image']
    img_array = np.frombuffer(file.read(), np.uint8)
    frame = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
    recognizer, label_map = load_recognizer()
    if recognizer is None:
        return jsonify({'success': False})
    results = recognize_face(frame, recognizer, label_map)
    for student, conf, _ in results:
        if student:
            att_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            att = Attendance.query.filter_by(student_id=student.id, date=att_date, subject=subject).first()
            if att and att.status != 'Present':
                att.status = 'Present'
                att.marked_by = 'system'
                db.session.commit()
                return jsonify({'success': True, 'usn': student.usn, 'name': student.user.full_name})
    return jsonify({'success': False})

@attendance_bp.route('/edit_attendance', methods=['GET', 'POST'])
@login_required
def edit_attendance():
    if current_user.role != 'teacher':
        flash('Unauthorized')
        return redirect(url_for('auth.dashboard'))
    teacher = current_user.teacher_profile
    students = teacher.students
    student_ids = [s.id for s in students]
    
    # Get filter parameters
    filter_date = request.args.get('filter_date', '')
    filter_subject = request.args.get('filter_subject', '')
    
    query = Attendance.query.filter(Attendance.student_id.in_(student_ids))
    if filter_date:
        try:
            filter_date_obj = datetime.strptime(filter_date, '%Y-%m-%d').date()
            query = query.filter(Attendance.date == filter_date_obj)
        except:
            pass
    if filter_subject:
        query = query.filter(Attendance.subject.ilike(f'%{filter_subject}%'))
    
    attendances = query.order_by(Attendance.date.desc(), Attendance.subject).all()
    
    if request.method == 'POST':
        attendance_id = request.form['attendance_id']
        new_status = request.form['status']
        att = Attendance.query.get(attendance_id)
        if att and att.student_id in student_ids:
            att.status = new_status
            att.marked_by = 'teacher'
            att.edited_by_teacher = True
            db.session.commit()
            flash('Attendance updated')
        return redirect(url_for('attendance.edit_attendance', filter_date=filter_date, filter_subject=filter_subject))
    
    # Get distinct subjects for filter dropdown (from this teacher's attendances)
    subjects = db.session.query(Attendance.subject).filter(Attendance.student_id.in_(student_ids)).distinct().all()
    subjects = [s[0] for s in subjects]
    
    return render_template('edit_attendance.html', attendances=attendances, 
                           filter_date=filter_date, filter_subject=filter_subject,
                           subjects=subjects)