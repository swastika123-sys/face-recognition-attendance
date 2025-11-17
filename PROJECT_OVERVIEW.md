# Face Recognition Attendance System — Complete Process Overview

## 🎯 Project Purpose
An AI-powered Flask web application that **automates student attendance using real-time face recognition**. Teachers can mark attendance via webcam, manage students, view history, and export records.

---

## 🏗️ High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER INTERFACE (Browser)                  │
│  • Login/Register (Teacher & Student roles)                      │
│  • Realtime Webcam Feed (Face Detection & Recognition)           │
│  • Student Management (View, Edit, Delete)                       │
│  • Attendance History & Manual Entry                             │
│  • Settings & Help Pages                                         │
└────────────────────────┬────────────────────────────────────────┘
                         │ HTTP/JSON
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    FLASK BACKEND (app.py)                        │
│  • Session Management (Auth)                                     │
│  • Face Recognition Routes (/recognize, /detect_face)            │
│  • Student CRUD Operations                                       │
│  • Attendance Logging (DB + CSV backup)                          │
│  • Image Serving (/known_faces/<filename>)                       │
└────────────────────────┬────────────────────────────────────────┘
                         │
        ┌────────────────┼────────────────┐
        ▼                ▼                ▼
┌──────────────┐  ┌─────────────────┐  ┌────────────────┐
│   DeepFace   │  │   MySQL 8.0     │  │  File System   │
│   (FaceNet)  │  │  Database       │  │  known_faces/  │
│              │  │  - teachers     │  │  attendance.csv│
│ Extract Face │  │  - students     │  │                │
│ Embeddings   │  │  - attendance   │  │  Student images│
│              │  │                 │  │                │
└──────────────┘  └─────────────────┘  └────────────────┘
```

---

## 📊 Database Schema (MySQL)

### `teachers` Table
- **id** (INT, Primary Key)
- **username** (VARCHAR, Unique)
- **email** (VARCHAR, Unique)
- **password** (VARCHAR) — plaintext (for demo; hash in production)
- **created_at** (TIMESTAMP, Default: NOW)

### `students` Table
- **id** (INT, Primary Key)
- **username** (VARCHAR, Unique)
- **email** (VARCHAR, Unique)
- **serial_number** (VARCHAR, Unique) — e.g., "12" (for attendance marking)
- **phone** (VARCHAR) — 10 digits
- **image_path** (VARCHAR) — path to known_faces/<filename>
- **face_encoding** (TEXT) — serialized FaceNet embedding (128-dim numpy array as string)
- **created_at** (TIMESTAMP, Default: NOW)

### `attendance` Table
- **id** (INT, Primary Key)
- **student_id** (INT, Foreign Key → students)
- **timestamp** (TIMESTAMP, Default: NOW)
- **status** (ENUM: 'Present', 'Absent', 'Late')
- **method** (ENUM: 'Face Recognition', 'Manual')
- **teacher_id** (INT, Foreign Key → teachers)
- **notes** (TEXT) — optional remarks

---

## 🔄 Complete Workflow (Step-by-Step)

### **1. SETUP & INITIALIZATION**
```
a) Start Server
   └─ python app.py
   └─ Calls: init_db() → creates tables if missing
   └─ Calls: load_known_faces() → loads all student embeddings from DB into memory
   └─ Server listens on http://localhost:5001

b) Database Connection (db.py)
   └─ MySQL host='localhost', user='root', password='', database='face_project'
```

### **2. USER REGISTRATION**

#### **Teacher Registration**
```
User visits /register
  ├─ Fills: username, email, password, teacher_secret
  ├─ Validation: teacher_secret must be 'admin'
  └─ If valid:
      └─ INSERT INTO teachers (username, email, password)
      └─ Redirects to /login
