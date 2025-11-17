import cv2
import os

cascade_path = 'haarcascade/haarcascade_frontalface_default.xml'
if not os.path.exists(cascade_path):
    raise IOError(f"Cannot find {cascade_path}. Please check the path.")

face_cascade = cv2.CascadeClassifier(cascade_path)
if face_cascade.empty():
    raise IOError(f"Cannot load {cascade_path}. Check the file content.")

cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    if not ret:
        print("Failed to grab frame from webcam.")
        break

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, 1.1, 4)

    for (x, y, w, h) in faces:
        cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)

    cv2.imshow('Face Detection', frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()