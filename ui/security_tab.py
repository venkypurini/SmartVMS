from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QComboBox, QPushButton, QFrame, 
                             QTableWidget, QTableWidgetItem, QHeaderView, 
                             QSplitter, QMessageBox, QInputDialog)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor

from models.audit_logs import AuditLogModel
from models.user import UserModel
from models.settings import SystemSettingsModel
import random
import string

class SecurityTab(QWidget):
    def __init__(self, user_session, parent=None):
        super().__init__(parent)
        self.user_session = user_session
        self.init_ui()
        self.refresh_logs()
        self.refresh_users_list()

    def init_ui(self):
        # Main Layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.main_layout.setSpacing(15)

        # Tab Header Title
        title_label = QLabel("Security Audit Logs & Account Administration")
        title_label.setObjectName("TabTitle")
        self.main_layout.addWidget(title_label)

        # Splitter to separate Audit Logs (Left) and User Management (Right)
        splitter = QSplitter(Qt.Horizontal)
        splitter.setStyleSheet("QSplitter::handle { background-color: #2d2d3f; width: 1px; }")
        self.main_layout.addWidget(splitter)

        # ------------------ LEFT SIDE: AUDIT LOGS GRID ------------------
        logs_frame = QFrame()
        logs_layout = QVBoxLayout(logs_frame)
        logs_layout.setContentsMargins(0, 0, 15, 0)
        logs_layout.setSpacing(12)

        l_title = QLabel("System Activity Audit Trail")
        l_title.setFont(QFont("Segoe UI", 12, QFont.Bold))
        l_title.setStyleSheet("color: #2ecc71;")
        logs_layout.addWidget(l_title)

        # Search Bar for Logs
        self.search_logs_input = QLineEdit()
        self.search_logs_input.setPlaceholderText("Filter logs by Action, Details, or Username...")
        self.search_logs_input.textChanged.connect(self.refresh_logs)
        logs_layout.addWidget(self.search_logs_input)

        # Logs Table
        self.logs_table = QTableWidget()
        self.logs_table.setColumnCount(5)
        self.logs_table.setHorizontalHeaderLabels(["Timestamp", "User", "Role", "Action", "Details"])
        self.logs_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.logs_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.logs_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.logs_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.logs_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.logs_table.setSelectionMode(QTableWidget.ExtendedSelection)
        self.logs_table.verticalHeader().setVisible(False)
        self.logs_table.itemSelectionChanged.connect(self._on_logs_selection)
        logs_layout.addWidget(self.logs_table)

        # Delete Selected Logs Button Row
        logs_btn_row = QHBoxLayout()
        self.delete_logs_btn = QPushButton("🗑️  Delete Selected Logs")
        self.delete_logs_btn.setStyleSheet(
            "background-color:#3a1a1a; color:#ff4444; border:1px solid #6b1f1f;"
            "border-radius:6px; padding:6px 12px; font-weight:bold;"
        )
        self.delete_logs_btn.setEnabled(False)
        self.delete_logs_btn.clicked.connect(self._delete_selected_logs)
        logs_btn_row.addWidget(self.delete_logs_btn)
        logs_btn_row.addStretch()
        logs_layout.addLayout(logs_btn_row)

        splitter.addWidget(logs_frame)

        # ------------------ RIGHT SIDE: USER ADMINISTRATION ------------------
        users_frame = QFrame()
        self.users_layout = QVBoxLayout(users_frame)
        self.users_layout.setContentsMargins(15, 0, 0, 0)
        self.users_layout.setSpacing(12)

        u_title = QLabel("System Operator Accounts")
        u_title.setFont(QFont("Segoe UI", 12, QFont.Bold))
        u_title.setStyleSheet("color: #2ecc71;")
        self.users_layout.addWidget(u_title)

        # Check Roles: Admin role gets full user management privileges
        if self.user_session['role'].lower() == 'admin':
            # Create User Section Card
            self.create_card = QFrame()
            self.create_card.setObjectName("MetricCard")
            create_layout = QVBoxLayout(self.create_card)
            create_layout.setSpacing(8)

            c_lbl = QLabel("Create Operator Account")
            c_lbl.setFont(QFont("Segoe UI", 11, QFont.Bold))
            c_lbl.setStyleSheet("color: #2ecc71;")
            create_layout.addWidget(c_lbl)

            # Input fields
            self.u_username = QLineEdit()
            self.u_username.setPlaceholderText("Username")
            create_layout.addWidget(self.u_username)

            self.u_fullname = QLineEdit()
            self.u_fullname.setPlaceholderText("Full Name")
            create_layout.addWidget(self.u_fullname)

            self.u_email = QLineEdit()
            self.u_email.setPlaceholderText("Email Address")
            create_layout.addWidget(self.u_email)

            self.u_password = QLineEdit()
            self.u_password.setPlaceholderText("Password")
            self.u_password.setEchoMode(QLineEdit.Password)
            create_layout.addWidget(self.u_password)

            self.u_role = QComboBox()
            self.u_role.addItems(["Receptionist", "Security", "Admin"])
            create_layout.addWidget(self.u_role)

            self.create_btn = QPushButton("CREATE ACCOUNT")
            self.create_btn.setObjectName("PrimaryBtn")
            self.create_btn.clicked.connect(self.create_system_user)
            create_layout.addWidget(self.create_btn)

            self.users_layout.addWidget(self.create_card)

            # User Accounts Table
            self.users_table = QTableWidget()
            self.users_table.setColumnCount(3)
            self.users_table.setHorizontalHeaderLabels(["Username", "Role", "Action"])
            self.users_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            self.users_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
            self.users_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
            self.users_table.setEditTriggers(QTableWidget.NoEditTriggers)
            self.users_table.verticalHeader().setVisible(False)
            self.users_layout.addWidget(self.users_table)
            
            # ----------------------------------------------------
            # Admin Secret Code Section
            # ----------------------------------------------------
            self.secret_card = QFrame()
            self.secret_card.setObjectName("MetricCard")
            secret_layout = QVBoxLayout(self.secret_card)
            secret_layout.setSpacing(8)

            s_lbl = QLabel("Admin Secret Code Generator")
            s_lbl.setFont(QFont("Segoe UI", 11, QFont.Bold))
            s_lbl.setStyleSheet("color: #2ecc71;")
            secret_layout.addWidget(s_lbl)
            
            s_desc = QLabel("Share this code securely with staff if they need temporary Admin Portal access.")
            s_desc.setWordWrap(True)
            s_desc.setStyleSheet("color: #ffffff;")
            secret_layout.addWidget(s_desc)
            
            s_row = QHBoxLayout()
            self.secret_display = QLineEdit()
            self.secret_display.setReadOnly(True)
            self.secret_display.setAlignment(Qt.AlignCenter)
            self.secret_display.setFont(QFont("Consolas", 14, QFont.Bold))
            
            # Load current code if exists
            current_code = SystemSettingsModel.get_setting("admin_secret_code", "NONE")
            self.secret_display.setText(current_code)
            
            s_btn = QPushButton("Generate New Code")
            s_btn.setObjectName("SecondaryBtn")
            s_btn.clicked.connect(self.generate_secret_code)
            
            s_row.addWidget(self.secret_display)
            s_row.addWidget(s_btn)
            secret_layout.addLayout(s_row)
            
            self.users_layout.addWidget(self.secret_card)

        else:
            # Non-Admin restrict message
            lock_card = QFrame()
            lock_card.setObjectName("MetricCard")
            lock_layout = QVBoxLayout(lock_card)
            
            lock_lbl = QLabel(
                "🔒 Account Administration Restricted\n\n"
                "User management operations are restricted to System Administrators.\n"
                "Please contact your administrator to register new operators or request password resets."
            )
            lock_lbl.setWordWrap(True)
            lock_lbl.setFont(QFont("Segoe UI", 10))
            lock_lbl.setStyleSheet("color: #ff9f43; line-height: 1.5;")
            lock_lbl.setAlignment(Qt.AlignCenter)
            lock_layout.addWidget(lock_lbl)
            self.users_layout.addWidget(lock_card)
            self.users_layout.addStretch()

        splitter.addWidget(users_frame)

    def refresh_logs(self):
        """Fetch audit trail logs matching filter query and display them in table."""
        search = self.search_logs_input.text().strip()
        try:
            logs = AuditLogModel.get_logs(limit=100, search_query=search)
            self.logs_table.setRowCount(0)
            self.logs_table.setRowCount(len(logs))
            
            for row_idx, l in enumerate(logs):
                t_item = QTableWidgetItem(l['timestamp'])
                t_item.setData(Qt.UserRole, l['id'])
                t_item.setForeground(QColor("#ffffff"))
                self.logs_table.setItem(row_idx, 0, t_item)
                
                u_item = QTableWidgetItem(l['username'] or "SYSTEM")
                u_item.setForeground(QColor("#ffffff"))
                self.logs_table.setItem(row_idx, 1, u_item)
                
                role_item = QTableWidgetItem(l['role'] or "N/A")
                role_item.setTextAlignment(Qt.AlignCenter)
                role_item.setForeground(QColor("#ffffff"))
                self.logs_table.setItem(row_idx, 2, role_item)
                
                action_item = QTableWidgetItem(l['action'])
                action_item.setFont(QFont("Segoe UI", 9, QFont.Bold))
                
                # Color code actions
                if l['action'] in ["Login", "Check-In"]:
                    action_item.setForeground(QColor("#00ff66"))
                elif l['action'] in ["Logout", "Check-Out"]:
                    action_item.setForeground(QColor("#ff9f43"))
                elif l['action'] in ["Register Visitor", "Create User"]:
                    action_item.setForeground(QColor("#2ecc71"))
                else:
                    action_item.setForeground(QColor("#ff2e93"))
                    
                self.logs_table.setItem(row_idx, 3, action_item)
                
                d_item = QTableWidgetItem(l['details'] or "")
                d_item.setForeground(QColor("#ffffff"))
                self.logs_table.setItem(row_idx, 4, d_item)
        except Exception as e:
            print(f"[SecurityTab] Error loading audit logs: {e}")

    def refresh_users_list(self):
        """Load list of system operator users in Admin-level table view."""
        if self.user_session['role'].lower() != 'admin':
            return
            
        try:
            users = UserModel.get_all_users()
            self.users_table.setRowCount(0)
            self.users_table.setRowCount(len(users))
            
            for row_idx, u in enumerate(users):
                username_item = QTableWidgetItem(u['username'])
                username_item.setForeground(QColor("#ffffff"))
                self.users_table.setItem(row_idx, 0, username_item)
                
                role_val_item = QTableWidgetItem(u['role'])
                role_val_item.setForeground(QColor("#ffffff"))
                self.users_table.setItem(row_idx, 1, role_val_item)
                
                # Delete account button
                del_btn = QPushButton("Delete")
                del_btn.setObjectName("AccentBtn")
                del_btn.setFixedHeight(22)
                del_btn.setCursor(Qt.PointingHandCursor)
                
                # Disable deleting oneself
                if u['id'] == self.user_session['id']:
                    del_btn.setEnabled(False)
                    del_btn.setToolTip("Cannot delete currently logged-in account.")
                    
                del_btn.clicked.connect(lambda checked, uid=u['id'], name=u['username']: self.delete_system_user(uid, name))
                self.users_table.setCellWidget(row_idx, 2, del_btn)
                
        except Exception as e:
            print(f"[SecurityTab] Error loading operator accounts: {e}")

    def create_system_user(self):
        """Register a new system user profile after validation."""
        username = self.u_username.text().strip()
        fullname = self.u_fullname.text().strip()
        email = self.u_email.text().strip()
        password = self.u_password.text()
        role = self.u_role.currentText()

        # Validation checks
        if not username or not fullname or not password:
            QMessageBox.warning(self, "Validation Error", "Username, Full Name, and Password are required.")
            return

        try:
            success, err_msg = UserModel.create_user(username, fullname, email, password, role)
            if success:
                AuditLogModel.log_event(self.user_session['id'], "Create User", f"Created new operator account: '{username}' (Role: {role}).")
                
                QMessageBox.information(self, "Success", f"Operator account '{username}' created successfully!")
                
                # Clear fields
                self.u_username.clear()
                self.u_fullname.clear()
                self.u_email.clear()
                self.u_password.clear()
                self.u_role.setCurrentIndex(0)
                
                self.refresh_users_list()
                self.refresh_logs()
            else:
                QMessageBox.warning(self, "Creation Failed", err_msg)
        except Exception as e:
            QMessageBox.critical(self, "System Error", f"Failed to create user account: {e}")

    def delete_system_user(self, user_id, username):
        """Prompt confirmation and delete system operator account."""
        reply = QMessageBox.question(
            self, "Confirm Delete",
            f"Are you sure you want to delete operator account '{username}'?\nThis action cannot be undone.",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                UserModel.delete_user(user_id)
                AuditLogModel.log_event(self.user_session['id'], "Delete User", f"Deleted operator account: '{username}'.")
                
                QMessageBox.information(self, "Deleted", f"Operator account '{username}' has been deleted.")
                self.refresh_users_list()
                self.refresh_logs()
            except Exception as e:
                QMessageBox.critical(self, "Delete Failed", f"Failed to delete account: {e}")

    def generate_secret_code(self):
        """Generates a random 6-character alphanumeric secret code."""
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        try:
            SystemSettingsModel.set_setting("admin_secret_code", code)
            self.secret_display.setText(code)
            AuditLogModel.log_event(self.user_session['id'], "Admin Security", "Generated a new Admin Secret Code.")
            self.refresh_logs()
            QMessageBox.information(self, "Success", f"New Admin Secret Code generated: {code}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not generate code: {e}")

    def _on_logs_selection(self):
        selected_rows = self.logs_table.selectionModel().selectedRows()
        self.delete_logs_btn.setEnabled(len(selected_rows) > 0)

    def _delete_selected_logs(self):
        selected_rows = self.logs_table.selectionModel().selectedRows()
        if not selected_rows:
            return

        log_ids = []
        for index in selected_rows:
            row_idx = index.row()
            t_item = self.logs_table.item(row_idx, 0)
            if t_item:
                log_ids.append(t_item.data(Qt.UserRole))

        if not log_ids:
            return

        if len(log_ids) == 1:
            confirm_msg = "Delete 1 selected audit log entry?"
        else:
            confirm_msg = f"Delete {len(log_ids)} selected audit log entries?"

        reply = QMessageBox.question(
            self, "Confirm Delete",
            f"{confirm_msg}\n\n⚠️ This cannot be undone.",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return

        try:
            AuditLogModel.delete_logs(log_ids)
            AuditLogModel.log_event(
                self.user_session['id'], "Delete Audit Logs",
                f"Deleted {len(log_ids)} audit logs.", module="Security"
            )
            self.refresh_logs()
        except Exception as e:
            QMessageBox.critical(self, "Delete Error", f"Could not delete audit logs:\n{e}")

