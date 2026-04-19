from flask import Blueprint, render_template, flash, redirect, url_for, request, jsonify
from flask_login import login_required, current_user
from extensions import db, mail
from flask_mail import Message
from models import Student, BehaviorLog, Teacher
from behavior_utils import detect_sleeping_state, detect_phone_state
import cv2
import numpy as np
import base64
from datetime import datetime

behavior_bp = Blueprint('behavior', __name__)

@behavior_bp.route('/monitor')
@login_required
def monitor():
    if current_user.role != 'teacher':
        flash('Unauthorized')
        return redirect(url_for('auth.dashboard'))
    teacher = current_user.teacher_profile
    students = teacher.students
    return render_template('monitor_behavior.html', students=students)

def send_alert_email(student, behavior_type):
    if not student.user.parent_email:
        return
    try:
        msg = Message(
            f'Alert: {behavior_type} detected for {student.user.full_name}',
            sender='your-email@gmail.com',
            recipients=[student.user.parent_email]
        )
        msg.body = (f'Dear Parent,\n\nYour child {student.user.full_name} (USN: {student.usn}) '
                    f'was detected {behavior_type} during class at {datetime.now()}. '
                    f'Please discuss appropriate behavior.\n\nRegards,\nSchool System')
        mail.send(msg)
    except Exception as e:
        print(f"Email error: {e}")

@behavior_bp.route('/detect', methods=['POST'])
@login_required
def detect():
    if current_user.role != 'teacher':
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json()
    if not data or 'image' not in data:
        return jsonify({'error': 'No image'}), 400
    
    image_data = base64.b64decode(data['image'].split(',')[1])
    np_arr = np.frombuffer(image_data, np.uint8)
    frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    
    teacher_id = current_user.teacher_profile.id
    
    sleeping, sleep_alert = detect_sleeping_state(frame, teacher_id, required_seconds=5)
    phone, phone_alert = detect_phone_state(frame, teacher_id, required_seconds=10)
    
    teacher = current_user.teacher_profile
    student_list = teacher.students
    alert_sent = False
    alert_type = None
    
    if student_list and (sleep_alert or phone_alert):
        student = student_list[0]
        now = datetime.now()
        if sleep_alert:
            log = BehaviorLog(student_id=student.id, timestamp=now, behavior_type='sleeping', alert_sent=True)
            db.session.add(log)
            db.session.commit()
            send_alert_email(student, 'sleeping')
            alert_sent = True
            alert_type = 'sleeping'
        elif phone_alert:
            log = BehaviorLog(student_id=student.id, timestamp=now, behavior_type='phone', alert_sent=True)
            db.session.add(log)
            db.session.commit()
            send_alert_email(student, 'phone usage')
            alert_sent = True
            alert_type = 'phone'
    
    return jsonify({
        'sleeping': sleeping,
        'phone': phone,
        'alert_sent': alert_sent,
        'alert_type': alert_type
    })