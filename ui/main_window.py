import os
from PyQt5.QtWidgets import (QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, 
                             QFrame, QLabel, QPushButton, QStackedWidget, 
                             QMessageBox, QGridLayout, QLineEdit, QComboBox, 
                             QTextEdit, QDateEdit, QTableWidget, QTableWidgetItem, QHeaderView, QInputDialog, QDialog)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QPixmap, QImage
import qrcode

from ui.sidebar import Sidebar
from ui.theme import Theme
from ui.components import MetricCard, CameraWidget
from models.checkin import VisitModel
from models.department import DepartmentModel
from models.visitor import VisitorModel
from models.settings import SystemSettingsModel

# Import functional tabs
from ui.dashboard_tab import DashboardTab
from ui.registration_tab import RegistrationTab
from ui.approvals_tab import ApprovalsTab
from ui.checkin_tab import CheckinTab
from ui.history_tab import HistoryTab
from ui.reports_tab import ReportsTab
from ui.employees_tab import EmployeesTab
from ui.security_tab import SecurityTab
from ui.settings_tab import SettingsTab
from modules.camera import CameraThread
from web.app import start_kiosk_server

class MainWindow(QMainWindow):
    logout_requested = pyqtSignal()

    def __init__(self, user_session):
        super().__init__()
        self.user_session = user_session
        self.is_dark_mode = True
        
        self.setWindowTitle("SmartVMS - Enterprise Visitor Management System")
        self.resize(1200, 750)
        self.init_ui()
        self.apply_theme()
        
        self.kiosk_url = None
        self.kiosk_tunnel = None
        self.start_kiosk()

    def start_kiosk(self):
        try:
            _, url, tunnel_proc = start_kiosk_server(5000)
            
            # Form the final url
            if url.startswith("http"):
                self.kiosk_url = f"{url}/register"
            else:
                self.kiosk_url = f"http://{url}:5000/register"
                
            self.kiosk_tunnel = tunnel_proc
        except Exception as e:
            print(f"[MainWindow] Failed to start kiosk server: {e}")

    def init_ui(self):
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        self.main_layout = QHBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # 1. Navigation Sidebar (Imported from ui/sidebar.py)
        self.sidebar = Sidebar(self.user_session['full_name'], self.user_session['role'])
        self.sidebar.tab_changed.connect(self.switch_tab)
        self.sidebar.unlock_requested.connect(self.handle_admin_unlock)
        self.main_layout.addWidget(self.sidebar)

        # 2. Right Content Panel
        right_container = QWidget()
        right_layout = QVBoxLayout(right_container)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        # Header Bar
        header_bar = QFrame()
        header_bar.setFixedHeight(60)
        header_bar.setObjectName("HeaderBar")
        header_bar.setStyleSheet("background-color: #121214; border-bottom: 1px solid #2d2d3f;")
        
        header_layout = QHBoxLayout(header_bar)
        header_layout.setContentsMargins(20, 0, 20, 0)

        self.page_title_label = QLabel("Analytics Dashboard")
        self.page_title_label.setFont(QFont("Segoe UI", 16, QFont.Bold))
        self.page_title_label.setStyleSheet("color: #ffffff;")
        header_layout.addWidget(self.page_title_label)

        header_layout.addStretch()

        # Kiosk QR Button
        self.kiosk_btn = QPushButton("📱 Show Kiosk QR")
        self.kiosk_btn.setObjectName("PrimaryBtn")
        self.kiosk_btn.setFixedWidth(140)
        self.kiosk_btn.setFixedHeight(34)
        self.kiosk_btn.clicked.connect(self.show_kiosk_qr)
        header_layout.addWidget(self.kiosk_btn)

        # Admin Web URL Button
        self.admin_web_btn = QPushButton("🖥️ Show Admin Web")
        self.admin_web_btn.setObjectName("PrimaryBtn")
        self.admin_web_btn.setFixedWidth(140)
        self.admin_web_btn.setFixedHeight(34)
        self.admin_web_btn.clicked.connect(self.show_admin_web_qr)
        header_layout.addWidget(self.admin_web_btn)

        # Theme Selector
        self.theme_btn = QPushButton("Light Mode")
        self.theme_btn.setObjectName("SecondaryBtn")
        self.theme_btn.setFixedWidth(100)
        self.theme_btn.setFixedHeight(34)
        self.theme_btn.clicked.connect(self.toggle_theme)
        header_layout.addWidget(self.theme_btn)

        # Signout
        logout_btn = QPushButton("Logout")
        logout_btn.setObjectName("AccentBtn")
        logout_btn.setFixedWidth(80)
        logout_btn.setFixedHeight(34)
        logout_btn.clicked.connect(self.handle_logout)
        header_layout.addWidget(logout_btn)

        right_layout.addWidget(header_bar)

        # Stacked widgets tabs
        self.stacked_widget = QStackedWidget()
        
        # Initialize single shared camera thread
        self.camera_thread = CameraThread()
        
        # Instantiate actual functional tabs
        self.tab_dashboard = DashboardTab(self.user_session, self)
        self.tab_register  = RegistrationTab(self.user_session, self)
        self.tab_approvals = ApprovalsTab(self.user_session, self)
        self.tab_checkin   = CheckinTab(self, self.user_session, self)
        self.tab_history   = HistoryTab(self.user_session, self)
        self.tab_reports   = ReportsTab(self.user_session, self)
        self.tab_employees = EmployeesTab(self.user_session, self)
        self.tab_security  = SecurityTab(self.user_session, self)
        self.tab_settings  = SettingsTab(self.user_session, self)

        # Cross-tab signal wiring
        self.tab_register.registration_completed.connect(self.tab_approvals.load_pending)
        self.tab_register.registration_completed.connect(self.tab_checkin.load_visitor_records)
        self.tab_register.registration_completed.connect(self.tab_history.refresh_table)
        self.tab_register.registration_completed.connect(self.tab_dashboard.refresh_counters)
        self.tab_register.registration_completed.connect(self._refresh_approval_badge)

        self.tab_approvals.approval_completed.connect(self.tab_checkin.load_visitor_records)
        self.tab_approvals.approval_completed.connect(self.tab_dashboard.refresh_counters)
        self.tab_approvals.approval_completed.connect(self._refresh_approval_badge)

        self.tab_checkin.check_in_out_completed.connect(self.tab_dashboard.refresh_counters)
        self.tab_checkin.check_in_out_completed.connect(self.tab_history.refresh_table)
        self.tab_checkin.check_in_out_completed.connect(self.tab_security.refresh_logs)

        # Add to stacked widget (order = index)
        self.stacked_widget.addWidget(self.tab_dashboard)   # 0
        self.stacked_widget.addWidget(self.tab_register)    # 1
        self.stacked_widget.addWidget(self.tab_approvals)   # 2
        self.stacked_widget.addWidget(self.tab_checkin)     # 3
        self.stacked_widget.addWidget(self.tab_history)     # 4
        self.stacked_widget.addWidget(self.tab_reports)     # 5
        self.stacked_widget.addWidget(self.tab_employees)   # 6
        self.stacked_widget.addWidget(self.tab_security)    # 7
        self.stacked_widget.addWidget(self.tab_settings)    # 8

        right_layout.addWidget(self.stacked_widget)
        self.main_layout.addWidget(right_container)
        
        # Explicitly switch to Dashboard (0) on startup to ensure clean camera state
        self.switch_tab(0)

    def _refresh_approval_badge(self):
        """Update the sidebar approval count badge."""
        try:
            count = len(VisitorModel.get_pending_visits())
            self.sidebar.update_pending_badge(count)
        except Exception:
            pass

    def switch_tab(self, index):
        # 1. Disconnect camera from any previous tab
        if hasattr(self, 'camera_thread') and self.camera_thread:
            try:
                self.camera_thread.frame_ready.disconnect()
            except (TypeError, AttributeError):
                pass

        # 2. Switch stacked widget
        self.stacked_widget.setCurrentIndex(index)
        titles = [
            "Analytics Dashboard",          # 0
            "Visitor Registration Form",     # 1
            "Approval Queue",               # 2
            "Visitor Check-In & Check-Out", # 3
            "Visitor History Logs",         # 4
            "Report Exporter Panel",        # 5
            "Employee Management",          # 6
            "Security Audit Trails",        # 7
            "Email & System Settings",      # 8
        ]
        if 0 <= index < len(titles):
            self.page_title_label.setText(titles[index])
        
        # 3. Camera management — only for Register (1) and Check-In (3)
        if index == 1:   # Register Visitor
            self.camera_thread.frame_ready.connect(self.tab_register.update_camera_frame)
            if not self.camera_thread.isRunning():
                self.camera_thread.start()
        elif index == 3:  # Check-In / Out
            self.camera_thread.frame_ready.connect(self.tab_checkin.on_frame_ready)
            if not self.camera_thread.isRunning():
                self.camera_thread.start()
        else:
            if self.camera_thread.isRunning():
                self.camera_thread.stop()
            self.tab_register.camera_view.setText("Webcam Feed Offline")
            self.tab_checkin.camera_view.setText("Live Scanner Offline")

        # 4. Trigger per-tab refresh
        current_tab = self.stacked_widget.currentWidget()
        if index == 0:   # Dashboard
            if hasattr(current_tab, 'refresh_counters'):
                current_tab.refresh_counters()
            if hasattr(current_tab, 'render_charts'):
                current_tab.render_charts()
        elif index == 2:  # Approvals
            if hasattr(current_tab, 'load_pending'):
                current_tab.load_pending()
            self._refresh_approval_badge()
        elif index == 3:  # Check-in
            if hasattr(current_tab, 'load_visitor_records'):
                current_tab.load_visitor_records()
        elif index == 4:  # History
            if hasattr(current_tab, 'refresh_table'):
                current_tab.refresh_table()
        elif index == 6:  # Employees — reload list + refresh reg-tab employee cache
            if hasattr(current_tab, 'load_employees'):
                current_tab.load_employees()
            # Refresh the employee list used by the registration host-search
            if hasattr(self.tab_register, '_load_all_employees'):
                self.tab_register._load_all_employees()
        elif index == 7:  # Security & Logs
            if hasattr(current_tab, 'refresh_logs'):
                current_tab.refresh_logs()
            if hasattr(current_tab, 'refresh_users_list'):
                current_tab.refresh_users_list()

    def toggle_theme(self):
        self.is_dark_mode = not self.is_dark_mode
        self.apply_theme()

    def apply_theme(self):
        stylesheet = Theme.get_stylesheet(self.is_dark_mode)
        self.setStyleSheet(stylesheet)
        self.theme_btn.setText("Light Mode" if self.is_dark_mode else "Dark Mode")
        
        # Notify dashboard to redraw charts with correct theme settings
        if hasattr(self, 'tab_dashboard') and hasattr(self.tab_dashboard, 'set_chart_theme'):
            self.tab_dashboard.set_chart_theme(self.is_dark_mode)

    def handle_logout(self):
        self.logout_requested.emit()
        self.close()

    def handle_admin_unlock(self):
        code, ok = QInputDialog.getText(self, "Unlock Admin Portal", "Enter Admin Secret Code:", QLineEdit.Password)
        if ok and code:
            correct_code = SystemSettingsModel.get_setting("admin_secret_code", "NONE")
            if code == correct_code:
                # Elevate privileges for this session
                self.user_session['role'] = 'Admin'
                QMessageBox.information(self, "Unlocked", "Admin Portal Unlocked successfully.")
                
                # Replace Sidebar
                self.main_layout.removeWidget(self.sidebar)
                self.sidebar.deleteLater()
                self.sidebar = Sidebar(self.user_session['full_name'], self.user_session['role'])
                self.sidebar.tab_changed.connect(self.switch_tab)
                self.sidebar.unlock_requested.connect(self.handle_admin_unlock)
                self.main_layout.insertWidget(0, self.sidebar)
            else:
                QMessageBox.warning(self, "Access Denied", "Incorrect Secret Code.")

    def show_kiosk_qr(self):
        try:
            if not self.kiosk_url:
                QMessageBox.warning(self, "Error", "Kiosk server is not running.")
                return
                
            # Determine if it's a local fallback or true public tunnel
            is_local = "192.168" in self.kiosk_url or "10." in self.kiosk_url or "127." in self.kiosk_url or ".local" in self.kiosk_url
                
            qr = qrcode.QRCode(version=None, box_size=10, border=4)
            qr.add_data(self.kiosk_url)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Save to temp file to avoid QImage conversion issues that can break QR scannability
            import tempfile
            import os
            qr_path = os.path.join(tempfile.gettempdir(), "smartvms_kiosk_qr.png")
            img.save(qr_path)
            
            pixmap = QPixmap(qr_path)
            
            dlg = QDialog(self)
            dlg.setWindowTitle("Visitor Self-Registration Kiosk")
            dlg.setMinimumWidth(500)
            layout = QVBoxLayout(dlg)
            
            if is_local:
                lbl_warn = QLabel("⚠️ NO INTERNET TUNNEL: Visitors MUST be connected to your local office Wi-Fi to scan this.")
                lbl_warn.setStyleSheet("color: #ffcc00; font-weight: bold; font-size: 14px;")
                lbl_warn.setAlignment(Qt.AlignCenter)
                layout.addWidget(lbl_warn)
            else:
                lbl_info = QLabel("Ask visitors to scan this QR code with their mobile camera to check in.\n(Works on 4G/5G and Wi-Fi)")
                lbl_info.setStyleSheet("color: white; font-size: 14px;")
                lbl_info.setAlignment(Qt.AlignCenter)
                layout.addWidget(lbl_info)
            
            lbl_url = QLabel(self.kiosk_url)
            lbl_url.setStyleSheet("color: #2ecc71; font-weight: bold; font-size: 16px;")
            lbl_url.setAlignment(Qt.AlignCenter)
            layout.addWidget(lbl_url)
            
            lbl_qr = QLabel()
            # Do NOT use SmoothTransformation! It blurs the sharp edges of the QR code and breaks scanners.
            # Use the raw, perfectly sharp pixmap.
            lbl_qr.setPixmap(pixmap)
            lbl_qr.setAlignment(Qt.AlignCenter)
            layout.addWidget(lbl_qr)
            
            # Ensure the dialog is large enough so it doesn't clip the image
            dlg.resize(550, 650)
            dlg.exec_()
        except Exception as e:
            QMessageBox.critical(self, "QR Generation Error", f"Failed to generate QR Code. Error: {str(e)}")

    def show_admin_web_qr(self):
        try:
            if not self.kiosk_url:
                QMessageBox.warning(self, "Error", "Kiosk server is not running.")
                return
                
            admin_url = self.kiosk_url.replace('/register', '/admin')
            # Determine if it's a local fallback or true public tunnel
            is_local = "192.168" in admin_url or "10." in admin_url or "127." in admin_url or ".local" in admin_url
                
            qr = qrcode.QRCode(version=None, box_size=10, border=4)
            qr.add_data(admin_url)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")
            
            import tempfile
            import os
            qr_path = os.path.join(tempfile.gettempdir(), "smartvms_admin_qr.png")
            img.save(qr_path)
            
            pixmap = QPixmap(qr_path)
            
            dlg = QDialog(self)
            dlg.setWindowTitle("Operator Web Admin Portal")
            dlg.setMinimumWidth(500)
            layout = QVBoxLayout(dlg)
            
            if is_local:
                lbl_warn = QLabel("⚠️ NO INTERNET TUNNEL: Friends MUST be connected to your local office Wi-Fi to scan this.")
                lbl_warn.setStyleSheet("color: #ffcc00; font-weight: bold; font-size: 14px;")
                lbl_warn.setAlignment(Qt.AlignCenter)
                layout.addWidget(lbl_warn)
            else:
                lbl_info = QLabel("Share this link or scan this QR code to access the Admin Console.\n(Valid credentials required to log in)")
                lbl_info.setStyleSheet("color: white; font-size: 14px;")
                lbl_info.setAlignment(Qt.AlignCenter)
                layout.addWidget(lbl_info)
            
            lbl_url = QLabel(admin_url)
            lbl_url.setStyleSheet("color: #2ecc71; font-weight: bold; font-size: 16px;")
            lbl_url.setAlignment(Qt.AlignCenter)
            layout.addWidget(lbl_url)
            
            lbl_qr = QLabel()
            lbl_qr.setPixmap(pixmap)
            lbl_qr.setAlignment(Qt.AlignCenter)
            layout.addWidget(lbl_qr)
            
            dlg.resize(550, 650)
            dlg.exec_()
        except Exception as e:
            QMessageBox.critical(self, "QR Generation Error", f"Failed to generate QR Code. Error: {str(e)}")

    # ==========================================
    # CORE TAB WIDGETS CREATION (PHASE 1 SHELLS)
    # ==========================================
    def create_dashboard_widget(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Metric cards row
        cards_layout = QHBoxLayout()
        self.card_today = MetricCard("Today's Total", "0", "Visits checked-in today", "#2ecc71")
        self.card_active = MetricCard("Active Now", "0", "Visitors currently inside", "#ff2e93")
        self.card_completed = MetricCard("Completed Today", "0", "Completed departures", "#00ff66")
        
        cards_layout.addWidget(self.card_today)
        cards_layout.addWidget(self.card_active)
        cards_layout.addWidget(self.card_completed)
        layout.addLayout(cards_layout)
        
        # Grid layout for quick details
        info_grid = QGridLayout()
        info_box = QFrame()
        info_box.setObjectName("MetricCard")
        ib_layout = QVBoxLayout(info_box)
        ib_layout.addWidget(QLabel("<b>Visitor Management System Overview</b>"))
        ib_layout.addWidget(QLabel("This system automates and records corporate visitor activities. Navigate using the sidebar menu."))
        info_grid.addWidget(info_box, 0, 0)
        layout.addLayout(info_grid)
        layout.addStretch()
        return widget

    def create_register_widget(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        form_frame = QFrame()
        form_frame.setObjectName("MetricCard")
        form_layout = QVBoxLayout(form_frame)
        
        form_layout.addWidget(QLabel("<b>Register New Visitor Profile</b>"))
        
        # Add basic form inputs
        self.reg_name = QLineEdit()
        self.reg_name.setPlaceholderText("Full Name")
        form_layout.addWidget(self.reg_name)
        
        self.reg_mobile = QLineEdit()
        self.reg_mobile.setPlaceholderText("Mobile Number")
        form_layout.addWidget(self.reg_mobile)
        
        self.reg_company = QLineEdit()
        self.reg_company.setPlaceholderText("Company Name")
        form_layout.addWidget(self.reg_company)
        
        register_btn = QPushButton("Submit Registration")
        register_btn.setObjectName("PrimaryBtn")
        form_layout.addWidget(register_btn)
        
        layout.addWidget(form_frame)
        layout.addStretch()
        return widget

    def create_checkin_widget(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        card = QFrame()
        card.setObjectName("MetricCard")
        card_layout = QVBoxLayout(card)
        card_layout.addWidget(QLabel("<b>Live Scanning & Entrance Station</b>"))
        
        camera_widget = CameraWidget(placeholder="Entrance Webcam (Simulation Mode Active)")
        card_layout.addWidget(camera_widget)
        
        layout.addWidget(card)
        layout.addStretch()
        return widget

    def create_history_widget(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        table = QTableWidget()
        table.setColumnCount(6)
        table.setHorizontalHeaderLabels(["Code", "Visitor Name", "Mobile", "Host", "Check-In", "Status"])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(table)
        return widget

    def create_reports_widget(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        card = QFrame()
        card.setObjectName("MetricCard")
        card_layout = QVBoxLayout(card)
        card_layout.addWidget(QLabel("<b>Export System Records</b>"))
        
        export_btn = QPushButton("COMPILE & EXPORT PDF REPORT")
        export_btn.setObjectName("PrimaryBtn")
        card_layout.addWidget(export_btn)
        
        layout.addWidget(card)
        layout.addStretch()
        return widget

    def create_security_widget(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        table = QTableWidget()
        table.setColumnCount(4)
        table.setHorizontalHeaderLabels(["Timestamp", "User", "Action", "Details"])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(table)
        return widget

    def closeEvent(self, event):
        """Ensure shared camera thread is stopped before exiting."""
        if hasattr(self, 'camera_thread') and self.camera_thread:
            try:
                self.camera_thread.stop()
            except Exception as e:
                print(f"[MainWindow] Error stopping camera: {e}")
        event.accept()
