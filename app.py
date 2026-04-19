from flask import Flask
from extensions import db, login_manager, mail

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'your-secret-key-change-in-production'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///virus.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    app.config['MAIL_SERVER'] = 'smtp.gmail.com'
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USERNAME'] = 'your-email@gmail.com'
    app.config['MAIL_PASSWORD'] = 'your-app-password'
    
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    mail.init_app(app)
    
    from auth import auth_bp
    from admin_routes import admin_bp
    from teacher_routes import teacher_bp
    from student_routes import student_bp
    from attendance_routes import attendance_bp
    from behavior_routes import behavior_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(teacher_bp, url_prefix='/teacher')
    app.register_blueprint(student_bp, url_prefix='/student')
    app.register_blueprint(attendance_bp, url_prefix='/attendance')
    app.register_blueprint(behavior_bp, url_prefix='/behavior')
    
    with app.app_context():
        from models import User
        db.create_all()
        if not User.query.filter_by(role='admin').first():
            admin = User(username='admin', email='admin@school.com', role='admin', full_name='Admin')
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            print("Default admin created: username=admin, password=admin123")
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)