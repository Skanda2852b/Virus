import cv2
import numpy as np
import time
from ultralytics import YOLO

# ---------- YOLO model for phone ----------
phone_model = None
try:
    phone_model = YOLO('yolov8n.pt')
    print("✅ YOLO model loaded. Phone detection enabled.")
except Exception as e:
    print(f"❌ YOLO model failed: {e}. Phone detection disabled.")

# ---------- Face & eye cascades for sleep ----------
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
eye_cascade  = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')

# ---------- State storage (per teacher) ----------
sleep_state = {}
phone_state = {}


def detect_sleeping_state(frame, teacher_id, required_seconds=5):
    """
    Returns (is_sleeping_now, alert_triggered)
    Eyes-closed timer increments only when face is found AND fewer than 2 eyes detected.
    A grace buffer of 2 consecutive open-eye frames is required before resetting,
    preventing a single noisy frame from resetting a valid sleep timer.
    """
    if teacher_id not in sleep_state:
        sleep_state[teacher_id] = {
            'start_time': None,
            'alerted': False,
            'open_frame_count': 0   # grace buffer: how many consecutive open frames seen
        }

    state = sleep_state[teacher_id]
    now   = time.time()

    gray  = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    # equalizeHist improves eye detection under varying lighting
    gray  = cv2.equalizeHist(gray)

    faces = face_cascade.detectMultiScale(
        gray,
        scaleFactor=1.1,
        minNeighbors=5,
        minSize=(80, 80)
    )

    if len(faces) == 0:
        # No face visible — do not reset timer (person may have briefly looked away)
        # but do not increment either
        return False, False

    # Use the largest detected face
    (x, y, w, h) = max(faces, key=lambda f: f[2] * f[3])

    # Only examine the upper 60% of the face for eyes (avoids mouth/nose false hits)
    roi_gray = gray[y: y + int(h * 0.6), x: x + w]

    eyes = eye_cascade.detectMultiScale(
        roi_gray,
        scaleFactor=1.1,
        minNeighbors=3,   # lowered from 6 — less strict, catches real eyes reliably
        minSize=(20, 20),
        maxSize=(80, 80)  # ignore huge blobs falsely classified as eyes
    )

    eyes_open = len(eyes) >= 2

    if eyes_open:
        state['open_frame_count'] += 1
        # Only reset the sleep timer after 2 consecutive open-eye frames (grace buffer)
        if state['open_frame_count'] >= 2:
            state['start_time'] = None
            state['alerted']    = False
        return False, False
    else:
        # Eyes closed (or only 0–1 eye detected)
        state['open_frame_count'] = 0   # reset grace buffer

        if state['start_time'] is None:
            state['start_time'] = now

        elapsed = now - state['start_time']

        if elapsed >= required_seconds:
            if not state['alerted']:
                state['alerted'] = True
                print(f"[SLEEP] Alert triggered after {elapsed:.1f}s of continuous eye closure")
                return True, True   # alert fires once
            return True, False      # still sleeping, alert already sent
        else:
            return False, False     # not long enough yet


def detect_phone_state(frame, teacher_id, required_seconds=10):
    """
    Returns (phone_visible_now, alert_triggered)
    Uses a miss-tolerance counter: up to 3 consecutive frames without detection
    are forgiven before the timer resets. This prevents flickering detections
    from resetting a valid phone-use timer.
    """
    if phone_model is None:
        return False, False

    if teacher_id not in phone_state:
        phone_state[teacher_id] = {
            'start_time': None,
            'alerted': False,
            'miss_count': 0   # how many consecutive frames phone was NOT detected
        }

    state = phone_state[teacher_id]
    now   = time.time()

    # Always resize to exactly 640px on the longer side for reliable YOLO inference
    h, w  = frame.shape[:2]
    scale = 640 / max(h, w)
    if scale < 1.0:
        resized = cv2.resize(frame, (int(w * scale), int(h * scale)))
    else:
        resized = frame

    phone_detected = False
    try:
        results = phone_model(resized, verbose=False)
        for r in results:
            if r.boxes is None:
                continue
            for box in r.boxes:
                cls  = int(box.cls[0])
                conf = float(box.conf[0])
                # COCO class 67 = cell phone; lowered threshold to 0.25 for yolov8n
                if cls == 67 and conf > 0.15:
                    phone_detected = True
                    print(f"[PHONE] Detected conf={conf:.2f}")
                    break
            if phone_detected:
                break
    except Exception as e:
        print(f"[PHONE] Inference error: {e}")
        return False, False

    if phone_detected:
        state['miss_count'] = 0   # reset miss counter on any positive detection

        if state['start_time'] is None:
            state['start_time'] = now

        elapsed = now - state['start_time']
        print(f"[PHONE] Timer: {elapsed:.1f}s / {required_seconds}s")

        if elapsed >= required_seconds:
            if not state['alerted']:
                state['alerted'] = True
                print(f"[PHONE] Alert triggered after {elapsed:.1f}s of continuous detection")
                return True, True   # alert fires once
            return True, False      # still detected, alert already sent
        else:
            return False, False     # detected but not long enough yet

    else:
        # Phone not visible this frame
        state['miss_count'] += 1

        # Tolerate up to 3 missed frames before resetting the timer
        # (handles YOLO flickering between frames)
        if state['miss_count'] > 3:
            state['start_time'] = None
            state['alerted']    = False

        return False, False