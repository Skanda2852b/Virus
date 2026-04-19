from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from extensions import db
from models import User, Teacher

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/dashboard')
@login_required
def admin_dashboard():
    if current_user.role != 'admin':
        flash('Access denied')
        return redirect(url_for('auth.dashboard'))
    teachers = User.query.filter_by(role='teacher').all()
    return render_template('admin_dashboard.html', teachers=teachers)

@admin_bp.route('/add_teacher', methods=['POST'])
@login_required
def add_teacher():
    if current_user.role != 'admin':
        return 'Unauthorized', 403
    username = request.form['username']
    email = request.form['email']
    full_name = request.form['full_name']
    department = request.form['department']
    password = request.form['password']
    if User.query.filter_by(username=username).first():
        flash('Username already exists')
        return redirect(url_for('admin.admin_dashboard'))
    user = User(username=username, email=email, role='teacher', full_name=full_name)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    teacher = Teacher(user_id=user.id, department=department)
    db.session.add(teacher)
    db.session.commit()
    flash('Teacher added successfully')
    return redirect(url_for('admin.admin_dashboard'))