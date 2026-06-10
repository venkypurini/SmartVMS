import os
import numpy as np
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QLineEdit, QComboBox, QTextEdit, QPushButton,
                             QFrame, QFileDialog, QMessageBox, QSplitter,
                             QListWidget, QListWidgetItem)
from PyQt5.QtCore import Qt, pyqtSignal, pyqtSlot, QDateTime, QTimer
from PyQt5.QtGui import QImage, QPixmap, QFont

from models.visitor import VisitorModel
from models.employee import EmployeeModel
from models.audit_logs import AuditLogModel
from modules.camera import CameraThread
from modules.face_rec import FaceRecognizer
from modules.qr_code import QRPassGenerator
from utils.validators import Validators

class RegistrationTab(QWidget):
    registration_completed = pyqtSignal()  # Emitted when a new visitor is registered

    def __init__(self, user_session, parent=None):
        super().__init__(parent)
        self.user_session = user_session

        # Camera management
        self.camera_thread = None
        self.current_frame = None  # Cache for capture frame
        self.captured_photo_path = None

        # Resolved host employee from the live search
        self._selected_employee_id   = None
        self._selected_department_id = None

        self.init_ui()
        self._load_all_employees()   # preload employee list for search

    def init_ui(self):
        # Main Layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.main_layout.setSpacing(15)

        # Tab Header
        title_label = QLabel("Visitor Registration Form")
        title_label.setObjectName("TabTitle")
        self.main_layout.addWidget(title_label)

        # Splitter to separate Form (left) and Media/Camera (right)
        splitter = QSplitter(Qt.Horizontal)
        splitter.setStyleSheet("QSplitter::handle { background-color: #2d2d3f; width: 1px; }")
        self.main_layout.addWidget(splitter)

        # ------------------ LEFT SIDE: REGISTRATION FORM ------------------
        form_frame = QFrame()
        form_layout = QVBoxLayout(form_frame)
        form_layout.setContentsMargins(0, 0, 15, 0)
        form_layout.setSpacing(12)

        # Visitor ID (Read-only, generated on registration or displayed pre-generated)
        id_layout = QHBoxLayout()
        id_label = QLabel("Visitor ID (Auto-Gen):")
        id_label.setObjectName("FormLabel")
        id_label.setFixedWidth(140)
        self.id_val_lbl = QLabel("[Generated on Submit]")
        self.id_val_lbl.setStyleSheet("color: #2ecc71; font-weight: bold; font-size: 14px;")
        id_layout.addWidget(id_label)
        id_layout.addWidget(self.id_val_lbl)
        form_layout.addLayout(id_layout)

        # Full Name
        name_layout = QHBoxLayout()
        name_label = QLabel("Full Name *:")
        name_label.setObjectName("FormLabel")
        name_label.setFixedWidth(140)
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("First & Last Name")
        name_layout.addWidget(name_label)
        name_layout.addWidget(self.name_input)
        form_layout.addLayout(name_layout)

        # Gender
        gender_layout = QHBoxLayout()
        gender_label = QLabel("Gender *:")
        gender_label.setObjectName("FormLabel")
        gender_label.setFixedWidth(140)
        self.gender_combo = QComboBox()
        self.gender_combo.addItems(["Male", "Female", "Other"])
        gender_layout.addWidget(gender_label)
        gender_layout.addWidget(self.gender_combo)
        form_layout.addLayout(gender_layout)

        # Mobile Number
        mobile_layout = QHBoxLayout()
        mobile_label = QLabel("Mobile Number *:")
        mobile_label.setObjectName("FormLabel")
        mobile_label.setFixedWidth(140)
        self.mobile_input = QLineEdit()
        self.mobile_input.setPlaceholderText("e.g. +15550199 or 5550199")
        # Quick validation on focus out or text change (optional duplicate detection on lost focus)
        self.mobile_input.editingFinished.connect(self.check_duplicate_visitor)
        mobile_layout.addWidget(mobile_label)
        mobile_layout.addWidget(self.mobile_input)
        form_layout.addLayout(mobile_layout)

        # Email
        email_layout = QHBoxLayout()
        email_label = QLabel("Email Address:")
        email_label.setObjectName("FormLabel")
        email_label.setFixedWidth(140)
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("name@company.com")
        email_layout.addWidget(email_label)
        email_layout.addWidget(self.email_input)
        form_layout.addLayout(email_layout)

        # Company Name
        company_layout = QHBoxLayout()
        company_label = QLabel("Company Name:")
        company_label.setObjectName("FormLabel")
        company_label.setFixedWidth(140)
        self.company_input = QLineEdit()
        self.company_input.setPlaceholderText("Visitor's Employer Organization")
        company_layout.addWidget(company_label)
        company_layout.addWidget(self.company_input)
        form_layout.addLayout(company_layout)

        # Purpose of Visit
        purpose_layout = QHBoxLayout()
        purpose_label = QLabel("Purpose of Visit *:")
        purpose_label.setObjectName("FormLabel")
        purpose_label.setFixedWidth(140)
        self.purpose_combo = QComboBox()
        self.purpose_combo.addItems(["Meeting", "Interview", "Delivery", "Contractor / Maintenance", "Personal Visit", "Other"])
        purpose_layout.addWidget(purpose_label)
        purpose_layout.addWidget(self.purpose_combo)
        form_layout.addLayout(purpose_layout)

        # ---- WHO DO YOU WANT TO MEET? (live host search) ----
        host_section_lbl = QLabel("Who do you want to meet?")
        host_section_lbl.setObjectName("FormLabel")
        host_section_lbl.setStyleSheet("color:#2ecc71; font-weight:bold; margin-top:6px;")
        form_layout.addWidget(host_section_lbl)

        # Search input
        host_search_layout = QHBoxLayout()
        host_search_label = QLabel("Host Name *:")
        host_search_label.setObjectName("FormLabel")
        host_search_label.setFixedWidth(140)
        self.host_search_input = QLineEdit()
        self.host_search_input.setPlaceholderText("Type the name of the person to meet...")
        self.host_search_input.textChanged.connect(self._on_host_search_changed)
        host_search_layout.addWidget(host_search_label)
        host_search_layout.addWidget(self.host_search_input)
        form_layout.addLayout(host_search_layout)

        # Suggestion list (hidden until user types)
        self.host_suggestion_list = QListWidget()
        self.host_suggestion_list.setMaximumHeight(120)
        self.host_suggestion_list.setStyleSheet("""
            QListWidget {
                background-color: #242436;
                border: 1px solid #2ecc71;
                border-radius: 6px;
                color: #ffffff;
                font-size: 13px;
                font-weight: 500;
            }
            QListWidget::item { padding: 6px 10px; }
            QListWidget::item:hover  { background-color: #1e3a3a; }
            QListWidget::item:selected { background-color: #2ecc71; color: white; }
        """)
        self.host_suggestion_list.itemClicked.connect(self._on_host_selected)
        self.host_suggestion_list.hide()
        form_layout.addWidget(self.host_suggestion_list)

        # Confirmed host display label
        self.host_confirmed_lbl = QLabel("No host selected yet.")
        self.host_confirmed_lbl.setStyleSheet(
            "color:#ffffff; font-size:11px; padding-left:145px;"
        )
        form_layout.addWidget(self.host_confirmed_lbl)
        proof_layout = QHBoxLayout()
        proof_label = QLabel("ID Proof Type:")
        proof_label.setObjectName("FormLabel")
        proof_label.setFixedWidth(140)
        self.proof_combo = QComboBox()
        self.proof_combo.addItems(["National Identity Card (ID)", "Passport", "Driver's License", "Company ID", "None"])
        proof_layout.addWidget(proof_label)
        proof_layout.addWidget(self.proof_combo)
        form_layout.addLayout(proof_layout)

        # Address
        addr_layout = QHBoxLayout()
        addr_label = QLabel("Full Address:")
        addr_label.setObjectName("FormLabel")
        addr_label.setFixedWidth(140)
        self.address_input = QTextEdit()
        self.address_input.setPlaceholderText("Visitor current street address")
        self.address_input.setMaximumHeight(60)
        addr_layout.addWidget(addr_label)
        addr_layout.addWidget(self.address_input)
        form_layout.addLayout(addr_layout)

        # Register Submit Button
        self.submit_btn = QPushButton("📝  SUBMIT REGISTRATION REQUEST")
        self.submit_btn.setObjectName("PrimaryBtn")
        self.submit_btn.setFixedHeight(48)
        self.submit_btn.setCursor(Qt.PointingHandCursor)
        self.submit_btn.clicked.connect(self.submit_registration)
        form_layout.addWidget(self.submit_btn)

        # Reset button
        reset_btn = QPushButton("Clear Form")
        reset_btn.setObjectName("SecondaryBtn")
        reset_btn.clicked.connect(self.clear_form)
        form_layout.addWidget(reset_btn)

        splitter.addWidget(form_frame)

        # ------------------ RIGHT SIDE: CAMERA & PHOTO CAPTURE ------------------
        media_frame = QFrame()
        media_layout = QVBoxLayout(media_frame)
        media_layout.setContentsMargins(15, 0, 0, 0)
        media_layout.setSpacing(15)

        # Camera feed container Label
        camera_card = QFrame()
        camera_card.setObjectName("MetricCard")
        camera_card_layout = QVBoxLayout(camera_card)
        camera_card_layout.setContentsMargins(5, 5, 5, 5)
        
        self.camera_view = QLabel()
        self.camera_view.setAlignment(Qt.AlignCenter)
        self.camera_view.setStyleSheet("background-color: #1a1a24; border-radius: 8px;")
        self.camera_view.setFixedSize(360, 270)
        self.camera_view.setText("Webcam Feed Offline")
        self.camera_view.setFont(QFont("Segoe UI", 12))
        camera_card_layout.addWidget(self.camera_view)
        media_layout.addWidget(camera_card)

        # Capture button
        self.capture_btn = QPushButton("CAPTURE FACE PHOTO")
        self.capture_btn.setObjectName("AccentBtn")
        self.capture_btn.setFixedHeight(38)
        self.capture_btn.setCursor(Qt.PointingHandCursor)
        self.capture_btn.clicked.connect(self.capture_photo)
        media_layout.addWidget(self.capture_btn)

        # Photo Preview Section
        preview_card = QFrame()
        preview_card.setObjectName("MetricCard")
        preview_card_layout = QHBoxLayout(preview_card)
        preview_card_layout.setSpacing(15)

        preview_text_layout = QVBoxLayout()
        preview_text_layout.setSpacing(5)
        
        p_title = QLabel("Captured Photo")
        p_title.setFont(QFont("Segoe UI", 11, QFont.Bold))
        p_title.setStyleSheet("color: #2ecc71;")
        
        self.p_status = QLabel("No photo captured yet.\nFace detection auto-applied on capture.")
        self.p_status.setWordWrap(True)
        self.p_status.setFont(QFont("Segoe UI", 9))
        self.p_status.setStyleSheet("color: #ffffff;")
        
        preview_text_layout.addWidget(p_title)
        preview_text_layout.addWidget(self.p_status)
        preview_text_layout.addStretch()
        
        preview_card_layout.addLayout(preview_text_layout)

        # Captured Preview Frame
        self.photo_preview = QLabel()
        self.photo_preview.setFixedSize(100, 100)
        self.photo_preview.setAlignment(Qt.AlignCenter)
        self.photo_preview.setStyleSheet("background-color: #1a1a24; border: 1px dashed #2d2d3f; border-radius: 8px;")
        self.photo_preview.setText("PREVIEW")
        self.photo_preview.setFont(QFont("Segoe UI", 8))
        preview_card_layout.addWidget(self.photo_preview)

        media_layout.addWidget(preview_card)

        # ---- APPROVAL STATUS CARD (shown after successful registration) ----
        self.approval_card = QFrame()
        self.approval_card.setObjectName("MetricCard")
        self.approval_card.setStyleSheet("""
            QFrame#MetricCard {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #0d2b1e, stop:1 #1a1a2e);
                border: 1px solid #00ff66;
                border-radius: 10px;
            }
        """)
        approval_card_layout = QVBoxLayout(self.approval_card)
        approval_card_layout.setContentsMargins(16, 14, 16, 14)
        approval_card_layout.setSpacing(8)

        # Status badge row
        badge_row = QHBoxLayout()
        self.status_badge = QLabel("⏳  PENDING APPROVAL")
        self.status_badge.setFont(QFont("Segoe UI", 12, QFont.Bold))
        self.status_badge.setStyleSheet(
            "background-color:#1a3a1a; color:#00ff66;"
            "border:1px solid #1f6b30; border-radius:6px;"
            "padding:5px 14px;"
        )
        badge_row.addWidget(self.status_badge)
        badge_row.addStretch()
        approval_card_layout.addLayout(badge_row)

        # Divider
        div = QFrame()
        div.setFrameShape(QFrame.HLine)
        div.setStyleSheet("color:#1f6b30;")
        approval_card_layout.addWidget(div)

        # Details grid
        self.apv_visitor_lbl  = QLabel()
        self.apv_code_lbl     = QLabel()
        self.apv_host_lbl     = QLabel()
        self.apv_dept_lbl     = QLabel()
        self.apv_purpose_lbl  = QLabel()

        for lbl in [self.apv_visitor_lbl, self.apv_code_lbl,
                    self.apv_host_lbl, self.apv_dept_lbl, self.apv_purpose_lbl]:
            lbl.setStyleSheet("color:#ffffff; font-size:12px;")
            lbl.setWordWrap(True)
            approval_card_layout.addWidget(lbl)

        # Info message
        info_lbl = QLabel(
            "ℹ️  The approval request has been sent to the host.\n"
            "Once approved, a QR pass will be generated automatically."
        )
        info_lbl.setStyleSheet("color:#00ff66; font-size:11px; margin-top:4px;")
        info_lbl.setWordWrap(True)
        approval_card_layout.addWidget(info_lbl)

        # Go to Approvals button
        self.goto_approvals_btn = QPushButton("✅  Go to Approvals Tab")
        self.goto_approvals_btn.setStyleSheet(
            "background-color:#1a3a1a; color:#00ff66;"
            "border:1px solid #1f6b30; border-radius:6px;"
            "padding:8px; font-weight:bold; margin-top:4px;"
        )
        self.goto_approvals_btn.setCursor(Qt.PointingHandCursor)
        self.goto_approvals_btn.clicked.connect(self._goto_approvals)
        approval_card_layout.addWidget(self.goto_approvals_btn)

        # Email status — updated after send attempt
        self.email_status_lbl = QLabel("⏳ Sending notification email…")
        self.email_status_lbl.setStyleSheet("color:#ffffff; font-size:11px; margin-top:4px;")
        self.email_status_lbl.setWordWrap(True)
        approval_card_layout.addWidget(self.email_status_lbl)

        self.approval_card.hide()   # hidden until a visitor is registered
        media_layout.addWidget(self.approval_card)

        media_layout.addStretch()
        splitter.addWidget(media_frame)

    # ------------------------------------------------------------------
    # HOST LIVE SEARCH
    # ------------------------------------------------------------------
    def _load_all_employees(self):
        """Pre-load all employees from DB into a local list for fast search."""
        try:
            self._all_employees = EmployeeModel.get_all_employees()
        except Exception as e:
            self._all_employees = []
            print(f"[RegTab] Failed to load employees: {e}")

    def _on_host_search_changed(self, text):
        """Filter employee suggestions as user types."""
        try:
            # If a host is already confirmed, don't disturb unless user is actively editing
            if self._selected_employee_id and self.host_search_input.signalsBlocked():
                return

            text = text.strip()
            self.host_suggestion_list.clear()

            # If field is cleared, reset selection
            if not text:
                self.host_suggestion_list.hide()
                self._selected_employee_id   = None
                self._selected_department_id = None
                self.host_confirmed_lbl.setText("No host selected yet.")
                self.host_confirmed_lbl.setStyleSheet("color:#ffffff; font-size:11px; padding-left:145px;")
                return

            # If a host is already confirmed and text matches, don't re-search
            if self._selected_employee_id:
                return

            matches = [
                emp for emp in self._all_employees
                if text.lower() in emp['name'].lower()
            ]

            if matches:
                for emp in matches[:10]:
                    dept = emp.get('department_name', 'N/A')
                    item = QListWidgetItem(f"{emp['name']}  —  {dept}")
                    item.setData(Qt.UserRole, emp)
                    self.host_suggestion_list.addItem(item)
                self.host_suggestion_list.show()
                self.host_confirmed_lbl.setText("Select a name from the list below ↑")
                self.host_confirmed_lbl.setStyleSheet(
                    "color:#ff9f43; font-size:11px; padding-left:145px;"
                )
            else:
                self.host_suggestion_list.hide()
                self._selected_employee_id   = None
                self._selected_department_id = None
                self.host_confirmed_lbl.setText(
                    f"⚠️  No registered employee found matching '{text}'."
                    "  Register the employee first in the 👤 Employees tab."
                )
                self.host_confirmed_lbl.setStyleSheet(
                    "color:#ff4444; font-size:11px; font-weight:bold; padding-left:145px;"
                )
        except Exception as e:
            print(f"[RegTab] _on_host_search_changed error: {e}")

    def _on_host_selected(self, item):
        """Called when user clicks a suggestion. Locks in the employee."""
        emp = item.data(Qt.UserRole)
        if not emp:
            return

        self._selected_employee_id   = emp['id']
        self._selected_department_id = emp.get('department_id')

        dept = emp.get('department_name', 'N/A')

        # Block textChanged so setting text doesn't re-trigger the search
        self.host_search_input.blockSignals(True)
        self.host_search_input.setText(emp['name'])
        self.host_search_input.blockSignals(False)

        self.host_suggestion_list.clear()
        self.host_suggestion_list.hide()

        self.host_confirmed_lbl.setText(
            f"✅  Host confirmed: {emp['name']}  |  Department: {dept}"
        )
        self.host_confirmed_lbl.setStyleSheet(
            "color:#00ff66; font-size:11px; font-weight:bold; padding-left:145px;"
        )

    def start_camera(self):
        """Start OpenCV capture thread and connect frames signal."""
        if self.camera_thread is None:
            self.camera_thread = CameraThread()
            self.camera_thread.frame_ready.connect(self.update_camera_frame)
            self.camera_thread.start()

    def stop_camera(self):
        """Stop camera thread."""
        if self.camera_thread:
            self.camera_thread.stop()
            self.camera_thread = None
            self.camera_view.setText("Webcam Feed Offline")

    @pyqtSlot(QImage)
    def update_camera_frame(self, q_img):
        """Receive QImage from camera thread, scale and show it in QLabel."""
        self.current_frame = q_img
        
        # Convert QImage to OpenCV format (numpy) for live face detection wireframe (optional feedback)
        # However, drawing is already simulated in the emulator if webcam is empty.
        # We can directly display it
        scaled_img = q_img.scaled(self.camera_view.width(), self.camera_view.height(), 
                                  Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.camera_view.setPixmap(QPixmap.fromImage(scaled_img))

    def capture_photo(self):
        """Capture the current frame, detect faces, save photo and update preview."""
        try:
            if self.current_frame is None:
                QMessageBox.warning(self, "Camera Warning", "No active camera frame available.")
                return

            # Generate temporary visitor ID to map image name (fixed: use QDateTime directly)
            temp_id = f"TEMP_{int(QDateTime.currentSecsSinceEpoch())}"
            
            # Convert QImage back to OpenCV image (numpy array BGR)
            width = self.current_frame.width()
            height = self.current_frame.height()
            ptr = self.current_frame.constBits()
            ptr.setsize(self.current_frame.byteCount())
            
            # Convert to numpy array
            arr = np.array(ptr, copy=True).reshape((height, width, 3))
            # RGB to BGR
            import cv2
            cv_img = cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)

            # Detect face bounding box
            faces = FaceRecognizer.detect_faces(cv_img)
            bbox = faces[0] if faces else None

            # Save photo
            photo_path = FaceRecognizer.save_visitor_photo(cv_img, temp_id, bounding_box=bbox)
            
            if photo_path and os.path.exists(photo_path):
                self.captured_photo_path = photo_path
                
                # Show preview
                pix = QPixmap(photo_path)
                scaled_pix = pix.scaled(self.photo_preview.width(), self.photo_preview.height(),
                                        Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.photo_preview.setPixmap(scaled_pix)
                
                if bbox:
                    self.p_status.setText("Success! Face detected and cropped. Ready to register.")
                    self.p_status.setStyleSheet("color: #00ff66;")
                else:
                    self.p_status.setText("Photo captured (No face detected). You can still proceed.")
                    self.p_status.setStyleSheet("color: #ff9f43;")
            else:
                QMessageBox.critical(self, "Capture Error", "Failed to save captured photo.")
        except Exception as e:
            print(f"[RegTab] capture_photo error: {e}")
            QMessageBox.critical(self, "Capture Error", f"An error occurred during capture:\n{e}")

    def check_duplicate_visitor(self):
        """Real-time duplicate check by mobile number when user finishes editing the field."""
        mobile = self.mobile_input.text().strip()
        if not mobile:
            return
            
        dup = VisitorModel.is_duplicate_visitor(mobile)
        if dup:
            QMessageBox.information(
                self, "Active Visitor Detected",
                f"A visitor named '{dup['full_name']}' is already registered with mobile '{mobile}'.\n"
                f"Current Status: {dup['status']}\n\n"
                "Please check them out first in the Check-In/Out panel if they are entering again."
            )

    def submit_registration(self):
        """Validate input data, create database entry, generate QR Code and PDF badge. Wrapped in try/except to prevent silent crashes."""
        try:
            self._do_submit_registration()
        except Exception as e:
            print(f"[RegTab] submit_registration unexpected error: {e}")
            QMessageBox.critical(self, "Registration Error", f"An unexpected error occurred:\n{e}")

    def _do_submit_registration(self):
        """Internal registration logic."""
        name = self.name_input.text().strip()
        mobile = self.mobile_input.text().strip()
        email = self.email_input.text().strip()
        company = self.company_input.text().strip()
        address = self.address_input.toPlainText().strip()
        purpose = self.purpose_combo.currentText()
        proof_type = self.proof_combo.currentText()

        # Host employee from live search
        employee_id   = self._selected_employee_id
        dept_id       = self._selected_department_id
        host_name     = self.host_search_input.text().strip()

        if not employee_id:
            QMessageBox.warning(
                self, "Validation Error",
                "Please type the host's name in the 'Host Name' field\n"
                "and select them from the suggestion list that appears."
            )
            self.host_search_input.setFocus()
            return

        # Validation Checks
        if not Validators.validate_required(name) or not Validators.validate_name(name):
            QMessageBox.warning(self, "Validation Error", "Please enter a valid Full Name (alphabet characters only).")
            return

        if not Validators.validate_mobile(mobile):
            QMessageBox.warning(self, "Validation Error", "Please enter a valid Mobile Number (7-15 digits).")
            return

        if email and not Validators.validate_email(email):
            QMessageBox.warning(self, "Validation Error", "Please enter a valid Email Address.")
            return

        # Double check duplicate
        dup = VisitorModel.is_duplicate_visitor(mobile)
        if dup and dup['status'] == 'CheckedIn':
            QMessageBox.warning(self, "Duplicate Error", f"Visitor '{name}' is already Checked In.")
            return

        # 1. Build visitor dictionary (no 'id' key — DB assigns auto int id)
        visitor_data = {
            'full_name': name,
            'gender': self.gender_combo.currentText(),
            'mobile': mobile,
            'email': email if email else None,
            'address': address if address else None,
            'company_name': company if company else None,
            'purpose': purpose,
            'employee_id': employee_id,
            'department_id': dept_id,
            'id_proof_type': proof_type if proof_type != "None" else None,
            'photo_path': None,  # will update after rename below
        }

        try:
            # 2. Save visitor to SQLite — get back (int_id, visitor_code)
            visitor_int_id, visitor_code = VisitorModel.register_visitor(visitor_data)

            # 3. Rename captured photo using visitor_code
            final_photo_path = None
            if self.captured_photo_path and os.path.exists(self.captured_photo_path):
                directory = os.path.dirname(self.captured_photo_path)
                new_filename = f"{visitor_code}.jpg"
                final_photo_path = os.path.join(directory, new_filename)
                try:
                    if os.path.exists(final_photo_path):
                        os.remove(final_photo_path)
                    os.rename(self.captured_photo_path, final_photo_path)
                    # Update photo_path in DB
                    from database.db_manager import get_db_connection
                    conn = get_db_connection()
                    conn.execute("UPDATE visitors SET photo_path = ? WHERE id = ?;",
                                 (final_photo_path, visitor_int_id))
                    conn.commit()
                    conn.close()
                    FaceRecognizer.reload_visitor_encoding(visitor_code, final_photo_path)
                except Exception as pe:
                    print(f"[RegTab] Error renaming photo file: {pe}")
                    final_photo_path = self.captured_photo_path

            # 4. Fetch full visitor details
            visitor_details = VisitorModel.get_visitor_by_id(visitor_int_id)

            # NOTE: QR code is NOT generated here.
            # It will be generated only after the host approves in the Approvals tab.

            # 5. Log event
            AuditLogModel.log_event(
                self.user_session['id'], "Register Visitor",
                f"Registered visitor {name} ({visitor_code}) to meet employee ID {employee_id}. Awaiting approval.",
                module="Registration"
            )

            # 6. Show approval status card (no popup)
            # Safely look up dept name from the employee cache
            matched_emp = next(
                (e for e in self._all_employees if e['id'] == employee_id), {}
            )
            self._show_approval_card(
                visitor_code=visitor_code,
                visitor_name=name,
                host_name=host_name,
                dept_name=matched_emp.get('department_name', ''),
                purpose=purpose
            )

            # 7. Send approval-request email to the host employee (non-blocking)
            try:
                from utils.email_sender import send_approval_request_to_employee
                import datetime
                emp_email = matched_emp.get('email', '')
                ok, err = send_approval_request_to_employee(
                    employee_email=emp_email,
                    employee_name=host_name,
                    visitor_name=name,
                    visitor_mobile=mobile,
                    visitor_company=company,
                    purpose=purpose,
                    visitor_code=visitor_code,
                    visit_date=datetime.date.today().strftime("%d %B %Y"),
                    visitor_photo_path=final_photo_path
                )
                if ok:
                    self._update_approval_card_email_status(
                        f"📧 Approval request emailed to {emp_email}"
                    )
                else:
                    self._update_approval_card_email_status(
                        f"⚠️ Email not sent: {err}"
                    )
            except Exception as mail_err:
                print(f"[RegTab] Email send error: {mail_err}")
                self._update_approval_card_email_status(
                    "⚠️ Email notification skipped (configure in ⚙️ Settings)"
                )

            self.registration_completed.emit()
            self._soft_clear_form()

        except Exception as e:
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "Registration Error", f"Failed to register visitor:\n{e}")

    def clear_form(self):
        """Reset all form fields to default state and hide approval card."""
        self.name_input.clear()
        self.mobile_input.clear()
        self.email_input.clear()
        self.company_input.clear()
        self.address_input.clear()
        self.gender_combo.setCurrentIndex(0)
        self.purpose_combo.setCurrentIndex(0)
        self.proof_combo.setCurrentIndex(0)
        self.id_val_lbl.setText("[Generated on Submit]")
        self.photo_preview.clear()
        self.photo_preview.setText("PREVIEW")
        self.p_status.setText("No photo captured yet.\nFace detection auto-applied on capture.")
        self.p_status.setStyleSheet("color: #ffffff;")
        # Reset host search
        self.host_search_input.clear()
        self.host_suggestion_list.clear()
        self.host_suggestion_list.hide()
        self.host_confirmed_lbl.setText("No host selected yet.")
        self.host_confirmed_lbl.setStyleSheet("color:#ffffff; font-size:11px; padding-left:145px;")
        self._selected_employee_id   = None
        self._selected_department_id = None
        # Clean up temporary captured photo
        if self.captured_photo_path and os.path.exists(self.captured_photo_path):
            try:
                os.remove(self.captured_photo_path)
            except Exception:
                pass
        self.captured_photo_path = None
        # Hide approval status card
        self.approval_card.hide()

    def _soft_clear_form(self):
        """Clear form inputs only — keep the approval card visible so operator can read it."""
        self.name_input.clear()
        self.mobile_input.clear()
        self.email_input.clear()
        self.company_input.clear()
        self.address_input.clear()
        self.gender_combo.setCurrentIndex(0)
        self.purpose_combo.setCurrentIndex(0)
        self.proof_combo.setCurrentIndex(0)
        self.id_val_lbl.setText("[Generated on Submit]")
        self.photo_preview.clear()
        self.photo_preview.setText("PREVIEW")
        self.p_status.setText("No photo captured yet.\nFace detection auto-applied on capture.")
        self.p_status.setStyleSheet("color: #ffffff;")
        self.host_search_input.clear()
        self.host_suggestion_list.clear()
        self.host_suggestion_list.hide()
        self.host_confirmed_lbl.setText("No host selected yet.")
        self.host_confirmed_lbl.setStyleSheet("color:#ffffff; font-size:11px; padding-left:145px;")
        self._selected_employee_id   = None
        self._selected_department_id = None
        self.captured_photo_path = None

    def _show_approval_card(self, visitor_code, visitor_name, host_name, dept_name, purpose):
        """Populate and display the approval status card on the right panel."""
        self.apv_visitor_lbl.setText(f"👤  Visitor:   {visitor_name}")
        self.apv_code_lbl.setText(   f"🔖  Code:      {visitor_code}")
        self.apv_host_lbl.setText(   f"🧑‍💼  Host:      {host_name}")
        self.apv_dept_lbl.setText(   f"🏢  Dept:      {dept_name or 'N/A'}")
        self.apv_purpose_lbl.setText(f"📋  Purpose:   {purpose}")
        self.email_status_lbl.setText("⏳ Sending notification email to host…")
        self.email_status_lbl.setStyleSheet("color:#ffffff; font-size:11px; margin-top:4px;")
        self.approval_card.show()

    def _update_approval_card_email_status(self, message):
        """Update the email status label in the approval card."""
        if "📧" in message:
            color = "#00ff66"
        elif "⚠️" in message:
            color = "#ff9f43"
        else:
            color = "#ffffff"
        self.email_status_lbl.setText(message)
        self.email_status_lbl.setStyleSheet(
            f"color:{color}; font-size:11px; margin-top:4px; font-weight:bold;"
        )


    def _goto_approvals(self):
        """Navigate to the Approvals tab (index 2) via the main window."""
        parent = self.parent()
        # Walk up widget tree until we find the MainWindow
        while parent is not None:
            if hasattr(parent, 'switch_tab') and hasattr(parent, 'sidebar'):
                parent.switch_tab(2)
                parent.sidebar.select_tab(2)
                break
            parent = parent.parent()