```

#### **Student Registration** (Self-Service + Face Capture)
```
User visits /register
  ├─ Fills: username, email, serial_number, phone
  ├─ Provides: Face capture (canvas/webcam → base64 image)
  └─ If valid:
      ├─ Save image to known_faces/<serial_number>_<username>.png
      ├─ Extract embedding: extract_face_embedding(image)
      │   └─ Uses DeepFace.represent() with FaceNet model
      ├─ Check duplicate faces:
      │   └─ Load all existing face encodings from DB
      │   └─ Compare new embedding vs known embeddings
      │   └─ If distance < 3.0 (strict threshold) → reject as duplicate
      ├─ INSERT INTO students (..., face_encoding=serialized_embedding)
      ├─ Reload known faces into memory
      └─ Success: Student can now use face recognition
```

### **3. LOGIN**
```
User visits /login
  ├─ Fills: username, password
  ├─ Query: SELECT id, password FROM teachers WHERE username=?
  ├─ If match:
  │   └─ session['user'] = username
  │   └─ session['user_type'] = 'teacher'
  │   └─ session['user_id'] = teacher_id
  │   └─ Redirect to /dashboard
  └─ Else: Show error
```

### **4. REALTIME ATTENDANCE (Main Feature)**

#### **Webcam Detection & Recognition**
```
Teacher goes to /realtime page
  │
  ├─ JavaScript captures video frame (canvas) every ~500ms
  │
  ├─ Sends base64 image to /detect_face (POST, JSON)
  │   │
  │   └─ Backend /detect_face():
  │       ├─ Decode base64 → PIL Image → RGB numpy array
  │       ├─ Run DeepFace.extract_faces() → get face regions
  │       ├─ For each detected face:
  │       │   ├─ Extract embedding: extract_face_embedding()
  │       │   ├─ If logged in + known faces exist:
  │       │   │   └─ Compare embedding vs known embeddings (threshold=15.0)
  │       │   │   └─ If match: return face_name & status="registered"
  │       │   │   └─ Else: return status="unregistered"
  │       │   └─ Return: {x, y, width, height, name, display_name, status}
  │       └─ Response: {success: true, faces: [...], total_faces: N}
  │
  ├─ JavaScript draws bounding boxes on canvas + labels names
  │
  └─ When teacher clicks → capture attendance
      └─ Send image to /recognize (POST, JSON, requires login)
          │
          └─ Backend /recognize():
              ├─ Decode image → RGB array
              ├─ Extract embedding: extract_face_embedding()
              ├─ Check single face: If >1 face → error "Multiple faces"
              ├─ Compare vs known embeddings (threshold=15.0)
              ├─ If match:
              │   ├─ Extract serial_number from name
              │   ├─ Call mark_attendance(name):
              │   │   ├─ Write to attendance.csv (date, time, name)
              │   │   └─ INSERT INTO attendance (..., status='Present', method='Face Recognition')
              │   └─ Return: {success: true, recognized: true, message, student_info}
              └─ Else: {success: false, recognized: false, message: "Not recognized"}
```

### **5. STUDENT MANAGEMENT (CRUD)**

#### **Add Student (Teacher adds via form)**
```
/student page → "Add Student" form
  ├─ Inputs: serial_number, username, email, phone, photo (file upload)
  ├─ Process (same as registration):
  │   ├─ Save image to known_faces/
  │   ├─ Extract embedding
  │   └─ INSERT INTO students
  └─ Reload known faces
```

#### **View Student**
```
/view_student/<student_id>
  ├─ Query student from DB
  ├─ Serve image via /known_faces/<filename> route
  ├─ Show attendance history (last 10 records)
  └─ Display student info: name, email, phone, registration date
```

#### **Edit Student**
```
/edit_student/<student_id>
  ├─ GET: Load form with current data
  ├─ POST: Update username, email, phone
  │   └─ UPDATE students SET ... WHERE id=?
  └─ Note: Cannot change face (must delete & re-add)
```

#### **Delete Student**
```
/delete_student/<student_id> (POST)
  ├─ Get student info
  ├─ DELETE FROM students (cascades to attendance)
  ├─ Delete image file from known_faces/
  ├─ Reload known faces
  └─ Success message
```

### **6. ATTENDANCE MANAGEMENT**

#### **View Attendance**
```
/attendance page
  ├─ Query: SELECT attendance records + student names (LEFT JOIN)
  ├─ Display: date, time, student name, serial #, status, method, notes
  └─ Sort by timestamp DESC
