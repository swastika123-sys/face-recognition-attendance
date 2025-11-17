# Face Recognition Attendance System

An **AI-powered Flask web application** that automates student attendance using **real-time face recognition** with DeepFace and FaceNet.

## 🎯 Features

- ✅ **Real-time Face Recognition** - Webcam-based attendance with live detection
- ✅ **Duplicate Detection** - Prevents same student from registering twice (strict threshold)
- ✅ **Student Management** - Full CRUD operations (add, view, edit, delete)
- ✅ **Manual Fallback** - Form-based attendance if recognition fails
- ✅ **Data Persistence** - MySQL database + CSV backup
- ✅ **Role-Based Access** - Teacher login with session management
- ✅ **Futuristic UI** - Glassmorphism design with animated backgrounds
- ✅ **Multi-Method Attendance** - Face recognition + manual entry with audit trail

## 🏗️ Architecture

```
Webcam → Canvas API → Base64 JSON
  ↓
Flask /detect_face & /recognize endpoints
  ↓
DeepFace (FaceNet embeddings) + NumPy (distance comparison)
  ↓
MySQL (persistence) + CSV (backup)
  ↓
Attendance logged instantly
```

## 🚀 Quick Start

### Prerequisites

- Python 3.11 (Required for TensorFlow/DeepFace compatibility)
- MySQL 8.0
- Webcam

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/YOUR_USERNAME/face-recognition-attendance.git
cd face-recognition-attendance
```

2. **Create virtual environment**
```bash
python3.11 -m venv venv-py311
source venv-py311/bin/activate  # On Windows: venv-py311\Scripts\activate
```

3. **Install dependencies**
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

4. **Setup MySQL database**
```bash
# Create database
mysql -u root -e "CREATE DATABASE IF NOT EXISTS face_project;"

# Update db.py with your MySQL credentials if needed
# Default: host='localhost', user='root', password='', database='face_project'
```

5. **Run the application**
```bash
python app.py
```

6. **Access in browser**
```
http://localhost:5001
```

## 📦 Tech Stack

| Component | Technology |
|-----------|-----------|
| **Backend** | Python 3.11, Flask |
| **AI/CV** | DeepFace (FaceNet embeddings), OpenCV, NumPy, Pillow |
| **Frontend** | HTML5, CSS3, JavaScript, Bootstrap 5, Canvas API |
| **Database** | MySQL 8.0 (mysql-connector-python) |
| **Environment** | Virtual environment (venv-py311), pip |

## 🧠 How It Works

### Face Recognition Pipeline

1. **Registration**: Student captures face → FaceNet extracts 128-D embedding → saved to DB
2. **Detection**: Webcam frame → `/detect_face` endpoint → bounding boxes + names returned
3. **Recognition**: Teacher clicks → `/recognize` endpoint → embedding compared (threshold=15.0) → attendance marked if match
4. **Storage**: Logged to MySQL `attendance` table + `attendance.csv` backup

### Thresholds

- **Duplicate Detection (Registration)**: 3.0 — strict, prevents fraud
- **Attendance Recognition**: 15.0 — lenient, tolerates lighting/pose variations

## 📊 Usage

### Register Teacher

1. Go to `/register`
2. Select "Teacher" role
3. Enter: username, email, password, teacher_secret (use: `admin`)
4. Click Register

### Register Student

1. Go to `/register`
2. Select "Student" role
3. Enter: username, email, serial_number, phone
4. Capture face using webcam
5. Click Register (system checks for duplicates)

### Mark Attendance

1. Login as teacher
2. Go to Dashboard → Realtime Attendance
3. Allow webcam access
4. System detects faces with bounding boxes
5. Click on detected face to mark attendance
6. Attendance logged instantly to database + CSV

## 🔐 Security Notes

**Current Implementation (Development)**
- Passwords stored in plaintext
- Face embeddings unencrypted in DB
- No HTTPS

**Production Requirements**
- Hash passwords with bcrypt/argon2
- Encrypt face encodings with AES-256
- Deploy with SSL certificates
- Replace `eval()` with `json.loads` for embedding deserialization
- Add audit logging

## 📁 Project Structure

```
projectface.html/
├── app.py                    # Main Flask application
├── db.py                     # Database connection
├── requirements.txt          # Python dependencies
├── attendance.csv            # CSV backup
├── known_faces/              # Student face images
├── static/                   # Static assets (JS, videos)
├── templates/                # HTML templates
└── venv-py311/              # Virtual environment
```

## 🎓 Key Routes

| Route | Method | Description |
|-------|--------|-------------|
| `/` | GET | Home page |
| `/register` | GET/POST | User registration (teacher/student) |
| `/login` | GET/POST | Teacher login |
| `/dashboard` | GET | Teacher dashboard |
| `/realtime` | GET | Webcam attendance page |
| `/detect_face` | POST | Real-time face detection (JSON) |
| `/recognize` | POST | Face recognition for attendance (JSON) |
| `/student` | GET | Student management page |
| `/attendance` | GET | Attendance history |
| `/known_faces/<filename>` | GET | Serve student images |

## 📈 Performance

- **Latency**: 225-470ms end-to-end (GPU/CPU)
- **Accuracy Target**: TAR > 95%, FAR < 1%
- **Embedding Dimension**: 128-D (FaceNet)
- **Throughput**: 10+ students/minute

## 🔮 Future Enhancements

- [ ] Anti-spoofing (liveness detection)
- [ ] FAISS vector indexing for 1000+ students
- [ ] ArcFace model for better accuracy
- [ ] Mobile app (Flutter/React Native)
- [ ] Analytics dashboard (attendance trends)
- [ ] GDPR compliance (encryption, consent, deletion)
- [ ] Multi-modal biometrics (face + fingerprint)

## 🐛 Known Limitations

1. **No anti-spoofing** - Can be fooled by high-quality photos
2. **Accuracy affected by** - Poor lighting, masks, glasses, aging
3. **Scaling** - O(n) comparison; needs FAISS for large deployments
4. **Bias** - FaceNet shows accuracy gaps for darker skin tones

## 📝 Documentation

- [Technical Deep Dive](TECHNICAL_DEEP_DIVE.md) - Detailed architecture & algorithms
- [Presentation Slides](PRESENTATION_SLIDES.md) - PowerPoint outline for viva/demo
- [Project Overview](PROJECT_OVERVIEW.md) - Complete process documentation

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is open source and available under the [MIT License](LICENSE).

## 👥 Authors

- **Swastika** - *Initial work* - [Your GitHub Profile]

## 🙏 Acknowledgments

- DeepFace library for face recognition
- FaceNet model (Google Research)
- Bootstrap for UI components
- Flask community

## 📞 Support

For questions or issues:
- Open an issue on GitHub
- Email: [your-email@example.com]

---

**⚠️ Disclaimer**: This is a prototype for educational purposes. For production deployment, implement proper security measures (encryption, HTTPS, audit logging, consent management).
