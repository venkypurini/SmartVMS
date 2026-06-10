# SmartVMS - Smart Visitor Management System

SmartVMS is a secure, modern, and high-performance Enterprise-Level Visitor Management System designed as a desktop application using Python, PyQt5, and SQLite. It automates registration, entry/exit check-in/out, face recognition, QR code pass verification, real-time logging, notifications, and analytics.

---

## Key Features

1. **Secure Session Authentication:** Dynamic logins for Admin, Security, and Receptionist roles with secure password hashing fallbacks.
2. **Visitor Registration Module:** Interactive form with full validations, webcam capture, crop-assisted face savings, and host employee selector.
3. **QR Code Passes:** Automatic high-contrast PNG QR pass generation and ReportLab-designed printable visitor badges.
4. **Dual-Mode Face Recognition:** Integrates `face_recognition` with automatic fallback to OpenCV Haar Cascades for face detection and matching.
5. **Dynamic Dashboard Analytics:** Glassmorphism metrics cards and embedded Matplotlib charts (Weekly Trends, Department distributions, Peak entry hours) adapting to Dark/Light themes.
6. **Report Management:** Customized filters to compile logs and export as PDF (Landscape layout), styled Excel spreadsheets, or standard CSV files.
7. **Operator Security Log:** Role-based access controls (RBAC) restricting operator creation/deletion to Admins, with full audit trail logging.
8. **Real-Time Notification System:** Log notifications locally to `reports/notifications_log.txt` with structured hooks for SMTP email alerts to host employees.

---

## Project Folder Structure

```
SmartVMS/
│
├── assets/                  # Icons, custom images, etc.
├── database/                # SQLite database (smart_vms.db)
├── reports/                 # Exported PDF/Excel/CSV logs & email audits
├── qr_codes/                # Generated visitor QR pass images (.png)
├── visitor_images/          # Captured visitor face photos (.jpg)
│
├── ui/                      # PyQt5 GUI Tab Views
│   ├── login_window.py      # Authentication screen
│   ├── main_window.py       # Base frame shell & Sidebar
│   ├── dashboard_tab.py     # Analytics & Matplotlib charts
│   ├── registration_tab.py  # Input form & Webcam captures
│   ├── checkin_tab.py       # QR & Face scan station
│   ├── history_tab.py       # Search logs with pagination
│   ├── reports_tab.py       # Document exporters (PDF/XLS/CSV)
│   └── security_tab.py      # Operator creation & Audit log
│
├── modules/                 # Business logic controllers
│   ├── camera.py            # QThread webcam capture & mock generator
│   ├── face_rec.py          # Facial encodings & Haar Cascades matching
│   ├── qr_code.py           # QR PNG creation & PDF Badge builder
│   └── notifier.py          # Email and local notifications engine
│
├── models/                  # Database schema & CRUD wrappers
│   ├── db_manager.py        # SQLite connectivity & DB seeding
│   ├── user.py              # Operator authentication
│   ├── visitor.py           # Visitor transactions & analytics queries
│   └── employee.py          # Host employee & department lookups
│
├── utils/                   # Helpers & Stylesheet systems
│   ├── styles.py            # Dark & Light QSS styling definitions
│   └── validators.py        # Email, Mobile, & Name validators
│
├── main.py                  # Main entry point application
├── requirements.txt         # Package dependencies
└── README.md                # Documentation & User Manual
```

---

## Installation & Setup Guide

### 1. Prerequisites
- **Python:** Version 3.8 to 3.14 (3.10+ recommended)
- **C++ Build Tools (Optional):** Required to compile `dlib` if you want *native* high-accuracy face recognition. If missing, the app automatically switches to *OpenCV Haar Cascade Fallback Mode* and runs flawlessly.

### 2. Dependency Installation
Navigate to the project directory and run the following command in terminal:
```bash
pip install -r requirements.txt
```

### 3. Running the Application
Launch the VMS application by running:
```bash
python main.py
```

---

## Operator User Manual

### Default Access Profiles
The system is seeded with three default accounts for testing:
- **System Administrator:**
  - Username: `admin`
  - Password: `admin123`
  - Access: Full features including User Administration, deleting accounts, and auditing.
- **Receptionist:**
  - Username: `reception`
  - Password: `reception123`
  - Access: Registration, Dashboard, Check-In/Out, History, Reports. (User administration locked).
- **Security Officer:**
  - Username: `security`
  - Password: `security123`
  - Access: Check-In/Out, Dashboard, History, Security Logs. (User administration locked).

### Step-by-Step Operations

#### 1. Registering a New Visitor
- Go to the **Register Visitor** tab.
- Fill out the form. The **Employee (Host)** dropdown list will automatically filter when you select a **Department**.
- Position the visitor in front of the camera and click **CAPTURE FACE PHOTO**. The system will scan and crop the face automatically.
- Click **REGISTER & GENERATE PASS**.
- A unique Visitor ID is assigned (e.g. `VIS-YYYYMMDD-0001`), a QR pass is saved under `qr_codes/`, and a printable PDF badge is compiled under `reports/`.

#### 2. Checking In / Out a Visitor
- Go to the **Check-In / Check-Out** tab.
- **Auto-Scan Method:** Align the visitor's printed QR pass or show their face to the camera. The system will decode the QR code or match the face against preloaded registered encodings.
  - If they are currently *Registered*, they are checked in.
  - If they are currently *Checked In*, they are checked out and stay duration is calculated.
- **Manual Method:** Search for the visitor in the right-side list by name, ID, or phone. Click on their name to inspect details, then click **CHECK IN** or **CHECK OUT**.
- **Notifications:** Upon check-in/out, a notification details log is generated in `reports/notifications_log.txt` (and email sent if SMTP is active) notifying the host.

#### 3. Analyzing Traffic and Exporting Reports
- Open the **Analytics Dashboard** to view live metrics cards and visual trends.
- Switch theme modes by clicking **Light Mode** / **Dark Mode** at the top right; all elements and Matplotlib charts will adapt their stylesheets instantly.
- To download records, open the **Reports Panel**, configure dates and statuses, and choose **EXPORT TO PDF**, **EXPORT TO EXCEL**, or **EXPORT TO CSV**. Click *Open File* in the confirmation window to review.
