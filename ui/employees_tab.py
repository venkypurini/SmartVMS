from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QComboBox, QPushButton, QFrame, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QAbstractItemView, QSplitter, QFormLayout
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor

from database.db_manager import get_db_connection
from models.audit_logs import AuditLogModel


# ---------------------------------------------------------------------------
# Lightweight EmployeeManager model (avoids coupling to EmployeeModel)
# ---------------------------------------------------------------------------
class _EmpDB:
    @staticmethod
    def get_departments():
        conn = get_db_connection()
        rows = conn.execute("SELECT id, name FROM departments ORDER BY name ASC;").fetchall()
        conn.close()
        return [dict(r) for r in rows]

    @staticmethod
    def get_all():
        conn = get_db_connection()
        rows = conn.execute("""
            SELECT e.id, e.emp_code, e.full_name, e.email, e.phone,
                   e.designation, e.is_active, d.name AS department_name, e.department_id
            FROM employees e
            LEFT JOIN departments d ON e.department_id = d.id
            ORDER BY e.full_name ASC;
        """).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    @staticmethod
    def add(emp_code, full_name, email, phone, dept_id, designation):
        conn = get_db_connection()
        try:
            # Check unique phone
            dup = conn.execute("SELECT id FROM employees WHERE phone = ?;", (phone,)).fetchone()
            if dup:
                return False, "Mobile number already exists for another employee."
            conn.execute("""
                INSERT INTO employees (emp_code, full_name, email, phone, department_id, designation, is_active)
                VALUES (?, ?, ?, ?, ?, ?, 1);
            """, (emp_code, full_name, email, phone, dept_id, designation))
            conn.commit()
            return True, None
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()

    @staticmethod
    def update(emp_id, full_name, email, phone, dept_id, designation):
        conn = get_db_connection()
        try:
            # Check unique phone
            dup = conn.execute("SELECT id FROM employees WHERE phone = ? AND id != ?;", (phone, emp_id)).fetchone()
            if dup:
                return False, "Mobile number already exists for another employee."
            conn.execute("""
                UPDATE employees
                SET full_name = ?, email = ?, phone = ?, department_id = ?, designation = ?
                WHERE id = ?;
            """, (full_name, email, phone, dept_id, designation, emp_id))
            conn.commit()
            return True, None
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()


    @staticmethod
    def deactivate(emp_id):
        conn = get_db_connection()
        conn.execute("UPDATE employees SET is_active = 0 WHERE id = ?;", (emp_id,))
        conn.commit()
        conn.close()

    @staticmethod
    def delete(emp_id):
        conn = get_db_connection()
        conn.execute("DELETE FROM employees WHERE id = ?;", (emp_id,))
        conn.commit()
        conn.close()

    @staticmethod
    def next_emp_code():
        conn = get_db_connection()
        row = conn.execute(
            "SELECT emp_code FROM employees ORDER BY id DESC LIMIT 1;"
        ).fetchone()
        conn.close()
        if row:
            code = row[0]  # e.g. EMP006
            try:
                num = int(code.replace("EMP", "")) + 1
            except Exception:
                num = 1
        else:
            num = 1
        return f"EMP{num:03d}"


