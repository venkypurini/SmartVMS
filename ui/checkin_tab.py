import time
import numpy as np
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QFrame, QListWidget, 
                             QMessageBox, QSplitter, QListWidgetItem)
from PyQt5.QtCore import Qt, pyqtSignal, pyqtSlot, QTimer
from PyQt5.QtGui import QImage, QPixmap, QFont

from models.visitor import VisitorModel
from models.employee import EmployeeModel
from models.audit_logs import AuditLogModel
from modules.camera import CameraThread
from modules.face_rec import FaceRecognizer
from modules.qr_code import QRPassGenerator
from modules.notifier import Notifier

class CheckinTab(QWidget):
    check_in_out_completed = pyqtSignal()  # Signal to refresh dashboard/history tabs

    def __init__(self, parent_widget, user_session, parent=None):
        super().__init__(parent)
        self.user_session = user_session
        self.camera_thread = None
        
        # Scanners cooldown
        self.last_scanned_id = None
        self.cooldown_time = 0
        
        self.selected_visitor_id = None
        
        self.init_ui()
        self.load_visitor_records()
        
        # Cooldown Timer
        self.cooldown_timer = QTimer()
        self.cooldown_timer.timeout.connect(self.check_cooldown)
        self.cooldown_timer.start(1000) # Check every 1s

    def init_ui(self):
        # Main Layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.main_layout.setSpacing(15)

        # Title
        title_label = QLabel("Visitor Entry & Exit Portal")
        title_label.setObjectName("TabTitle")
        self.main_layout.addWidget(title_label)

        # Horizontal Splitter: Left is Camera Scanner, Right is Manual Search & Details
        splitter = QSplitter(Qt.Horizontal)
        splitter.setStyleSheet("QSplitter::handle { background-color: #2d2d3f; width: 1px; }")
        self.main_layout.addWidget(splitter)

        # ------------------ LEFT COLUMN: LIVE SCANNER ------------------
        scan_frame = QFrame()
        scan_layout = QVBoxLayout(scan_frame)
        scan_layout.setContentsMargins(0, 0, 15, 0)
        scan_layout.setSpacing(12)

        s_title = QLabel("Auto Scan Terminal (QR Code / Face Recognition)")
        s_title.setFont(QFont("Segoe UI", 12, QFont.Bold))
        s_title.setStyleSheet("color: #2ecc71;")
        scan_layout.addWidget(s_title)

        # Live Feed Frame
        camera_card = QFrame()
        camera_card.setObjectName("MetricCard")
        camera_card_layout = QVBoxLayout(camera_card)
        camera_card_layout.setContentsMargins(5, 5, 5, 5)

        self.camera_view = QLabel()
        self.camera_view.setAlignment(Qt.AlignCenter)
        self.camera_view.setStyleSheet("background-color: #1a1a24; border-radius: 8px;")
        self.camera_view.setFixedSize(400, 300)
        self.camera_view.setText("Live Scanner Offline")
        self.camera_view.setFont(QFont("Segoe UI", 12))
        camera_card_layout.addWidget(self.camera_view)
        scan_layout.addWidget(camera_card)

        # Scanning status banner
        self.status_banner = QLabel("Terminal Active - Align QR Pass or Face")
        self.status_banner.setAlignment(Qt.AlignCenter)
        self.status_banner.setFont(QFont("Segoe UI", 10, QFont.Bold))
        self.status_banner.setStyleSheet("""
            QLabel {
                background-color: #1a1a24;
                color: #2ecc71;
                border: 1px solid #2d2d3f;
                border-radius: 6px;
                padding: 10px;
            }
        """)
        scan_layout.addWidget(self.status_banner)
        
        scan_layout.addStretch()
        splitter.addWidget(scan_frame)

        # ------------------ RIGHT COLUMN: MANUAL PORTAL ------------------
        manual_frame = QFrame()
        manual_layout = QVBoxLayout(manual_frame)
        manual_layout.setContentsMargins(15, 0, 0, 0)
        manual_layout.setSpacing(12)

        m_title = QLabel("Manual Verification Desk")
        m_title.setFont(QFont("Segoe UI", 12, QFont.Bold))
        m_title.setStyleSheet("color: #2ecc71;")
        manual_layout.addWidget(m_title)

        # Search box
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search visitor by Name, ID, Mobile, or Company...")
        self.search_input.textChanged.connect(self.filter_visitors)
        manual_layout.addWidget(self.search_input)

        # List of matching visitors
        self.visitor_list = QListWidget()
        self.visitor_list.setStyleSheet("""
            QListWidget {
                background-color: #1a1a24;
                border: 1px solid #2d2d3f;
                border-radius: 6px;
                padding: 5px;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #252535;
                color: #ffffff;
            }
            QListWidget::item:hover {
                background-color: #242436;
            }
            QListWidget::item:selected {
                background-color: #2ecc71;
                color: white;
            }
        """)
        self.visitor_list.itemClicked.connect(self.on_visitor_selected)
        manual_layout.addWidget(self.visitor_list)

        # Selection Details Frame
        self.details_card = QFrame()
        self.details_card.setObjectName("MetricCard")
        self.details_layout = QVBoxLayout(self.details_card)
        self.details_layout.setSpacing(8)

        self.details_title = QLabel("No Visitor Selected")
        self.details_title.setFont(QFont("Segoe UI", 11, QFont.Bold))
        self.details_title.setStyleSheet("color: #ffffff;")
        self.details_layout.addWidget(self.details_title)

        self.details_lbl = QLabel("")
        self.details_lbl.setWordWrap(True)
        self.details_lbl.setStyleSheet("color: #ffffff; line-height: 1.4;")
        self.details_layout.addWidget(self.details_lbl)

        # Action Buttons for manual portal
        actions_layout = QHBoxLayout()
        
        self.checkin_btn = QPushButton("CHECK IN")
        self.checkin_btn.setObjectName("PrimaryBtn")
        self.checkin_btn.setFixedHeight(34)
        self.checkin_btn.setCursor(Qt.PointingHandCursor)
        self.checkin_btn.clicked.connect(lambda: self.process_check_in_out(self.selected_visitor_id))
        self.checkin_btn.setEnabled(False)
        actions_layout.addWidget(self.checkin_btn)

        self.checkout_btn = QPushButton("CHECK OUT")
        self.checkout_btn.setObjectName("AccentBtn")
        self.checkout_btn.setFixedHeight(34)
        self.checkout_btn.setCursor(Qt.PointingHandCursor)
        self.checkout_btn.clicked.connect(lambda: self.process_check_in_out(self.selected_visitor_id))
        self.checkout_btn.setEnabled(False)
        actions_layout.addWidget(self.checkout_btn)

        self.details_layout.addLayout(actions_layout)
        manual_layout.addWidget(self.details_card)

        splitter.addWidget(manual_frame)

    def check_cooldown(self):
        """Decrease scan cooldown."""
        if self.cooldown_time > 0:
            self.cooldown_time -= 1
            if self.cooldown_time == 0:
                self.last_scanned_id = None
                self.status_banner.setText("Terminal Active - Align QR Pass or Face")
                self.status_banner.setStyleSheet("""
                    QLabel {
                        background-color: #1a1a24;
                        color: #2ecc71;
                        border: 1px solid #2d2d3f;
                        border-radius: 6px;
                        padding: 10px;
                    }
                """)

    def start_camera(self):
        """Start OpenCV grabber thread for active scanning."""
        if self.camera_thread is None:
            self.camera_thread = CameraThread()
            self.camera_thread.frame_ready.connect(self.on_frame_ready)
            self.camera_thread.start()

    def stop_camera(self):
        """Stop grabber thread."""
        if self.camera_thread:
            self.camera_thread.stop()
            self.camera_thread = None
            self.camera_view.setText("Live Scanner Offline")

    @pyqtSlot(QImage)
    def on_frame_ready(self, q_img):
        """Display camera frames and run background scanning algorithms."""
        # Scale to fit window
        scaled_img = q_img.scaled(self.camera_view.width(), self.camera_view.height(), 
                                  Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.camera_view.setPixmap(QPixmap.fromImage(scaled_img))

        # Check scanner cooldown
        if self.cooldown_time > 0:
            return

        # Convert QImage to OpenCV numpy array
        width = q_img.width()
        height = q_img.height()
        ptr = q_img.constBits()
        ptr.setsize(q_img.byteCount())
        arr = np.array(ptr, copy=True).reshape((height, width, 3))
        import cv2
        cv_img = cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)

        # 1. First scan for QR Code
        qr_id = QRPassGenerator.scan_qr_from_frame(cv_img)
        if qr_id:
            self.handle_scanned_visitor(qr_id, scan_method="QR Code Scan")
            return

        # 2. If no QR, perform Face Recognition scan
        face_id = FaceRecognizer.recognize_face(cv_img)
        if face_id:
            # Let's make sure they aren't matching random faces continuously
            self.handle_scanned_visitor(face_id, scan_method="Face Recognition Match")
            return

    def handle_scanned_visitor(self, visitor_id, scan_method):
        """Retrieve scanned visitor, process entry/exit transaction, apply cooldowns."""
        # Prevent double scanning in consecutive frames
        if self.last_scanned_id == visitor_id:
            return

        visitor = VisitorModel.get_visitor_by_id(visitor_id)
        if not visitor:
            print(f"[Scanner] Invalid scanned ID: {visitor_id}")
            return

        self.last_scanned_id = visitor_id
        self.cooldown_time = 4  # 4 seconds cooldown
        
        # Display feedback in banner
        self.status_banner.setText(f"SCANNED: {visitor['full_name']} ({scan_method})")
        self.status_banner.setStyleSheet("""
            QLabel {
                background-color: #243624;
                color: #00ff66;
                border: 1px solid #1f6b30;
                border-radius: 6px;
                padding: 10px;
            }
        """)

        # Execute check-in or out
        self.process_check_in_out(visitor_id)

    def process_check_in_out(self, visitor_id):
        """Determine visitor's current status and process check-in or check-out."""
        visitor = VisitorModel.get_visitor_by_id(visitor_id)
        if not visitor:
            QMessageBox.warning(self, "Transaction Failed", "Visitor record not found.")
            return

        # Resolve to actual integer ID stored in visitors table
        resolved_id = visitor['id']

        # ---- APPROVAL GUARD ----
        from models.visitor import VisitorModel as VM
        approval_info = VM.get_visit_approval_status(resolved_id)
        if approval_info:
            approval_status = approval_info.get('approval_status', 'pending')
            if approval_status == 'pending':
                QMessageBox.warning(
                    self, "Access Denied — Awaiting Approval",
                    f"⏳  {visitor['full_name']}'s visit has NOT been approved yet.\n\n"
                    "Please go to the '✅ Approvals' tab and approve the visit\n"
                    "before the visitor can check in."
                )
                return
            elif approval_status == 'rejected':
                QMessageBox.warning(
                    self, "Access Denied — Visit Rejected",
                    f"❌  {visitor['full_name']}'s visit request was REJECTED.\n\n"
                    "The visitor is not allowed to enter.\n"
                    "Please contact the host employee for more information."
                )
                return
        # ---- END APPROVAL GUARD ----

        # Fetch host details for email notification
        host = EmployeeModel.get_employee_by_id(visitor['employee_id'])

        try:
            if visitor['status'] == 'Registered' or visitor['status'] == 'CheckedOut':
                # Process Entry (Check-In)
                VisitorModel.check_in_visitor(resolved_id, self.user_session['id'])
                AuditLogModel.log_event(self.user_session['id'], "Check-In", 
                                      f"Checked in visitor {visitor['full_name']} ({resolved_id}).")
                
                # Send email notification
                if host:
                    Notifier.notify_employee_arrival(visitor, host)
                
                QMessageBox.information(
                    self, "Access Granted",
                    f"Check-In Completed!\n\n"
                    f"Welcome, {visitor['full_name']}!\n"
                    f"Host Host: {host['name'] if host else 'N/A'}\n"
                    f"Time: {time.strftime('%H:%M:%S')}"
                )
            elif visitor['status'] == 'CheckedIn':
                # Process Exit (Check-Out)
                VisitorModel.check_out_visitor(resolved_id, self.user_session['id'])
                
                # Retrieve checkout duration details
                updated_visitor = VisitorModel.get_visitor_by_id(resolved_id)
                duration = updated_visitor.get('duration_minutes', 1)
                
                AuditLogModel.log_event(self.user_session['id'], "Check-Out", 
                                      f"Checked out visitor {visitor['full_name']} ({resolved_id}). Duration: {duration} mins.")
                
                # Send email notification
                if host:
                    Notifier.notify_employee_checkout(visitor, host, duration)
                
                # Remove face encoding from live recognizer memory (since they checked out)
                FaceRecognizer.remove_visitor_encoding(resolved_id)
                
                QMessageBox.information(
                    self, "Access Revoked (Exit)",
                    f"Check-Out Completed!\n\n"
                    f"Goodbye, {visitor['full_name']}!\n"
                    f"Total Stay Duration: {duration} minutes\n"
                    f"Time: {time.strftime('%H:%M:%S')}"
                )

            # Refresh manual details and visitor list
            self.load_visitor_records()
            if self.selected_visitor_id == resolved_id:
                self.update_details_card(resolved_id)
                
            # Emit notification to update dashboard counters, history logs, etc.
            self.check_in_out_completed.emit()

        except Exception as e:
            QMessageBox.critical(self, "System Error", f"Check-In/Out processing failed: {e}")

    def load_visitor_records(self):
        """Load registered/checked-in visitors for manual portal search list."""
        self.filter_visitors()

    def filter_visitors(self):
        """Filter list of visitors based on manual search query input."""
        search_query = self.search_input.text().strip()
        self.visitor_list.clear()

        # Find visitors
        try:
            # Fetch last 30 entries for manual check-in desk
            visitors = VisitorModel.get_visitors_paginated(limit=30, offset=0, search_query=search_query)
            
            for v in visitors:
                status_color = "#2ecc71" if v['status'] == 'CheckedIn' else "#ffffff"
                if v['status'] == 'CheckedOut':
                    status_color = "#00c2cb"
                    
                display_text = f"{v['id']}  |  {v['full_name']}  ({v['company_name'] or 'N/A'})\nStatus: {v['status']}"
                
                item = QListWidgetItem(display_text)
                # Store visitor ID in item user data
                item.setData(Qt.UserRole, v['id'])
                
                self.visitor_list.addItem(item)
        except Exception as e:
            print(f"[CheckinTab] Error searching visitors: {e}")

    def on_visitor_selected(self, item):
        """Retrieve visitor details when manual item is clicked and update action buttons."""
        visitor_id = item.data(Qt.UserRole)
        self.selected_visitor_id = visitor_id
        self.update_details_card(visitor_id)

    def update_details_card(self, visitor_id):
        """Render details block in manual desk card and toggle check-in/out buttons."""
        visitor = VisitorModel.get_visitor_by_id(visitor_id)
        if not visitor:
            return

        self.details_title.setText(f"{visitor['full_name']}  ({visitor['id']})")
        
        # Build info block text
        info = f"<b>Mobile:</b> {visitor['mobile']}<br>" \
               f"<b>Company:</b> {visitor.get('company_name', 'N/A')}<br>" \
               f"<b>Purpose:</b> {visitor['purpose']}<br>" \
               f"<b>Host Host:</b> {visitor.get('employee_name', 'N/A')}<br>" \
               f"<b>Department:</b> {visitor.get('department_name', 'N/A')}<br>" \
               f"<b>Status:</b> <span style='color: #2ecc71;'>{visitor['status']}</span><br>"
               
        if visitor['status'] == 'CheckedIn':
            info += f"<b>Checked In:</b> {visitor.get('check_in_time', 'N/A')}"
            self.checkin_btn.setEnabled(False)
            self.checkout_btn.setEnabled(True)
        elif visitor['status'] == 'Registered':
            info += "<b>Access Code:</b> Pass QR Registered. Waiting for check-in."
            self.checkin_btn.setEnabled(True)
            self.checkout_btn.setEnabled(False)
        else: # CheckedOut
            info += f"<b>Duration:</b> {visitor.get('duration_minutes', 0)} mins<br>" \
                    f"<b>Checked Out:</b> {visitor.get('check_out_time', 'N/A')}"
            # Allow checking in again
            self.checkin_btn.setEnabled(True)
            self.checkout_btn.setEnabled(False)

        self.details_lbl.setText(info)
