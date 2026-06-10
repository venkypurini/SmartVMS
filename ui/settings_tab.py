"""
ui/settings_tab.py
Email (SMTP) configuration settings panel for SmartVMS.
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFrame, QCheckBox, QFormLayout, QSpinBox,
    QMessageBox
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont

from utils.email_sender import (
    load_smtp_settings, save_smtp_settings, test_smtp_connection
)


# ------------------------------------------------------------------
# Background thread for SMTP test (so UI doesn't freeze)
# ------------------------------------------------------------------
class _SmtpTestThread(QThread):
    result = pyqtSignal(bool, str)

    def run(self):
        ok, err = test_smtp_connection()
        self.result.emit(ok, err or "")


# ------------------------------------------------------------------
# Settings Tab
# ------------------------------------------------------------------
class SettingsTab(QWidget):

    def __init__(self, user_session, parent=None):
        super().__init__(parent)
        self.user_session = user_session
        self._test_thread = None
        self.init_ui()
        self._load_settings()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 24, 30, 24)
        layout.setSpacing(20)

        # Title
        title = QLabel("⚙️  Application Settings")
        title.setObjectName("TabTitle")
        layout.addWidget(title)

        subtitle = QLabel(
            "Configure email notifications so visitors and employees receive "
            "automated alerts via Gmail when visits are registered or approved."
        )
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet("color:#ffffff;")
        layout.addWidget(subtitle)

        # ── Email Settings Card ────────────────────────────────────
        email_card = QFrame()
        email_card.setObjectName("MetricCard")
        email_layout = QVBoxLayout(email_card)
        email_layout.setContentsMargins(24, 20, 24, 20)
        email_layout.setSpacing(14)

        card_title = QLabel("📧  Email (SMTP) Notifications")
        card_title.setFont(QFont("Segoe UI", 13, QFont.Bold))
        card_title.setStyleSheet("color:#2ecc71;")
        email_layout.addWidget(card_title)

        # Enable toggle
        self.enable_chk = QCheckBox("Enable email notifications")
        self.enable_chk.setStyleSheet("color:#e0e0e6; font-size:13px;")
        self.enable_chk.stateChanged.connect(self._on_toggle_changed)
        email_layout.addWidget(self.enable_chk)

        # How-to info box
        how_to = QLabel(
            "💡 <b>How to set up Gmail:</b><br>"
            "1. Go to <u>myaccount.google.com/security</u><br>"
            "2. Enable <b>2-Step Verification</b><br>"
            "3. Under 2-Step Verification → <b>App Passwords</b><br>"
            "4. Select app: <b>Mail</b>, device: <b>Windows Computer</b><br>"
            "5. Copy the 16-character password and paste below"
        )
        how_to.setWordWrap(True)
        how_to.setStyleSheet(
            "background:#1a2540; color:#8ab4f8; border:1px solid #2d4080;"
            "border-radius:8px; padding:12px; font-size:12px; line-height:1.6;"
        )
        how_to.setOpenExternalLinks(True)
        email_layout.addWidget(how_to)

        # Form fields
        form = QFormLayout()
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignRight)

        self.f_host = QLineEdit()
        self.f_host.setPlaceholderText("smtp.gmail.com")
        form.addRow("SMTP Host:", self.f_host)

        self.f_port = QSpinBox()
        self.f_port.setRange(1, 65535)
        self.f_port.setValue(587)
        self.f_port.setFixedWidth(100)
        form.addRow("SMTP Port:", self.f_port)

        self.f_user = QLineEdit()
        self.f_user.setPlaceholderText("your.email@gmail.com")
        form.addRow("Gmail Address:", self.f_user)

        self.f_pass = QLineEdit()
        self.f_pass.setPlaceholderText("16-character App Password")
        self.f_pass.setEchoMode(QLineEdit.Password)

        # Show/hide password toggle
        show_pass_btn = QPushButton("👁  Show")
        show_pass_btn.setObjectName("SecondaryBtn")
        show_pass_btn.setFixedWidth(80)
        show_pass_btn.setCheckable(True)
        show_pass_btn.toggled.connect(
            lambda checked: self.f_pass.setEchoMode(
                QLineEdit.Normal if checked else QLineEdit.Password
            )
        )
        pass_row = QHBoxLayout()
        pass_row.setContentsMargins(0, 0, 0, 0)
        pass_row.addWidget(self.f_pass)
        pass_row.addWidget(show_pass_btn)
        form.addRow("App Password:", pass_row)

        self.f_sender = QLineEdit()
        self.f_sender.setPlaceholderText("SmartVMS")
        form.addRow("Sender Name:", self.f_sender)

        email_layout.addLayout(form)

        # Buttons row
        btn_row = QHBoxLayout()

        self.test_btn = QPushButton("🔌  Test Connection")
        self.test_btn.setObjectName("SecondaryBtn")
        self.test_btn.setFixedHeight(38)
        self.test_btn.clicked.connect(self._test_connection)
        btn_row.addWidget(self.test_btn)

        save_btn = QPushButton("💾  Save Settings")
        save_btn.setObjectName("PrimaryBtn")
        save_btn.setFixedHeight(38)
        save_btn.clicked.connect(self._save_settings)
        btn_row.addWidget(save_btn)

        email_layout.addLayout(btn_row)

        # Status label
        self.status_lbl = QLabel("")
        self.status_lbl.setWordWrap(True)
        self.status_lbl.setStyleSheet("font-size:12px;")
        email_layout.addWidget(self.status_lbl)

        layout.addWidget(email_card)

        # ── What emails are sent ──────────────────────────────────
        info_card = QFrame()
        info_card.setObjectName("MetricCard")
        info_layout = QVBoxLayout(info_card)
        info_layout.setContentsMargins(20, 16, 20, 16)

        info_title = QLabel("📬  What Emails Are Sent?")
        info_title.setFont(QFont("Segoe UI", 11, QFont.Bold))
        info_title.setStyleSheet("color:#ffffff;")
        info_layout.addWidget(info_title)

        rows = [
            ("🔔 Approval Request", "→ Employee's Email",
             "When a visitor registers and selects an employee as host"),
            ("✅ QR Pass", "→ Visitor's Email",
             "When the operator approves the visit — QR image attached"),
        ]
        for icon_label, arrow, desc in rows:
            row_frame = QFrame()
            row_frame.setStyleSheet(
                "background:#1a1a2e; border-radius:6px; margin:2px 0;"
            )
            row_h = QHBoxLayout(row_frame)
            row_h.setContentsMargins(12, 8, 12, 8)
            lbl1 = QLabel(f"<b>{icon_label}</b>  {arrow}")
            lbl1.setStyleSheet("color:#e0e0e6; font-size:12px;")
            lbl2 = QLabel(desc)
            lbl2.setStyleSheet("color:#00c2cb; font-size:11px;")
            row_h.addWidget(lbl1)
            row_h.addStretch()
            row_h.addWidget(lbl2)
            info_layout.addWidget(row_frame)

        layout.addWidget(info_card)
        layout.addStretch()

    # ------------------------------------------------------------------
    def _load_settings(self):
        cfg = load_smtp_settings()
        self.enable_chk.setChecked(bool(cfg.get("enabled")))
        self.f_host.setText(cfg.get("host", "smtp.gmail.com"))
        self.f_port.setValue(int(cfg.get("port", 587)))
        self.f_user.setText(cfg.get("username", ""))
        self.f_pass.setText(cfg.get("password", ""))
        self.f_sender.setText(cfg.get("sender_name", "SmartVMS"))
        self._on_toggle_changed(self.enable_chk.checkState())

    def _on_toggle_changed(self, state):
        enabled = bool(state)
        for w in [self.f_host, self.f_port, self.f_user, self.f_pass,
                  self.f_sender, self.test_btn]:
            w.setEnabled(enabled)

    def _save_settings(self):
        settings = {
            "enabled":     self.enable_chk.isChecked(),
            "host":        self.f_host.text().strip() or "smtp.gmail.com",
            "port":        self.f_port.value(),
            "username":    self.f_user.text().strip(),
            "password":    self.f_pass.text().strip(),
            "sender_name": self.f_sender.text().strip() or "SmartVMS",
        }
        try:
            save_smtp_settings(settings)
            self._set_status("✅  Settings saved successfully!", error=False)
        except Exception as e:
            self._set_status(f"❌  Could not save settings: {e}", error=True)

    def _test_connection(self):
        # Save current form values first so test uses them
        self._save_settings()
        self.test_btn.setEnabled(False)
        self.test_btn.setText("🔄  Testing…")
        self._set_status("Connecting to SMTP server…", error=False)

        self._test_thread = _SmtpTestThread()
        self._test_thread.result.connect(self._on_test_result)
        self._test_thread.start()

    def _on_test_result(self, ok, err):
        self.test_btn.setEnabled(True)
        self.test_btn.setText("🔌  Test Connection")
        if ok:
            self._set_status(
                "✅  Connection successful! Gmail SMTP is working correctly.", error=False
            )
        else:
            self._set_status(f"❌  Connection failed:\n{err}", error=True)

    def _set_status(self, msg, error=False):
        color = "#ff4444" if error else "#00ff66"
        self.status_lbl.setText(msg)
        self.status_lbl.setStyleSheet(f"color:{color}; font-size:12px; font-weight:bold;")