# ---------------------------------------------------------------------------
# Tab Widget
# ---------------------------------------------------------------------------
class EmployeesTab(QWidget):

    COLS = ["Emp Code", "Full Name", "Department", "Designation", "Email", "Phone", "Status", "Actions"]

    def __init__(self, user_session, parent=None):
        super().__init__(parent)
        self.user_session = user_session
        self._editing_id = None   # None = Add mode, int = Edit mode
        self._depts = []
        self.init_ui()
        self.load_departments()
        self.load_employees()

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        title = QLabel("Employee (Host) Management")
        title.setObjectName("TabTitle")
        layout.addWidget(title)

        info = QLabel(
            "Register all employees here first. Visitors can only be registered to meet employees "
            "that exist in this list. The host name search in the registration form is validated against this list."
        )
        info.setWordWrap(True)
        info.setStyleSheet("color:#ffffff; margin-bottom:4px;")
        layout.addWidget(info)

        splitter = QSplitter(Qt.Horizontal)
        splitter.setStyleSheet("QSplitter::handle { background-color: #2d2d3f; width: 1px; }")
        layout.addWidget(splitter)

        # ---------- LEFT: employee table ----------
        left = QFrame()
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 15, 0)
        left_layout.setSpacing(10)

        search_row = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by name, email, department…")
        self.search_input.textChanged.connect(self.load_employees)
        search_row.addWidget(self.search_input)

        refresh_btn = QPushButton("↻ Refresh")
        refresh_btn.setObjectName("SecondaryBtn")
        refresh_btn.setFixedWidth(90)
        refresh_btn.clicked.connect(self.load_employees)
        search_row.addWidget(refresh_btn)
        left_layout.addLayout(search_row)

        self.table = QTableWidget()
        self.table.setColumnCount(len(self.COLS))
        self.table.setHorizontalHeaderLabels(self.COLS)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.itemSelectionChanged.connect(self._on_row_selected)
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: #1a1a24;
                alternate-background-color: #222230;
                border: 1px solid #2d2d3f;
                border-radius: 8px;
                gridline-color: #252535;
            }
            QTableWidget::item { padding: 5px; color: #ffffff; }
            QTableWidget::item:selected { background-color: #2ecc7130; }
            QHeaderView::section {
                background-color: #121214; color: #ffffff;
                padding: 7px; border: none;
                border-bottom: 1px solid #2d2d3f; font-weight: bold;
            }
        """)
        left_layout.addWidget(self.table)

        # Action buttons below table
        action_row = QHBoxLayout()
        self.edit_btn = QPushButton("✏️  Edit Selected")
        self.edit_btn.setObjectName("SecondaryBtn")
        self.edit_btn.setEnabled(False)
        self.edit_btn.clicked.connect(self._load_selected_for_edit)
        action_row.addWidget(self.edit_btn)

        self.delete_btn = QPushButton("🗑️  Delete Selected")
        self.delete_btn.setStyleSheet(
            "background-color:#3a1a1a; color:#ff4444; border:1px solid #6b1f1f;"
            "border-radius:6px; padding:6px 12px; font-weight:bold;"
        )
        self.delete_btn.setEnabled(False)
        self.delete_btn.clicked.connect(self._delete_selected)
        action_row.addWidget(self.delete_btn)
        left_layout.addLayout(action_row)

        splitter.addWidget(left)

        # ---------- RIGHT: Add / Edit form ----------
        right = QFrame()
        right.setObjectName("MetricCard")
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(18, 18, 18, 18)
        right_layout.setSpacing(12)

        self.form_title = QLabel("➕  Add New Employee")
        self.form_title.setFont(QFont("Segoe UI", 13, QFont.Bold))
        self.form_title.setStyleSheet("color:#2ecc71;")
        right_layout.addWidget(self.form_title)

        form = QFormLayout()
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignRight)

        self.f_code = QLineEdit()
        self.f_code.setReadOnly(True)
        self.f_code.setStyleSheet("color:#00c2cb;")
        form.addRow("Emp Code:", self.f_code)

        self.f_name = QLineEdit()
        self.f_name.setPlaceholderText("Full name of the employee")
        form.addRow("Full Name *:", self.f_name)

        self.f_dept = QComboBox()
        form.addRow("Department *:", self.f_dept)

        self.f_desig = QLineEdit()
        self.f_desig.setPlaceholderText("e.g. Software Engineer, HR Manager")
        form.addRow("Designation:", self.f_desig)

        self.f_email = QLineEdit()
        self.f_email.setPlaceholderText("employee@company.com")
        form.addRow("Email *:", self.f_email)

        self.f_phone = QLineEdit()
        self.f_phone.setPlaceholderText("+91-9876543210")
        form.addRow("Phone *:", self.f_phone)

        right_layout.addLayout(form)

        btn_row = QHBoxLayout()
        self.save_btn = QPushButton("💾  Save Employee")
        self.save_btn.setObjectName("PrimaryBtn")
        self.save_btn.setFixedHeight(40)
        self.save_btn.clicked.connect(self._save_employee)
        btn_row.addWidget(self.save_btn)

        self.cancel_edit_btn = QPushButton("✖  Cancel Edit")
        self.cancel_edit_btn.setObjectName("SecondaryBtn")
        self.cancel_edit_btn.setFixedHeight(40)
        self.cancel_edit_btn.hide()
        self.cancel_edit_btn.clicked.connect(self._reset_form)
        btn_row.addWidget(self.cancel_edit_btn)
        right_layout.addLayout(btn_row)

        right_layout.addStretch()

        self.status_lbl = QLabel("")
        self.status_lbl.setWordWrap(True)
        right_layout.addWidget(self.status_lbl)

        # ---- Department quick-add section ----
        dept_sep = QFrame()
        dept_sep.setFrameShape(QFrame.HLine)
        dept_sep.setStyleSheet("color:#2d2d3f;")
        right_layout.addWidget(dept_sep)

        dept_header = QLabel("🏢  Manage Departments")
        dept_header.setFont(QFont("Segoe UI", 11, QFont.Bold))
        dept_header.setStyleSheet("color:#ffffff; margin-top:4px;")
        right_layout.addWidget(dept_header)

        dept_add_row = QHBoxLayout()
        self.dept_name_input = QLineEdit()
        self.dept_name_input.setPlaceholderText("New department name…")
        dept_add_row.addWidget(self.dept_name_input)
        add_dept_btn = QPushButton("Add Dept")
        add_dept_btn.setObjectName("SecondaryBtn")
        add_dept_btn.setFixedWidth(90)
        add_dept_btn.clicked.connect(self._add_department)
        dept_add_row.addWidget(add_dept_btn)
        right_layout.addLayout(dept_add_row)

        self.dept_status_lbl = QLabel("")
        self.dept_status_lbl.setStyleSheet("color:#2ecc71; font-size:11px;")
        right_layout.addWidget(self.dept_status_lbl)

        splitter.addWidget(right)
        splitter.setSizes([600, 380])

    # ------------------------------------------------------------------
    # DATA
    # ------------------------------------------------------------------
    def load_departments(self):
        self._depts = _EmpDB.get_departments()
        self.f_dept.clear()
        for d in self._depts:
            self.f_dept.addItem(d['name'], d['id'])

    def load_employees(self):
        query = self.search_input.text().strip().lower()
        employees = _EmpDB.get_all()
        if query:
            employees = [
                e for e in employees
                if query in (e.get('full_name') or '').lower()
                or query in (e.get('email') or '').lower()
                or query in (e.get('department_name') or '').lower()
            ]

        self.table.setRowCount(0)
        for row_idx, emp in enumerate(employees):
            self.table.insertRow(row_idx)
            values = [
                emp.get('emp_code', ''),
                emp.get('full_name', ''),
                emp.get('department_name', ''),
                emp.get('designation', ''),
                emp.get('email', ''),
                emp.get('phone', ''),
                "Active" if emp.get('is_active') else "Inactive",
            ]
            for col_idx, val in enumerate(values):
                item = QTableWidgetItem(str(val) if val else "—")
                item.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)
                if col_idx == 6:  # Status column coloring
                    item.setForeground(
                        QColor("#00ff66") if val == "Active" else QColor("#ff4444")
                    )
                else:
                    item.setForeground(QColor("#ffffff"))
                self.table.setItem(row_idx, col_idx, item)
            # Store employee id in row
            self.table.item(row_idx, 0).setData(Qt.UserRole, emp['id'])

            # Inline Edit button in last column
            edit_btn = QPushButton("✏️ Edit")
            edit_btn.setStyleSheet(
                "background-color:#1a2a3a; color:#2ecc71;"
                "border:1px solid #2ecc71; border-radius:5px;"
                "padding:3px 10px; font-weight:bold;"
            )
            edit_btn.setCursor(Qt.PointingHandCursor)
            edit_btn.clicked.connect(
                lambda _, eid=emp['id']: self._load_emp_id_for_edit(eid)
            )
            self.table.setCellWidget(row_idx, 7, edit_btn)

        self.edit_btn.setEnabled(False)
        self.delete_btn.setEnabled(False)

    def _on_row_selected(self):
        selected_rows = self.table.selectionModel().selectedRows()
        num_selected = len(selected_rows)
        self.edit_btn.setEnabled(num_selected == 1)
        self.delete_btn.setEnabled(num_selected > 0)

    def _get_selected_emp_id(self):
        row = self.table.currentRow()
        if row < 0:
            return None
        item = self.table.item(row, 0)
        return item.data(Qt.UserRole) if item else None

    # ------------------------------------------------------------------
    # FORM  OPERATIONS
    # ------------------------------------------------------------------
    def _reset_form(self):
        """Switch back to Add mode."""
        self._editing_id = None
        self.form_title.setText("➕  Add New Employee")
        self.f_code.setText(_EmpDB.next_emp_code())
        self.f_name.clear()
        self.f_desig.clear()
        self.f_email.clear()
        self.f_phone.clear()
        self.f_dept.setCurrentIndex(0)
        self.save_btn.setText("💾  Save Employee")
        self.cancel_edit_btn.hide()
        self.status_lbl.setText("")
        self.table.clearSelection()

    def _load_emp_id_for_edit(self, emp_id):
        """Load a specific employee by id into the form (called from inline button)."""
        conn = get_db_connection()
        row = conn.execute("SELECT * FROM employees WHERE id = ?;", (emp_id,)).fetchone()
        conn.close()
        if not row:
            return
        emp = dict(row)
        self._editing_id = emp_id
        self.form_title.setText(f"✏️  Editing: {emp['full_name']}")
        self.f_code.setText(emp.get('emp_code', ''))
        self.f_name.setText(emp.get('full_name', ''))
        self.f_desig.setText(emp.get('designation', '') or '')
        self.f_email.setText(emp.get('email', ''))
        self.f_phone.setText(emp.get('phone', ''))
        dept_id = emp.get('department_id')
        for i in range(self.f_dept.count()):
            if self.f_dept.itemData(i) == dept_id:
                self.f_dept.setCurrentIndex(i)
                break
        self.save_btn.setText("💾  Update Employee")
        self.cancel_edit_btn.show()
        self.status_lbl.setText("")
        # Scroll right panel into view by selecting the row
        for r in range(self.table.rowCount()):
            item = self.table.item(r, 0)
            if item and item.data(Qt.UserRole) == emp_id:
                self.table.selectRow(r)
                break

    def _load_selected_for_edit(self):
        """Load selected employee data into the form for editing (bottom button)."""
        emp_id = self._get_selected_emp_id()
        if emp_id is not None:
            self._load_emp_id_for_edit(emp_id)

    def _save_employee(self):
        full_name = self.f_name.text().strip()
        email     = self.f_email.text().strip()
        phone     = self.f_phone.text().strip()
        desig     = self.f_desig.text().strip()
        dept_idx  = self.f_dept.currentIndex()

        # Validation
        if not full_name:
            self._set_status("❌  Full Name is required.", error=True)
            self.f_name.setFocus()
            return
        if not email or "@" not in email:
            self._set_status("❌  A valid Email is required.", error=True)
            self.f_email.setFocus()
            return
        if not phone:
            self._set_status("❌  Phone number is required.", error=True)
            self.f_phone.setFocus()
            return
        if not phone.isdigit() or len(phone) != 10:
            self._set_status("❌  Phone number must be exactly 10 digits.", error=True)
            self.f_phone.setFocus()
            return
        if dept_idx < 0:
            self._set_status("❌  Please select a Department.", error=True)
            return

        dept_id = self.f_dept.itemData(dept_idx)

        if self._editing_id is None:
            # ADD
            emp_code = _EmpDB.next_emp_code()
            ok, err = _EmpDB.add(emp_code, full_name, email, phone, dept_id, desig)
            if ok:
                AuditLogModel.log_event(
                    self.user_session['id'], "Add Employee",
                    f"Added employee {full_name} ({emp_code}).", module="Employees"
                )
                self._set_status(f"✅  Employee '{full_name}' registered successfully!", error=False)
                self._reset_form()
                self.load_employees()
            else:
                self._set_status(f"❌  Failed to add: {err}", error=True)
        else:
            # EDIT
            ok, err = _EmpDB.update(self._editing_id, full_name, email, phone, dept_id, desig)
            if ok:
                AuditLogModel.log_event(
                    self.user_session['id'], "Update Employee",
                    f"Updated employee {full_name} (id={self._editing_id}).", module="Employees"
                )
                self._set_status(f"✅  Employee '{full_name}' updated successfully!", error=False)
                self._reset_form()
                self.load_employees()
            else:
                self._set_status(f"❌  Failed to update: {err}", error=True)

    def _delete_selected(self):
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            return

        emp_ids = []
        emp_names = []
        for index in selected_rows:
            row_idx = index.row()
            emp_id_item = self.table.item(row_idx, 0)
            if emp_id_item:
                emp_ids.append(emp_id_item.data(Qt.UserRole))
                name_item = self.table.item(row_idx, 1)
                emp_names.append(name_item.text() if name_item else "Unknown")

        if not emp_ids:
            return

        if len(emp_ids) == 1:
            confirm_msg = f"Delete employee <b>{emp_names[0]}</b>?"
        else:
            confirm_msg = f"Delete <b>{len(emp_ids)}</b> selected employees?"

        reply = QMessageBox.question(
            self, "Confirm Delete",
            f"{confirm_msg}\n\n"
            "⚠️  This cannot be undone. Any pending visits linked to these employees will lose their host reference.",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return

        try:
            conn = get_db_connection()
            placeholders = ",".join("?" for _ in emp_ids)
            conn.execute(f"DELETE FROM employees WHERE id IN ({placeholders});", tuple(emp_ids))
            conn.commit()
            conn.close()

            AuditLogModel.log_event(
                self.user_session['id'], "Delete Employees",
                f"Deleted employees: {', '.join(emp_names)}.", module="Employees"
            )
            self.table.clearSelection()
            self.load_employees()
            self._reset_form()
        except Exception as e:
            QMessageBox.critical(self, "Delete Error", f"Could not delete employees:\n{e}")

    def _set_status(self, msg, error=False):
        color = "#ff4444" if error else "#00ff66"
        self.status_lbl.setText(msg)
        self.status_lbl.setStyleSheet(f"color:{color}; font-weight:bold;")

    def _add_department(self):
        """Add a new department from the quick-add field."""
        name = self.dept_name_input.text().strip()
        if not name:
            self.dept_status_lbl.setText("⚠️  Please enter a department name.")
            self.dept_status_lbl.setStyleSheet("color:#ff9f43; font-size:11px;")
            return
        conn = get_db_connection()
        try:
            # Check for duplicate
            exists = conn.execute(
                "SELECT id FROM departments WHERE LOWER(name) = LOWER(?);", (name,)
            ).fetchone()
            if exists:
                self.dept_status_lbl.setText(f"⚠️  Department '{name}' already exists.")
                self.dept_status_lbl.setStyleSheet("color:#ff9f43; font-size:11px;")
                conn.close()
                return
            conn.execute("INSERT INTO departments (name) VALUES (?);", (name,))
            conn.commit()
            self.dept_status_lbl.setText(f"✅  Department '{name}' added.")
            self.dept_status_lbl.setStyleSheet("color:#00ff66; font-size:11px;")
            self.dept_name_input.clear()
            self.load_departments()   # refresh dropdown
        except Exception as e:
            self.dept_status_lbl.setText(f"❌  Error: {e}")
            self.dept_status_lbl.setStyleSheet("color:#ff4444; font-size:11px;")
        finally:
            conn.close()

    def showEvent(self, event):
        """Reload data every time tab becomes visible."""
        super().showEvent(event)
        self._reset_form()
        self.load_departments()
        self.load_employees()
