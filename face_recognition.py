import cv2
import os
import numpy as np
import csv
from datetime import datetime

# Check if dataset exists
dataset_path = 'dataset'
if not os.path.exists(dataset_path):
    print("[ERROR] 'dataset' folder not found. Please run dataset_capture.py first.")
    exit()

print("[INFO] Training model with captured dataset. Please wait...")

faces = []
labels = []
student_name = "Unknown"
student_usn = ""
label_id = 1

# Iterate through images in the dataset folder
image_names = [f for f in os.listdir(dataset_path) if f.endswith('.jpg')]

if len(image_names) == 0:
    print("[ERROR] No images found in 'dataset'.")
    exit()

for image_name in image_names:
    img_path = os.path.join(dataset_path, image_name)
    img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
    
    if img is None:
        continue
        
    # Extract name and USN from the filename (e.g., Shriram_1JS23CS162_1.jpg)
    parts = image_name.split('_')
    if len(parts) >= 3:
        student_name = parts[0]
        student_usn = parts[1]
        
    faces.append(img)
    labels.append(label_id)

# Initialize and train LBPH Face Recognizer
recognizer = cv2.face.LBPHFaceRecognizer_create()
recognizer.train(faces, np.array(labels))
print(f"[INFO] Model trained successfully for {student_name} ({student_usn})!")

# Load Haar Cascade
cascade_path = os.path.join(cv2.data.haarcascades, 'haarcascade_frontalface_default.xml')
face_cascade = cv2.CascadeClassifier(cascade_path)

# Set to keep track of marked attendance in this session to prevent duplicates
attendance_marked = set()
attendance_file = "attendance.csv"

# Function to mark attendance
def mark_attendance(name, usn):
    # Only mark if not already marked in this session
    if name not in attendance_marked:
        now = datetime.now()
        date_str = now.strftime('%Y-%m-%d')
        time_str = now.strftime('%H:%M:%S')
        
        # Check if file exists to write headers
        file_exists = os.path.isfile(attendance_file)
        
        with open(attendance_file, mode='a', newline='') as file:
            writer = csv.writer(file)
            
            # Write headers if the file is newly created
            if not file_exists or os.stat(attendance_file).st_size == 0:
                writer.writerow(['Name', 'USN', 'Date', 'Time'])
                
            writer.writerow([name, usn, date_str, time_str])
            
        attendance_marked.add(name)
        print(f"Attendance marked for {name}")

print("[INFO] Starting webcam for face recognition. Press 'q' to exit.")
cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    if not ret:
        break
        
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    detected_faces = face_cascade.detectMultiScale(gray, scaleFactor=1.3, minNeighbors=5)
    
    for (x, y, w, h) in detected_faces:
        roi_gray = gray[y:y+h, x:x+w]
        
        # Predict the face
        label, confidence = recognizer.predict(roi_gray)
        
        # If confidence is good (< 80)
        if confidence < 80:
            color = (0, 255, 0) # GREEN for match
            text = f"{student_name} - {student_usn}"
            # Automatically mark attendance
            mark_attendance(student_name, student_usn)
        else:
            color = (0, 0, 255) # RED for mismatch
            text = "Unknown"
            
        cv2.rectangle(frame, (x, y), (x+w, y+h), color, 2)
        cv2.putText(frame, text, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
        
    cv2.imshow('Face Recognition Attendance System', frame)
    
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
        
cap.release()
cv2.destroyAllWindows()