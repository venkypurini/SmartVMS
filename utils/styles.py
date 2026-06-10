class ThemeStyles:
    DARK_MODE = """
        /* General App Styling */
        QMainWindow {
            background-color: #121214;
        }
        
        QWidget {
            color: #e0e0e6;
            font-family: 'Segoe UI', Arial, sans-serif;
            font-size: 13px;
        }
        
        /* Sidebar Menu */
        QFrame#SidebarFrame {
            background-color: #181824;
            border-right: 1px solid #282836;
        }
        
        QLabel#SidebarTitle {
            color: #00f0ff;
            font-size: 18px;
            font-weight: bold;
            padding: 15px 10px;
        }
        
        QPushButton#SidebarBtn {
            background-color: transparent;
            color: #ffffff;
            border: none;
            border-radius: 6px;
            padding: 12px 15px;
            text-align: left;
            font-weight: 500;
        }
        
        QPushButton#SidebarBtn:hover {
            background-color: #242436;
            color: #ffffff;
        }
        
        QPushButton#SidebarBtn:checked {
            background-color: #00adb5;
            color: #ffffff;
            font-weight: bold;
        }
        
        /* Content Area */
        QStackedWidget {
            background-color: #121214;
            padding: 10px;
        }
        
        /* Glassmorphism Metric Cards */
        QFrame#MetricCard {
            background-color: rgba(32, 32, 46, 0.7);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 12px;
            padding: 15px;
        }
        
        QFrame#MetricCard:hover {
            border: 1px solid rgba(0, 173, 181, 0.4);
            background-color: rgba(36, 36, 52, 0.8);
        }
        
        QLabel#MetricTitle {
            color: #ffffff;
            font-size: 13px;
            font-weight: bold;
            text-transform: uppercase;
        }
        
        QLabel#MetricValue {
            color: #ffffff;
            font-size: 26px;
            font-weight: bold;
        }
        
        QLabel#MetricTrend {
            color: #00ff66;
            font-size: 11px;
        }
        
        /* Table Controls */
        QTableView {
            background-color: #1e1e2c;
            border: 1px solid #2d2d3f;
            gridline-color: #2d2d3f;
            border-radius: 8px;
            selection-background-color: #00adb5;
            selection-color: #ffffff;
        }
        
        QHeaderView::section {
            background-color: #181824;
            color: #ffffff;
            padding: 8px;
            border: none;
            border-bottom: 2px solid #2d2d3f;
            font-weight: bold;
        }
        
        QScrollBar:vertical {
            border: none;
            background: #181824;
            width: 10px;
            margin: 0px;
        }
        
        QScrollBar::handle:vertical {
            background: #2d2d3f;
            min-height: 20px;
            border-radius: 5px;
        }
        
        QScrollBar::handle:vertical:hover {
            background: #00adb5;
        }
        
        /* Form Inputs & Controls */
        QLineEdit, QComboBox, QTextEdit, QDateEdit {
            background-color: #1a1a24;
            border: 1px solid #2d2d3f;
            border-radius: 6px;
            padding: 8px 12px;
            color: #ffffff;
        }
        
        QLineEdit:focus, QComboBox:focus, QTextEdit:focus, QDateEdit:focus {
            border: 1px solid #00adb5;
            background-color: #1e1e2e;
        }
        
        QLabel#FormLabel {
            font-weight: bold;
            color: #ffffff;
        }
        
        /* Buttons */
        QPushButton#PrimaryBtn {
            background-color: #00adb5;
            color: #ffffff;
            border: none;
            border-radius: 6px;
            font-weight: bold;
            padding: 10px 20px;
        }
        
        QPushButton#PrimaryBtn:hover {
            background-color: #00c2cb;
        }
        
        QPushButton#PrimaryBtn:pressed {
            background-color: #00939a;
        }
        
        QPushButton#SecondaryBtn {
            background-color: #2d2d3f;
            color: #ffffff;
            border: 1px solid #3d3d5f;
            border-radius: 6px;
            font-weight: bold;
            padding: 10px 20px;
        }
        
        QPushButton#SecondaryBtn:hover {
            background-color: #35354e;
        }
        
        QPushButton#AccentBtn {
            background-color: #ff2e93;
            color: #ffffff;
            border: none;
            border-radius: 6px;
            font-weight: bold;
            padding: 10px 20px;
        }
        
        QPushButton#AccentBtn:hover {
            background-color: #ff4fa5;
        }
        
        /* Title Headers */
        QLabel#TabTitle {
            font-size: 22px;
            font-weight: bold;
            color: #ffffff;
            border-bottom: 2px solid #2d2d3f;
            padding-bottom: 8px;
            margin-bottom: 15px;
        }
    """

    LIGHT_MODE = """
        /* General App Styling */
        QMainWindow {
            background-color: #f4f6f9;
        }
        
        QWidget {
            color: #2c3e50;
            font-family: 'Segoe UI', Arial, sans-serif;
            font-size: 13px;
        }
        
        /* Sidebar Menu */
        QFrame#SidebarFrame {
            background-color: #1a252f;
            border-right: 1px solid #cbd5e1;
        }
        
        QLabel#SidebarTitle {
            color: #3498db;
            font-size: 18px;
            font-weight: bold;
            padding: 15px 10px;
        }
        
        QPushButton#SidebarBtn {
            background-color: transparent;
            color: #95a5a6;
            border: none;
            border-radius: 6px;
            padding: 12px 15px;
            text-align: left;
            font-weight: 500;
        }
        
        QPushButton#SidebarBtn:hover {
            background-color: #2c3e50;
            color: #ffffff;
        }
        
        QPushButton#SidebarBtn:checked {
            background-color: #3498db;
            color: #ffffff;
            font-weight: bold;
        }
        
        /* Content Area */
        QStackedWidget {
            background-color: #f4f6f9;
            padding: 10px;
        }
        
        /* Glassmorphism Metric Cards */
        QFrame#MetricCard {
            background-color: rgba(255, 255, 255, 0.9);
            border: 1px solid #e2e8f0;
            border-radius: 12px;
            padding: 15px;
        }
        
        QFrame#MetricCard:hover {
            border: 1px solid #3498db;
            background-color: #ffffff;
        }
        
        QLabel#MetricTitle {
            color: #7f8c8d;
            font-size: 13px;
            font-weight: bold;
            text-transform: uppercase;
        }
        
        QLabel#MetricValue {
            color: #2c3e50;
            font-size: 26px;
            font-weight: bold;
        }
        
        QLabel#MetricTrend {
            color: #27ae60;
            font-size: 11px;
        }
        
        /* Table Controls */
        QTableView {
            background-color: #ffffff;
            border: 1px solid #cbd5e1;
            gridline-color: #e2e8f0;
            border-radius: 8px;
            selection-background-color: #3498db;
            selection-color: #ffffff;
            color: #2c3e50;
        }
        
        QHeaderView::section {
            background-color: #f8fafc;
            color: #475569;
            padding: 8px;
            border: none;
            border-bottom: 2px solid #cbd5e1;
            font-weight: bold;
        }
        
        QScrollBar:vertical {
            border: none;
            background: #f1f5f9;
            width: 10px;
            margin: 0px;
        }
        
        QScrollBar::handle:vertical {
            background: #cbd5e1;
            min-height: 20px;
            border-radius: 5px;
        }
        
        QScrollBar::handle:vertical:hover {
            background: #3498db;
        }
        
        /* Form Inputs & Controls */
        QLineEdit, QComboBox, QTextEdit, QDateEdit {
            background-color: #ffffff;
            border: 1px solid #cbd5e1;
            border-radius: 6px;
            padding: 8px 12px;
            color: #2c3e50;
        }
        
        QLineEdit:focus, QComboBox:focus, QTextEdit:focus, QDateEdit:focus {
            border: 1px solid #3498db;
            background-color: #ffffff;
        }
        
        QLabel#FormLabel {
            font-weight: bold;
            color: #475569;
        }
        
        /* Buttons */
        QPushButton#PrimaryBtn {
            background-color: #3498db;
            color: #ffffff;
            border: none;
            border-radius: 6px;
            font-weight: bold;
            padding: 10px 20px;
        }
        
        QPushButton#PrimaryBtn:hover {
            background-color: #2980b9;
        }
        
        QPushButton#PrimaryBtn:pressed {
            background-color: #1f618d;
        }
        
        QPushButton#SecondaryBtn {
            background-color: #e2e8f0;
            color: #475569;
            border: 1px solid #cbd5e1;
            border-radius: 6px;
            font-weight: bold;
            padding: 10px 20px;
        }
        
        QPushButton#SecondaryBtn:hover {
            background-color: #cbd5e1;
        }
        
        QPushButton#AccentBtn {
            background-color: #e74c3c;
            color: #ffffff;
            border: none;
            border-radius: 6px;
            font-weight: bold;
            padding: 10px 20px;
        }
        
        QPushButton#AccentBtn:hover {
            background-color: #c0392b;
        }
        
        /* Title Headers */
        QLabel#TabTitle {
            font-size: 22px;
            font-weight: bold;
            color: #2c3e50;
            border-bottom: 2px solid #cbd5e1;
            padding-bottom: 8px;
            margin-bottom: 15px;
        }
    """
