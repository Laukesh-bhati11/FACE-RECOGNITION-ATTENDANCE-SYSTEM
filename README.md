📸 Face Recognition Attendance System
An automated biometric solution designed to streamline classroom management using Computer Vision. This system identifies students in real-time and logs their attendance directly into a MySQL database, eliminating manual paperwork and proxy attendance.

🚀 Features
Real-time Recognition: High-speed face detection and identification using a live camera feed.

MySQL Integration: Relational database storage for student profiles and timestamped attendance logs.

Data Security: Optimized image-to-data processing to ensure privacy and local storage.

Automated CSV Export: Option to export attendance reports for administrative use.

Responsive Logic: Minimal latency between face detection and database entry.

🛠️ Tech Stack
Language: Python 3.x

Library: OpenCV (Open Source Computer Vision Library)

Database: MySQL

Core Modules: mysql-connector-python, NumPy, Pandas

🏗️ System Architecture
Dataset Creation: Captures and stores 100+ facial samples per student to ensure high accuracy.

Model Training: Trains the recognition algorithm (LBPH/Eigenfaces) on the captured dataset.

Real-Time Identification: Scans the live video feed and compares facial embeddings against the database.

Attendance Logging: Automatically updates the attendance table in MySQL with student ID, Name, Date, and Time.

💻 Installation & Setup
Clone the Project

Bash
git clone https://github.com/your-username/face-recognition-attendance.git
cd face-recognition-attendance
Install Dependencies

Bash
pip install opencv-python mysql-connector-python numpy
Database Configuration

Create a MySQL database named attendance_system.

Create a table student_data and attendance_logs.

Update the database credentials in the configuration file.

Run the Application

Bash
python main.py
📈 Future Enhancements
[ ] Integration with a Web Dashboard for Teachers.

[ ] Email/SMS alerts for absent students.

[ ] Anti-spoofing logic to prevent photo-based bypass.
