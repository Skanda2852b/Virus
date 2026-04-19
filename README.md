# Virus Attendance System (Flask Web App)

## Features
- Face recognition attendance with auto-marking
- Teacher dashboard to edit attendance
- Behavior monitoring (sleeping/phone detection) with email alerts to parents
- Bulk student upload via CSV
- Role-based login (Admin, Teacher, Student)

## Setup
1. Install Python 3.8+
2. Install dependencies: pip install -r requirements.txt
3. Download MobileNet SSD model files (see below)
4. Run: python app.py
5. Open browser at http://127.0.0.1:5000
6. Default admin login: dmin / dmin123

## MobileNet SSD for phone detection
Download these two files and place them in the project root:
- [MobileNetSSD_deploy.caffemodel](https://github.com/chuanqi305/MobileNet-SSD/raw/master/MobileNetSSD_deploy.caffemodel)
- [MobileNetSSD_deploy.prototxt](https://github.com/chuanqi305/MobileNet-SSD/raw/master/MobileNetSSD_deploy.prototxt)

## Folder Structure
- /dataset – stores face images of students
- /models – stores trained LBPH face recognizer
- /templates – HTML files
- /static – CSS/JS files (create if needed)
- /uploads – for CSV uploads