```

#### **Manual Attendance** (Fallback)
```
Form on /attendance page
  ├─ Inputs: student_serial, status (Present/Absent/Late), notes
  ├─ Find student by serial: SELECT id FROM students WHERE serial_number=?
  ├─ If found:
  │   └─ INSERT INTO attendance (..., method='Manual', status=?, notes=?)
  └─ Redirect to /attendance
```

#### **Edit Attendance**
```
/edit_attendance/<attendance_id> (POST)
  ├─ Inputs: status, notes
  └─ UPDATE attendance SET status=?, notes=?, teacher_id=? WHERE id=?
```

#### **Delete Attendance**
```
/delete_attendance/<attendance_id> (POST)
  └─ DELETE FROM attendance WHERE id=?
```

---

## 🧠 Face Recognition Algorithm

### **Extract Embedding**
```python
def extract_face_embedding(image_array):
    # Input: RGB numpy array (H×W×3)
    result = DeepFace.represent(
        img_path=image_array,
        model_name='Facenet',           # 128-dim embeddings
        detector_backend='opencv',      # Face detection
        enforce_detection=False         # Lenient (allows edge cases)
    )
    # Output: 128-dim numpy vector
    return np.array(result[0]['embedding'])
```

### **Compare Faces**
```python
def compare_faces(known_embeddings, face_embedding, threshold=15.0):
    distances = []
    for known_emb in known_embeddings:
        # Euclidean (L2) distance
        dist = np.linalg.norm(known_emb - face_embedding)
        distances.append(dist)
    
    # Matches: indices where distance < threshold
    matches = [i for i, d in enumerate(distances) if d < threshold]
    return distances, matches
```

### **Thresholds**
- **Duplicate Detection (Registration)**: 3.0 — strict, prevents proxy/spoofing
- **Recognition (Attendance)**: 15.0 — lenient, tolerates lighting/pose variations

---

## 📁 File Structure

```
projectface.html/
├── app.py                          # Main Flask application
├── db.py                           # Database connection helper
├── requirements.txt                # Python dependencies
├── attendance.csv                  # Backup CSV log
│
├── known_faces/                    # Student face images
│   ├── 12_swas1.png
│   ├── 12_rudro.png
│   └── ...
│
├── static/
│   ├── 8090418-uhd_4096_2160_25fps.mp4  # Background video
│   └── realtime.js                      # Webcam JS
│
├── templates/                      # HTML templates
│   ├── index.html                  # Home page
│   ├── login.html                  # Login form
│   ├── register.html               # Registration form
│   ├── dashboard.html              # Teacher dashboard
│   ├── realtime.html               # Webcam attendance
│   ├── student.html                # Student list
│   ├── view_student.html           # Student profile
│   ├── edit_student.html           # Edit student
│   ├── attendance.html             # Attendance history
│   ├── CONTACT.HTML                # Contact page
│   ├── help.html                   # Help page
│   └── ...
│
└── venv-py311/                     # Virtual environment (Python 3.11)
```

---

## 🚀 How to Run

### **1. Setup Environment**
```bash
cd /Users/swastika/Desktop/projectface.html

# Activate venv (Python 3.11)
source venv-py311/bin/activate

# Verify packages
python --version  # Should be 3.11.x
pip show deepface flask  # Should show installed

# If missing, install:
pip install -r requirements.txt
```

### **2. Setup Database**
```bash
# Ensure MySQL is running
# Create database (if not exists):
mysql -u root -e "CREATE DATABASE IF NOT EXISTS face_project;"

# Tables auto-created when app starts (init_db() function)
```

### **3. Start Server**
```bash
python app.py

