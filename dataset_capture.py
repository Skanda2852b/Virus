import cv2
import os
import time

# Create 'dataset' folder if it doesn't exist
if not os.path.exists('dataset'):
    os.makedirs('dataset')

# Get user input for Name and USN
name = input("Enter student's Name: ")
usn = input("Enter student's USN: ")

# Load the Haar Cascade for face detection
# Using cv2.data.haarcascades automatically finds the file from the installed opencv package
cascade_path = os.path.join(cv2.data.haarcascades, 'haarcascade_frontalface_default.xml')
face_cascade = cv2.CascadeClassifier(cascade_path)

# Start webcam
cap = cv2.VideoCapture(0)

print("[INFO] Starting video stream for data capture...")
print("[INFO] Please look at the camera. Capturing 100 images...")

count = 0

while True:
    ret, frame = cap.read()
    if not ret:
        print("[ERROR] Failed to capture image from camera.")
        break
        
    # Convert frame to grayscale (Haar Cascades work better on grayscale)
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
    # Detect faces
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.3, minNeighbors=5)
    
    for (x, y, w, h) in faces:
        count += 1
        
        # Crop the face region from the grayscale image
        face_img = gray[y:y+h, x:x+w]
        
        # Save the captured face image in the 'dataset' folder
        # Filename format: name_usn_count.jpg
        file_name = f"dataset/{name}_{usn}_{count}.jpg"
        cv2.imwrite(file_name, face_img)
        
        # Draw a rectangle around the face to show the user
        cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 0, 0), 2)
        
        # Display the frame
        cv2.imshow('Capturing Face Data', frame)
        
        # Wait a little bit between captures to get diverse angles
        cv2.waitKey(100) 
        
    # Stop if we captured 100 images
    if count >= 100:
        break
        
    # Exit if user presses 'q'
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

print(f"[INFO] Successfully captured {count} images and saved them to the 'dataset' folder.")

# Cleanup
cap.release()
cv2.destroyAllWindows()
