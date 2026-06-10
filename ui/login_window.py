import sys
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QFrame, QMessageBox, QAction, QComboBox, QCheckBox)
from PyQt5.QtCore import Qt, pyqtSignal, QSettings
from PyQt5.QtGui import QFont, QIcon
from models.user import UserModel

class SignupDialog(QDialog):
    """Dialog to allow registration of new system operators directly from the login screen."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("SmartVMS - Register Operator")
        self.resize(380, 420)
        self.init_ui()
        self.apply_styles()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(10)

        # Header Title
        title_lbl = QLabel("Create Account")
        title_lbl.setFont(QFont("Segoe UI", 16, QFont.Bold))
        title_lbl.setAlignment(Qt.AlignCenter)
        title_lbl.setStyleSheet("color: #111111; margin-bottom: 10px;")
        layout.addWidget(title_lbl)

        # Username Field
        layout.addWidget(QLabel("Username *"))
        self.u_username = QLineEdit()
        self.u_username.setPlaceholderText("e.g. john_doe")
        layout.addWidget(self.u_username)

        # Full Name Field
        layout.addWidget(QLabel("Full Name *"))
        self.u_fullname = QLineEdit()
        self.u_fullname.setPlaceholderText("First & Last Name")
        layout.addWidget(self.u_fullname)

        # Email Field
        layout.addWidget(QLabel("Email Address *"))
        self.u_email = QLineEdit()
        self.u_email.setPlaceholderText("name@company.com")
        layout.addWidget(self.u_email)

        # Password Field
        layout.addWidget(QLabel("Password *"))
        self.u_password = QLineEdit()
        self.u_password.setPlaceholderText("Choose a secure password")
        self.u_password.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.u_password)

        # Role Field
        layout.addWidget(QLabel("Role *"))
        self.u_role = QComboBox()
        self.u_role.addItems(["admin", "receptionist", "security"])
        layout.addWidget(self.u_role)

        layout.addSpacing(15)

        # Submit button
        self.submit_btn = QPushButton("Register Operator")
        self.submit_btn.setFixedHeight(36)
        self.submit_btn.setCursor(Qt.PointingHandCursor)
        self.submit_btn.clicked.connect(self.handle_signup)
        layout.addWidget(self.submit_btn)

    def apply_styles(self):
        self.setStyleSheet("""
            QDialog {
                background-color: #aae1f8; /* Matching light sky blue */
            }
            QLabel {
                color: #1a252f;
                font-family: 'Segoe UI', Arial;
                font-weight: 600;
                font-size: 11px;
            }
            QLineEdit, QComboBox {
                background-color: #ffffff;
                border: 1px solid #e1e4e8;
                border-radius: 2px;
                padding: 8px;
                color: #000000;
            }
            QPushButton {
                background-color: #e0f8ff;
                border: 1px solid #99d8ee;
                color: #1a252f;
                border-radius: 2px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #ffffff;
                border: 1px solid #0b5394;
            }
        """)

    def handle_signup(self):
        username = self.u_username.text().strip()
        fullname = self.u_fullname.text().strip()
        email = self.u_email.text().strip()
        password = self.u_password.text()
        role = self.u_role.currentText()

        if not username or not fullname or not email or not password:
            QMessageBox.warning(self, "Validation Error", "All fields marked with * are required.")
            return

        # Simple email pattern validation
        if "@" not in email or "." not in email:
            QMessageBox.warning(self, "Validation Error", "Please enter a valid Email Address.")
            return

        success, err_msg = UserModel.create_user(username, fullname, email, password, role)
        if success:
            QMessageBox.information(
                self, "Success", 
                f"Operator account created successfully!\n\n"
                f"You can now log in using the email:\n{email}"
            )
            self.accept()
        else:
            QMessageBox.warning(self, "Registration Failed", err_msg)


class LoginWindow(QDialog):
    login_successful = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("SmartVMS - Operator Login")
        self.resize(450, 420)
        self.setWindowFlags(self.windowFlags() | Qt.CustomizeWindowHint)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        
        self.settings = QSettings("SmartVMS", "VisitorApp")
        
        self.init_ui()
        self.apply_styles()
        self.load_credentials()

    def init_ui(self):
        # Main vertical layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(40, 40, 40, 30)
        self.main_layout.setSpacing(12)

        # 1. Title: Admin Login
        self.title_label = QLabel("Admin Login")
        self.title_label.setFont(QFont("Segoe UI", 22, QFont.Bold))
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet("color: #111111; margin-bottom: 15px;")
        self.main_layout.addWidget(self.title_label)

        # 2. Username/Email Section
        username_lbl = QLabel("Username or Email")
        username_lbl.setFont(QFont("Segoe UI", 12))
        username_lbl.setStyleSheet("color: #1a252f; font-weight: 600;")
        self.main_layout.addWidget(username_lbl)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Enter your username or email")
        self.username_input.setFont(QFont("Segoe UI", 11))
        self.main_layout.addWidget(self.username_input)

        # 3. Password Section
        pass_lbl = QLabel("Password")
        pass_lbl.setFont(QFont("Segoe UI", 12))
        pass_lbl.setStyleSheet("color: #1a252f; font-weight: 600;")
        self.main_layout.addWidget(pass_lbl)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Enter your password")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setFont(QFont("Segoe UI", 11))
        self.password_input.returnPressed.connect(self.handle_login)
        
        # Add visibility toggle action inside QLineEdit
        self.toggle_action = QAction("👁", self)
        self.password_input.addAction(self.toggle_action, QLineEdit.TrailingPosition)
        self.toggle_action.triggered.connect(self.toggle_password_visibility)
        
        self.main_layout.addWidget(self.password_input)

        # Remember Me Checkbox
        self.remember_cb = QCheckBox("Remember Me")
        self.remember_cb.setStyleSheet("color: #111111; font-weight: bold;")
        self.main_layout.addWidget(self.remember_cb)

        # Feedback Error message
        self.error_label = QLabel("")
        self.error_label.setStyleSheet("color: #d32f2f; font-weight: 500;")
        self.error_label.setAlignment(Qt.AlignCenter)
        self.main_layout.addWidget(self.error_label)

        # 4. Submit Button (Centered in horizontal layout)
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        self.submit_btn = QPushButton("Submit")
        self.submit_btn.setObjectName("SubmitBtn")
        self.submit_btn.setFont(QFont("Segoe UI", 11))
        self.submit_btn.setFixedWidth(130)
        self.submit_btn.setFixedHeight(38)
        self.submit_btn.setCursor(Qt.PointingHandCursor)
        self.submit_btn.clicked.connect(self.handle_login)
        
        btn_layout.addWidget(self.submit_btn)
        btn_layout.addStretch()
        self.main_layout.addLayout(btn_layout)
        
        self.main_layout.addSpacing(10)

        # 5. Bottom Links: Signup & Forgot Password
        footer_layout = QHBoxLayout()
        
        self.signup_btn = QPushButton("New user? Signup")
        self.signup_btn.setStyleSheet("""
            QPushButton {
                color: #0b5394;
                background: transparent;
                border: none;
                text-align: left;
                text-decoration: underline;
                font-size: 11px;
            }
            QPushButton:hover {
                color: #0022cc;
            }
        """)
        self.signup_btn.setCursor(Qt.PointingHandCursor)
        self.signup_btn.clicked.connect(self.handle_signup_click)
        footer_layout.addWidget(self.signup_btn)
        
        footer_layout.addStretch()
        
        self.forgot_btn = QPushButton("Forgot Password")
        self.forgot_btn.setStyleSheet("""
            QPushButton {
                color: #0b5394;
                background: transparent;
                border: none;
                text-align: right;
                text-decoration: underline;
                font-size: 11px;
            }
            QPushButton:hover {
                color: #0022cc;
            }
        """)
        self.forgot_btn.setCursor(Qt.PointingHandCursor)
        self.forgot_btn.clicked.connect(self.handle_forgot_click)
        footer_layout.addWidget(self.forgot_btn)

        self.main_layout.addLayout(footer_layout)

    def load_credentials(self):
        saved_token = self.settings.value("session_token", "")
        if saved_token:
            # Auto-login if token is valid
            user = UserModel.authenticate_by_token(saved_token)
            if user:
                print(f"[Login] Auto-login successful via session token.")
                # Delay emit slightly to allow UI to instantiate properly
                from PyQt5.QtCore import QTimer
                QTimer.singleShot(100, lambda: self.finish_auto_login(user))
            else:
                self.settings.remove("session_token")
                
    def finish_auto_login(self, user):
        self.login_successful.emit(user)
        self.accept()

    def apply_styles(self):
        # Apply light sky-blue style corresponding to user reference image
        self.setStyleSheet("""
            QDialog {
                background-color: #aae1f8; /* Light sky blue */
            }
            QLineEdit {
                background-color: #ffffff;
                border: 1px solid #e1e4e8;
                border-radius: 2px;
                padding: 10px;
                color: #000000;
            }
            QLineEdit:focus {
                border: 1px solid #0b5394;
            }
            QPushButton#SubmitBtn {
                background-color: #e0f8ff;
                border: 1px solid #99d8ee;
                color: #1a252f;
                border-radius: 2px;
                font-weight: 500;
            }
            QPushButton#SubmitBtn:hover {
                background-color: #ffffff;
                border: 1px solid #0b5394;
            }
        """)

    def toggle_password_visibility(self):
        """Toggle QLineEdit echo mode between Password and Normal text."""
        if self.password_input.echoMode() == QLineEdit.Password:
            self.password_input.setEchoMode(QLineEdit.Normal)
            self.toggle_action.setText("🙈") # Hidden eye
        else:
            self.password_input.setEchoMode(QLineEdit.Password)
            self.toggle_action.setText("👁") # Open eye

    def handle_login(self):
        username_or_email = self.username_input.text().strip()
        password = self.password_input.text()

        if not username_or_email or not password:
            self.error_label.setText("Please fill out all fields.")
            return

        self.error_label.setText("")
        self.submit_btn.setEnabled(False)
        self.submit_btn.setText("Submitting...")

        # Authenticate by Username or Email
        user = UserModel.authenticate(username_or_email, password)
        
        if user:
            # Handle Remember Me Session Token
            if self.remember_cb.isChecked():
                token = UserModel.generate_session_token(user['id'])
                self.settings.setValue("session_token", token)
            else:
                self.settings.remove("session_token")
            
            # Emit login success
            self.login_successful.emit(user)
            self.accept()
        else:
            self.error_label.setText("Invalid username/email or password.")
            self.submit_btn.setEnabled(True)
            self.submit_btn.setText("Submit")
            self.password_input.clear()
            self.password_input.setFocus()

    def handle_signup_click(self):
        """Open a functional dialog allowing registration of new operators."""
        dlg = SignupDialog(self)
        dlg.exec_()

    def handle_forgot_click(self):
        QMessageBox.information(self, "Password Reset", "Please contact your system administrator to recover or reset your account password.")