# Output:
# 🚀 Starting Flask application...
# 📍 Access the app at: http://localhost:5001
# 🔄 Auto-reload is ENABLED - app will restart when files change
```

### **4. Access in Browser**
- **Home**: http://localhost:5001/
- **Register**: http://localhost:5001/register
- **Login**: http://localhost:5001/login
- **Dashboard**: http://localhost:5001/dashboard (after login)

---

## 🔑 Key Features

| Feature | Details |
|---------|---------|
| **Face Recognition** | Real-time webcam → DeepFace/FaceNet embeddings → distance comparison |
| **Duplicate Detection** | Prevents same student from registering twice (strict threshold) |
| **Manual Attendance** | Fallback form if face recognition fails |
| **CSV Backup** | Attendance also logged to attendance.csv for offline access |
| **Student Management** | CRUD operations (add, view, edit, delete) |
| **Role-Based Access** | Teachers login, students self-register with face |
| **Futuristic UI** | Animated gradients, glassmorphism, hover effects, responsive design |
| **Image Serving** | `/known_faces/<filename>` route securely serves student photos |

---

## ⚙️ Tech Stack

| Component | Technology |
|-----------|-----------|
| **Backend** | Python 3.11, Flask |
| **AI/CV** | DeepFace (FaceNet embeddings), OpenCV, NumPy, Pillow |
| **Frontend** | HTML5, CSS3, JavaScript, Bootstrap 5, Canvas API |
| **Database** | MySQL 8.0 (mysql-connector-python) |
| **Environment** | Virtual environment (venv-py311), pip |

---

## 🎓 Common Viva Questions & Answers

**Q: What happens when a student registers?**  
A: Face image captured → embedding extracted (FaceNet) → compared against existing embeddings (threshold 3.0) for duplicates → if unique, saved to DB and image stored in known_faces/ folder.

**Q: How does attendance marking work?**  
A: Teacher captures frame from webcam → extracts embedding → compares against all known embeddings (threshold 15.0) → if match found, marks present in DB and CSV.

**Q: Why two different thresholds?**  
A: Duplicate detection (3.0) is strict to prevent fraud. Attendance recognition (15.0) is lenient to tolerate lighting/pose variations in real classroom conditions.

**Q: What if multiple faces detected?**  
A: System blocks recognition and prompts "Multiple faces detected. Ensure only one person in frame."

**Q: How are embeddings stored?**  
A: As serialized numpy arrays (stringified lists) in MySQL students.face_encoding column. Loaded into memory at startup for fast comparison.

**Q: What if face recognition fails?**  
A: Teacher can manually enter student serial # and mark attendance via fallback form.

**Q: How to scale for large schools (1000+ students)?**  
A: Use vector database (FAISS/Weaviate), GPU inference, batch embedding indexing, and sharding by cohort.

---

## 🔒 Security Considerations (Current vs. Production)

| Aspect | Current | Production |
|--------|---------|-----------|
| **Passwords** | Plaintext | Hash with bcrypt/argon2 |
| **Embeddings** | Plaintext in DB | Encrypted at rest |
| **HTTPS** | No | Yes, with SSL certificates |
| **Auth** | Session-based | JWT or OAuth2 |
| **Access Control** | Basic role check | Fine-grained permissions |
| **Data Retention** | No policy | GDPR-compliant deletion policy |
| **Eval()** | Used (unsafe) | Replace with json.loads/ast.literal_eval |

---

## 📝 Demo Script (2–3 minutes)

1. **Start & Show Logs**
   - `python app.py` → show initialization logs

2. **Register & Login**
   - Register teacher with secret 'admin' → login

3. **Add Student**
   - Go to /student → add student with photo

4. **Realtime Recognition**
   - Open /realtime → show webcam → detect face → click to mark attendance

5. **View Attendance**
   - Open /attendance → show recorded entry with timestamp

6. **Student Profile**
   - Click student name → show photo (served via /known_faces/) + attendance history

7. **Discuss Thresholds & Accuracy**
   - Explain embedding distance, thresholds, and why two different values

---

## 🎯 Summary
This system **automates attendance via biometric face recognition** while providing **manual fallbacks, CRUD student management, and comprehensive audit trails**. It uses **pretrained FaceNet embeddings for speed and accuracy**, **MySQL for persistence**, and a **modern Flask web interface** for accessibility.

