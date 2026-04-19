import cv2
import os
import numpy as np
import json
from models import Student

MODEL_PATH = 'models/trained_model.yml'
LABEL_MAP_PATH = 'models/label_map.json'
CASCADE_PATH = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'

def train_model():
    """Trains LBPH model using images from dataset/ subfolders."""
    if not os.path.exists('dataset'):
        print("No dataset folder found")
        return None, None
    faces = []
    labels = []
    label_map = {}
    current_label = 0
    
    # Walk through all subfolders in dataset/
    for folder_name in os.listdir('dataset'):
        folder_path = os.path.join('dataset', folder_name)
        if not os.path.isdir(folder_path):
            continue
        # Extract USN from folder name (format: USN_Name)
        usn = folder_name.split('_')[0]
        if usn not in label_map:
            label_map[usn] = current_label
            current_label += 1
        # Load all .jpg images in this folder
        for filename in os.listdir(folder_path):
            if filename.endswith('.jpg'):
                img_path = os.path.join(folder_path, filename)
                img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
                if img is not None:
                    faces.append(img)
                    labels.append(label_map[usn])
    
    if len(faces) == 0:
        print("No face images found in dataset subfolders")
        return None, None
    recognizer = cv2.face.LBPHFaceRecognizer_create()
    recognizer.train(faces, np.array(labels))
    os.makedirs('models', exist_ok=True)
    recognizer.save(MODEL_PATH)
    with open(LABEL_MAP_PATH, 'w') as f:
        json.dump(label_map, f)
    label_to_usn = {v: k for k, v in label_map.items()}
    print(f"Model trained with {len(faces)} images from {len(label_map)} students")
    return recognizer, label_to_usn

def load_recognizer():
    if not os.path.exists(MODEL_PATH):
        return train_model()
    recognizer = cv2.face.LBPHFaceRecognizer_create()
    recognizer.read(MODEL_PATH)
    if os.path.exists(LABEL_MAP_PATH):
        with open(LABEL_MAP_PATH, 'r') as f:
            label_map = json.load(f)
        label_to_usn = {int(v): k for k, v in label_map.items()}
    else:
        # Fallback: query database and use all students
        students = Student.query.all()
        label_to_usn = {idx: s.usn for idx, s in enumerate(students)}
    return recognizer, label_to_usn

def recognize_face(frame, recognizer, label_map, threshold=80):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    face_cascade = cv2.CascadeClassifier(CASCADE_PATH)
    faces = face_cascade.detectMultiScale(gray, 1.3, 5)
    result = []
    for (x,y,w,h) in faces:
        roi = gray[y:y+h, x:x+w]
        label, confidence = recognizer.predict(roi)
        if confidence < threshold:
            usn = label_map.get(label, None)
            if usn:
                student = Student.query.filter_by(usn=usn).first()
                result.append((student, confidence, (x,y,w,h)))
            else:
                result.append((None, confidence, (x,y,w,h)))
        else:
            result.append((None, confidence, (x,y,w,h)))
    return result