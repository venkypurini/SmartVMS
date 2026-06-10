import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame,
    QMessageBox, QAbstractItemView
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QFont, QColor

from models.visitor import VisitorModel
from models.audit_logs import AuditLogModel
from modules.qr_code import QRPassGenerator


class ApprovalsTab(QWidget):
    """Tab for approving or rejecting pending visitor visit requests."""

    approval_completed = pyqtSignal()  # emitted after approve/reject

    COLUMNS = [
        ("Visitor Code",    "visitor_code"),
        ("Visitor Name",    "visitor_name"),
        ("Mobile",          "mobile"),
        ("Company",         "company_name"),
        ("Purpose",         "purpose"),
        ("Host Employee",   "employee_name"),
        ("Department",      "department_name"),
        ("Requested On",    "entry_date"),
    ]

    def __init__(self, user_session, parent=None):
        super().__init__(parent)
        self.user_session = user_session
        self._pending_data = []   # cache of current rows
        self.init_ui()
        self.load_pending()

        # Auto-refresh every 30 s
        self._timer = QTimer(self)
        self._timer.timeout.connect(self.load_pending)
        self._timer.start(30_000)

    # ------------------------------------------------------------------
    # UI SETUP
    # ------------------------------------------------------------------
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Title row
        title_row = QHBoxLayout()
        title = QLabel("Visitor Approval Queue")
        title.setObjectName("TabTitle")
        title_row.addWidget(title)
        title_row.addStretch()

        self.badge_lbl = QLabel("0 Pending")
        self.badge_lbl.setFont(QFont("Segoe UI", 10, QFont.Bold))
        self.badge_lbl.setStyleSheet(
            "background-color:#ff2e93; color:white; border-radius:10px; padding:4px 12px;"
        )
        title_row.addWidget(self.badge_lbl)

        refresh_btn = QPushButton("↻  Refresh")
        refresh_btn.setObjectName("SecondaryBtn")
        refresh_btn.setFixedWidth(100)
        refresh_btn.clicked.connect(self.load_pending)
        title_row.addWidget(refresh_btn)

        layout.addLayout(title_row)

        # Info card
        info = QFrame()
        info.setObjectName("MetricCard")
        info_layout = QHBoxLayout(info)
        info_lbl = QLabel(
            "When a visitor is registered, their request appears here.\n"
            "The host (or any operator) must <b>Approve</b> before a QR pass is generated "
            "and the visitor is allowed to enter."
        )
        info_lbl.setWordWrap(True)
        info_lbl.setStyleSheet("color:#ffffff;")
        info_layout.addWidget(info_lbl)
        layout.addWidget(info)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(len(self.COLUMNS) + 2)   # +2 for Approve / Reject buttons
        headers = [c[0] for c in self.COLUMNS] + ["", ""]
        self.table.setHorizontalHeaderLabels(headers)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setStretchLastSection(False)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)   # Visitor Name stretches
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: #1a1a24;
                alternate-background-color: #222230;
                border: 1px solid #2d2d3f;
                border-radius: 8px;
                gridline-color: #252535;
            }
            QTableWidget::item { padding: 6px; color: #ffffff; }
            QTableWidget::item:selected { background-color: #2ecc7130; }
            QHeaderView::section {
                background-color: #121214;
                color: #ffffff;
                padding: 8px;
                border: none;
                border-bottom: 1px solid #2d2d3f;
                font-weight: bold;
            }
        """)
        layout.addWidget(self.table)

        # Bottom status
        self.status_lbl = QLabel("Loading…")
        self.status_lbl.setStyleSheet("color:#00c2cb; font-size:11px;")
        layout.addWidget(self.status_lbl)

    # ------------------------------------------------------------------
    # DATA LOADING
    # ------------------------------------------------------------------
    def load_pending(self):
        """Fetch pending visits from DB and populate table."""
        try:
            self._pending_data = VisitorModel.get_pending_visits()
        except Exception as e:
            self.status_lbl.setText(f"Error loading pending visits: {e}")
            return

        count = len(self._pending_data)
        self.badge_lbl.setText(f"{count} Pending")
        self.badge_lbl.setStyleSheet(
            f"background-color:{'#ff2e93' if count else '#2d2d3f'}; "
            "color:white; border-radius:10px; padding:4px 12px;"
        )

        self.table.setRowCount(0)
        for row_idx, visit in enumerate(self._pending_data):
            self.table.insertRow(row_idx)

            for col_idx, (_, key) in enumerate(self.COLUMNS):
                val = visit.get(key) or "—"
                item = QTableWidgetItem(str(val))
                item.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)
                self.table.setItem(row_idx, col_idx, item)

            # Approve button
            approve_btn = QPushButton("✅  Approve")
            approve_btn.setStyleSheet(
                "background-color:#1a3a1a; color:#00ff66; border:1px solid #1f6b30;"
                "border-radius:5px; padding:4px 10px; font-weight:bold;"
            )
            approve_btn.setCursor(Qt.PointingHandCursor)
            approve_btn.clicked.connect(
                lambda _, v=visit: self.handle_approve(v)
            )
            self.table.setCellWidget(row_idx, len(self.COLUMNS), approve_btn)

            # Reject button
            reject_btn = QPushButton("❌  Reject")
            reject_btn.setStyleSheet(
                "background-color:#3a1a1a; color:#ff4444; border:1px solid #6b1f1f;"
                "border-radius:5px; padding:4px 10px; font-weight:bold;"
            )
            reject_btn.setCursor(Qt.PointingHandCursor)
            reject_btn.clicked.connect(
                lambda _, v=visit: self.handle_reject(v)
            )
            self.table.setCellWidget(row_idx, len(self.COLUMNS) + 1, reject_btn)

        if count:
            self.status_lbl.setText(f"Showing {count} pending approval request(s). Auto-refreshes every 30 seconds.")
        else:
            self.status_lbl.setText("No pending approval requests. All visitors are processed.")

    # ------------------------------------------------------------------
    # APPROVE / REJECT HANDLERS
    # ------------------------------------------------------------------
    def handle_approve(self, visit):
        """Approve the visit and generate QR pass."""
        visit_id    = visit['visit_id']
        visitor_id  = visit['visitor_id']
        visitor_code = visit['visitor_code']
        visitor_name = visit['visitor_name']
        company      = visit.get('company_name', '')
        employee_name = visit.get('employee_name', '')
        dept_name     = visit.get('department_name', '')

        reply = QMessageBox.question(
            self, "Confirm Approval",
            f"Approve visit request for <b>{visitor_name}</b>?<br>"
            f"Host: {employee_name} | Dept: {dept_name}<br><br>"
            "A QR Pass will be generated and the visitor can check in.",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes
        )
        if reply != QMessageBox.Yes:
            return

        try:
            # Generate QR code
            qr_path = QRPassGenerator.generate_pass(
                visitor_code, visitor_name, company,
                employee_name, dept_name
            )

            # Mark approved in DB
            VisitorModel.approve_visit(
                visit_id,
                self.user_session['id'],
                qr_code_path=qr_path
            )

            # Audit log
            AuditLogModel.log_event(
                self.user_session['id'],
                "Approve Visit",
                f"Approved visit for {visitor_name} ({visitor_code}). QR: {qr_path}",
                module="Approvals"
            )

            # Send QR pass email to visitor
            email_status = ""
            try:
                from utils.email_sender import send_qr_to_visitor
                from database.db_manager import get_db_connection
                import datetime

                # Fetch visitor email
                conn = get_db_connection()
                v_row = conn.execute(
                    "SELECT email FROM visitors WHERE id = ?;", (visitor_id,)
                ).fetchone()
                conn.close()
                visitor_email = dict(v_row).get('email', '') if v_row else ''

                ok, err = send_qr_to_visitor(
                    visitor_email=visitor_email,
                    visitor_name=visitor_name,
                    qr_path=qr_path,
                    host_name=employee_name,
                    dept_name=dept_name,
                    visit_date=datetime.date.today().strftime("%d %B %Y")
                )
                if ok:
                    email_status = f"\n\n📧 QR pass emailed to visitor: {visitor_email}"
                else:
                    email_status = f"\n\n⚠️ Email not sent: {err}"
            except Exception as mail_err:
                email_status = f"\n\n⚠️ Email skipped: {mail_err}"

            QMessageBox.information(
                self, "Visit Approved ✅",
                f"Visit approved for <b>{visitor_name}</b>!\n\n"
                f"QR Pass saved to:\n{qr_path}"
                f"{email_status}\n\n"
                "The visitor can now present this QR code at the gate to check in."
            )

            self.approval_completed.emit()
            self.load_pending()


        except Exception as e:
            QMessageBox.critical(self, "Approval Error", f"Failed to approve visit:\n{e}")

    def handle_reject(self, visit):
        """Reject (cancel) the visit request."""
        visit_id     = visit['visit_id']
        visitor_name = visit['visitor_name']

        reply = QMessageBox.question(
            self, "Confirm Rejection",
            f"Reject visit request for <b>{visitor_name}</b>?<br>"
            "The visitor will not be allowed to enter.",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return

        try:
            VisitorModel.reject_visit(visit_id, self.user_session['id'])

            AuditLogModel.log_event(
                self.user_session['id'],
                "Reject Visit",
                f"Rejected visit request for {visitor_name} (visit_id={visit_id}).",
                module="Approvals"
            )

            QMessageBox.information(
                self, "Visit Rejected",
                f"❌  Visit request for <b>{visitor_name}</b> has been rejected."
            )

            self.approval_completed.emit()
            self.load_pending()

        except Exception as e:
            QMessageBox.critical(self, "Rejection Error", f"Failed to reject visit:\n{e}")
