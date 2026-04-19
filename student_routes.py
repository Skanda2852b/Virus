from flask import Blueprint, render_template, flash, redirect, url_for
from flask_login import login_required, current_user
from models import Attendance, BehaviorLog

student_bp = Blueprint('student', __name__)

@student_bp.route('/dashboard')
@login_required
def student_dashboard():
    if current_user.role != 'student':
        flash('Unauthorized')
        return redirect(url_for('auth.dashboard'))
    student = current_user.student_profile
    attendances = Attendance.query.filter_by(student_id=student.id).order_by(Attendance.date.desc()).all()
    behaviors = BehaviorLog.query.filter_by(student_id=student.id).order_by(BehaviorLog.timestamp.desc()).all()
    return render_template('student_dashboard.html', attendances=attendances, behaviors=behaviors)