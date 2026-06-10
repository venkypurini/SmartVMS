from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QComboBox, QDateEdit, QPushButton, 
                             QFrame, QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, QAbstractItemView)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QFont, QColor

from models.visitor import VisitorModel
from models.checkin import VisitModel
from models.employee import EmployeeModel

class HistoryTab(QWidget):
    def __init__(self, user_session, parent=None):
        super().__init__(parent)
        self.user_session = user_session
        self.is_admin = self.user_session.get('role', '').lower() == 'admin'
        
        # Pagination settings
        self.current_page = 1
        self.items_per_page = 12
        self.total_pages = 1
        
        self.init_ui()
        self.load_departments()
        self.refresh_table()

    def init_ui(self):
        # Main Layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.main_layout.setSpacing(15)

        # Tab Header Title
        title_label = QLabel("Visitor Records Log")
        title_label.setObjectName("TabTitle")
        self.main_layout.addWidget(title_label)

        # ------------------ SEARCH & FILTERS HEADER ------------------
        filter_card = QFrame()
        filter_card.setObjectName("MetricCard")
        filter_layout = QHBoxLayout(filter_card)
        filter_layout.setContentsMargins(15, 12, 15, 12)
        filter_layout.setSpacing(10)

        # Search Query Input
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search Name, ID, Mobile...")
        self.search_input.setFixedWidth(200)
        self.search_input.textChanged.connect(self.reset_and_refresh)
        filter_layout.addWidget(self.search_input)

        # Status Filter Combo
        self.status_combo = QComboBox()
        self.status_combo.addItems(["All Statuses", "Registered", "CheckedIn", "CheckedOut"])
        self.status_combo.setFixedWidth(130)
        self.status_combo.currentIndexChanged.connect(self.reset_and_refresh)
        filter_layout.addWidget(self.status_combo)

        # Department Filter Combo
        self.dept_combo = QComboBox()
        self.dept_combo.setFixedWidth(150)
        self.dept_combo.currentIndexChanged.connect(self.reset_and_refresh)
        filter_layout.addWidget(self.dept_combo)

        # Date Range Filter inputs
        date_lbl = QLabel("Date:")
        date_lbl.setObjectName("FormLabel")
        filter_layout.addWidget(date_lbl)

        # Date From
        self.date_from = QDateEdit()
        self.date_from.setCalendarPopup(True)
        # Default to 30 days ago
        self.date_from.setDate(QDate.currentDate().addDays(-30))
        self.date_from.dateChanged.connect(self.reset_and_refresh)
        filter_layout.addWidget(self.date_from)

        to_lbl = QLabel("to")
        to_lbl.setObjectName("FormLabel")
        filter_layout.addWidget(to_lbl)

        # Date To
        self.date_to = QDateEdit()
        self.date_to.setCalendarPopup(True)
        self.date_to.setDate(QDate.currentDate())
        self.date_to.dateChanged.connect(self.reset_and_refresh)
        filter_layout.addWidget(self.date_to)

        # Reset filters button
        reset_filter_btn = QPushButton("Reset")
        reset_filter_btn.setObjectName("SecondaryBtn")
        reset_filter_btn.setFixedWidth(80)
        reset_filter_btn.clicked.connect(self.reset_filters)
        filter_layout.addWidget(reset_filter_btn)

        self.main_layout.addWidget(filter_card)

        # ------------------ DATA TABLE ------------------
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "Visitor ID", "Full Name", "Mobile", "Company", 
            "Host Employee", "Check-In Time", "Check-Out Time", "Status"
        ])
        
        # Configure table layout properties
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(7, QHeaderView.ResizeToContents)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.table.verticalHeader().setVisible(False)
        self.table.itemSelectionChanged.connect(self._on_table_selection)
        self.table.setStyleSheet("""
            QTableWidget {
                gridline-color: #2d2d3f;
            }
        """)

        self.main_layout.addWidget(self.table)

        # ------------------ PAGINATION CONTROLS ------------------
        pagination_layout = QHBoxLayout()
        
        # Delete Selected Button
        self.delete_btn = QPushButton("🗑️ Delete Selected")
        self.delete_btn.setStyleSheet(
            "background-color:#3a1a1a; color:#ff4444; border:1px solid #6b1f1f;"
            "border-radius:6px; padding:6px 12px; font-weight:bold;"
        )
        self.delete_btn.setEnabled(False)
        self.delete_btn.clicked.connect(self._delete_selected)
        pagination_layout.addWidget(self.delete_btn)
            
        pagination_layout.addStretch()

        self.prev_btn = QPushButton("◄ Previous")
        self.prev_btn.setObjectName("SecondaryBtn")
        self.prev_btn.setFixedWidth(100)
        self.prev_btn.setCursor(Qt.PointingHandCursor)
        self.prev_btn.clicked.connect(self.prev_page)
        pagination_layout.addWidget(self.prev_btn)

        self.page_lbl = QLabel("Page 1 of 1")
        self.page_lbl.setFont(QFont("Segoe UI", 10, QFont.Bold))
        self.page_lbl.setStyleSheet("color: #ffffff; padding: 0px 15px;")
        pagination_layout.addWidget(self.page_lbl)

        self.next_btn = QPushButton("Next ►")
        self.next_btn.setObjectName("SecondaryBtn")
        self.next_btn.setFixedWidth(100)
        self.next_btn.setCursor(Qt.PointingHandCursor)
        self.next_btn.clicked.connect(self.next_page)
        pagination_layout.addWidget(self.next_btn)

        pagination_layout.addStretch()
        self.main_layout.addLayout(pagination_layout)

    def load_departments(self):
        """Populate departments combo filter box."""
        try:
            depts = EmployeeModel.get_all_departments()
            self.dept_combo.clear()
            self.dept_combo.addItem("All Departments", 0)
            for d in depts:
                self.dept_combo.addItem(d['name'], d['id'])
        except Exception as e:
            print(f"[HistoryTab] Error loading departments: {e}")

    def get_current_filters(self):
        """Generate filter dictionary for SQL queries based on form values."""
        filters = {}
        
        # Search query
        search = self.search_input.text().strip()
        if search:
            filters['search'] = search
            
        # Status
        status_idx = self.status_combo.currentIndex()
        if status_idx > 0:
            status_text = self.status_combo.currentText()
            if status_text == "CheckedIn":
                filters['status'] = 'active'
            elif status_text == "CheckedOut":
                filters['status'] = 'completed'
            
        # Department
        dept_idx = self.dept_combo.currentIndex()
        if dept_idx > 0:
            filters['department_id'] = self.dept_combo.itemData(dept_idx)
            
        # Date range
        filters['date_from'] = self.date_from.date().toString("yyyy-MM-dd")
        filters['date_to'] = self.date_to.date().toString("yyyy-MM-dd")
        
        return filters

    def reset_and_refresh(self):
        """Reset pagination page to 1 and reload table records."""
        self.current_page = 1
        self.refresh_table()

    def refresh_table(self):
        """Fetch filtered records from SQLite database and populate table items."""
        filters = self.get_current_filters()
        offset = (self.current_page - 1) * self.items_per_page
        
        try:
            # 1. Fetch total count to calculate pagination
            total_records = VisitModel.get_visits_count(filters)
            self.total_pages = max(1, (total_records + self.items_per_page - 1) // self.items_per_page)
            
            # Update pagination UI labels and button states
            self.page_lbl.setText(f"Page {self.current_page} of {self.total_pages}")
            self.prev_btn.setEnabled(self.current_page > 1)
            self.next_btn.setEnabled(self.current_page < self.total_pages)
            
            # 2. Fetch paginated logs
            visits = VisitModel.get_visits_history(limit=self.items_per_page, offset=offset, filters=filters)
            
            # 3. Populate Table Widget
            self.table.setRowCount(0)
            self.table.setRowCount(len(visits))
            
            for row_idx, v in enumerate(visits):
                id_item = QTableWidgetItem(v['visitor_code'])
                id_item.setData(Qt.UserRole, v['id'])
                self.table.setItem(row_idx, 0, id_item)
                self.table.setItem(row_idx, 1, QTableWidgetItem(v['visitor_name']))
                self.table.setItem(row_idx, 2, QTableWidgetItem(v['visitor_mobile']))
                self.table.setItem(row_idx, 3, QTableWidgetItem(v['visitor_company'] or "N/A"))
                self.table.setItem(row_idx, 4, QTableWidgetItem(v['employee_name'] or "N/A"))
                
                checkin_val = f"{v['entry_date']} {v['entry_time']}"
                checkout_val = v.get('exit_time') or "N/A"
                self.table.setItem(row_idx, 5, QTableWidgetItem(checkin_val))
                self.table.setItem(row_idx, 6, QTableWidgetItem(checkout_val))
                
                # Style status column with rich highlights
                status_raw = v['status']
                status_text = "Checked Out" if status_raw == "completed" else ("Checked In" if status_raw == "active" else "Cancelled")
                status_item = QTableWidgetItem(status_text)
                status_item.setTextAlignment(Qt.AlignCenter)
                status_item.setFont(QFont("Segoe UI", 9, QFont.Bold))
                
                if status_raw == 'active':
                    status_item.setForeground(QColor("#00ff66")) # Green text
                elif status_raw == 'cancelled':
                    status_item.setForeground(QColor("#ff2e93")) # Red text
                else: # completed
                    status_item.setForeground(QColor("#ffffff")) # Gray text
                    
                self.table.setItem(row_idx, 7, status_item)

        except Exception as e:
            print(f"[HistoryTab] Error loading records: {e}")

    def reset_filters(self):
        """Restore all search inputs and filter combo values to default states."""
        self.search_input.clear()
        self.status_combo.setCurrentIndex(0)
        self.dept_combo.setCurrentIndex(0)
        self.date_from.setDate(QDate.currentDate().addDays(-30))
        self.date_to.setDate(QDate.currentDate())
        self.reset_and_refresh()

    def prev_page(self):
        """Navigate to previous page."""
        if self.current_page > 1:
            self.current_page -= 1
            self.refresh_table()

    def next_page(self):
        """Navigate to next page."""
        if self.current_page < self.total_pages:
            self.current_page += 1
            self.refresh_table()

    def _on_table_selection(self):
        selected_rows = self.table.selectionModel().selectedRows()
        self.delete_btn.setEnabled(len(selected_rows) > 0)

    def _delete_selected(self):
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            return

        visit_ids = []
        visitor_names = []
        for index in selected_rows:
            row_idx = index.row()
            visit_id_item = self.table.item(row_idx, 0)
            if visit_id_item:
                visit_ids.append(visit_id_item.data(Qt.UserRole))
                name_item = self.table.item(row_idx, 1)
                visitor_names.append(name_item.text() if name_item else "Unknown")

        if not visit_ids:
            return

        if len(visit_ids) == 1:
            confirm_msg = f"permanently delete the visit record for <b>{visitor_names[0]}</b>?"
        else:
            confirm_msg = f"permanently delete <b>{len(visit_ids)}</b> selected visit records?"

        reply = QMessageBox.question(
            self, "Confirm Delete",
            f"Are you sure you want to {confirm_msg}\nThis action cannot be undone.",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                VisitModel.delete_visits(visit_ids)
                self.table.clearSelection()
                self.refresh_table()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete records:\n{e}")
