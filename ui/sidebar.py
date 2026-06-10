from PyQt5.QtWidgets import QFrame, QVBoxLayout, QLabel, QPushButton, QButtonGroup, QHBoxLayout
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont

class Sidebar(QFrame):
    """Sidebar menu container widget."""
    tab_changed = pyqtSignal(int)
    unlock_requested = pyqtSignal()

    def __init__(self, user_name, user_role, parent=None):
        super().__init__(parent)
        self.setObjectName("SidebarFrame")
        self.setFixedWidth(230)
        self.user_name = user_name
        self.user_role = user_role.lower() if user_role else ""
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 20, 15, 20)
        layout.setSpacing(10)

        # Brand Title
        brand_label = QLabel("SmartVMS")
        brand_label.setObjectName("SidebarTitle")
        brand_label.setFont(QFont("Segoe UI", 20, QFont.Bold))
        brand_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(brand_label)
        
        # Spacer
        sep = QFrame()
        layout.addWidget(sep)

        # Button Group for mutual exclusivity
        self.nav_group = QButtonGroup(self)
        self.nav_group.setExclusive(True)

        self.nav_buttons = []
        menu_items = [
            ("📊  Dashboard",        0),
            ("📝  Register Visitor",  1),
            ("✅  Approvals",         2),
            ("🚪  Check-In / Out",   3),
            ("📋  Visitor History",   4),
            ("📄  Reports Panel",     5),
            ("👤  Employees",         6),
            ("🔒  Security & Logs",   7),
            ("⚙️  Settings",          8)
        ]



        for text, index in menu_items:
            btn = QPushButton(text)
            btn.setObjectName("SidebarBtn")
            btn.setFont(QFont("Segoe UI", 11, QFont.Medium))
            btn.setCheckable(True)
            btn.setFixedHeight(45)
            btn.setCursor(Qt.PointingHandCursor)
            
            # Connect signals
            btn.clicked.connect(lambda checked, idx=index: self.tab_changed.emit(idx))

            self.nav_group.addButton(btn)

            # Approvals button gets a badge wrapper
            if index == 2:
                row = QHBoxLayout()
                row.setContentsMargins(0, 0, 0, 0)
                row.setSpacing(4)
                row.addWidget(btn)
                self.pending_badge = QLabel("")
                self.pending_badge.setFixedSize(22, 22)
                self.pending_badge.setAlignment(Qt.AlignCenter)
                self.pending_badge.setStyleSheet(
                    "background-color:#ff2e93; color:white; border-radius:11px;"
                    "font-size:10px; font-weight:bold;"
                )
                self.pending_badge.hide()
                row.addWidget(self.pending_badge)
                layout.addLayout(row)
            else:
                layout.addWidget(btn)

            self.nav_buttons.append(btn)

        # Default active checked (Dashboard)
        self.nav_buttons[0].setChecked(True)

        layout.addStretch()

        # User profile block
        user_info_frame = QFrame()
        user_info_frame.setStyleSheet("""
            QFrame {
                border-top: 1px solid #2d2d3f;
                padding-top: 15px;
            }
        """)
        user_info_layout = QVBoxLayout(user_info_frame)
        user_info_layout.setContentsMargins(0, 5, 0, 0)
        user_info_layout.setSpacing(4)

        user_name_lbl = QLabel(self.user_name)
        user_name_lbl.setFont(QFont("Segoe UI", 11, QFont.Bold))
        user_name_lbl.setStyleSheet("color: #ffffff;")
        
        user_role_lbl = QLabel(f"Role: {self.user_role.capitalize()}")
        user_role_lbl.setFont(QFont("Segoe UI", 9))
        user_role_lbl.setStyleSheet("color: #ffffff;")
        
        user_info_layout.addWidget(user_name_lbl)
        user_info_layout.addWidget(user_role_lbl)
        layout.addWidget(user_info_frame)
        


    def select_tab(self, index):
        """Set active button by index programmatically."""
        if 0 <= index < len(self.nav_buttons):
            self.nav_buttons[index].setChecked(True)

    def update_pending_badge(self, count):
        """Show or hide the pending approval count badge on the Approvals button."""
        if count > 0:
            self.pending_badge.setText(str(count))
            self.pending_badge.show()
        else:
            self.pending_badge.hide()
