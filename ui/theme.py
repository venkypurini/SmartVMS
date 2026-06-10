import config

class Theme:
    @staticmethod
    def get_stylesheet(is_dark=True):
        cfg = config.THEME
        
        if is_dark:
            return f"""
                QMainWindow {{
                    background-color: {cfg['PRIMARY_BG_DARK']};
                }}
                QWidget {{
                    color: #ffffff;
                    font-family: '{cfg['FONT_FAMILY']}', Arial;
                    font-size: 13px;
                }}
                QLabel {{
                    color: #ffffff;
                }}
                QDialog, QMessageBox {{
                    background-color: #121214;
                    color: #ffffff;
                }}
                QMessageBox QLabel {{
                    color: #ffffff;
                    font-size: 14px;
                }}
                QMessageBox QPushButton {{
                    background-color: #2d2d3f;
                    color: #ffffff;
                    border: 1px solid #3d3d5f;
                    border-radius: 6px;
                    padding: 6px 16px;
                    font-weight: bold;
                }}
                QMessageBox QPushButton:hover {{
                    background-color: #35354e;
                }}
                QFrame#SidebarFrame {{
                    background-color: #181824;
                    border-right: 1px solid #282836;
                }}
                QLabel#SidebarTitle {{
                    color: {cfg['ACCENT_COLOR']};
                    font-size: 18px;
                    font-weight: bold;
                    padding: 15px 10px;
                }}
                QPushButton#SidebarBtn {{
                    background-color: transparent;
                    color: #ffffff;
                    border: none;
                    border-radius: 6px;
                    padding: 12px 15px;
                    text-align: left;
                    font-weight: 500;
                }}
                QPushButton#SidebarBtn:hover {{
                    background-color: #242436;
                    color: #ffffff;
                }}
                QPushButton#SidebarBtn:checked {{
                    background-color: {cfg['ACCENT_COLOR']};
                    color: #ffffff;
                    font-weight: bold;
                }}
                QFrame#MetricCard {{
                    background-color: {cfg['CARD_BG_DARK']};
                    border: 1px solid rgba(255, 255, 255, 0.08);
                    border-radius: 12px;
                    padding: 15px;
                }}
                QFrame#MetricCard:hover {{
                    border: 1px solid rgba(46, 204, 113, 0.4);
                }}
                QLineEdit, QComboBox, QTextEdit, QDateEdit {{
                    background-color: #1a1a24;
                    border: 1px solid #2d2d3f;
                    border-radius: 6px;
                    padding: 8px 12px;
                    color: #ffffff;
                    font-weight: 500;
                }}
                QLineEdit::placeholder, QTextEdit::placeholder {{
                    color: #27ae60;
                }}
                QComboBox QAbstractItemView {{
                    background-color: #1a1a24;
                    color: #ffffff;
                    selection-background-color: {cfg['ACCENT_COLOR']};
                    selection-color: #ffffff;
                }}
                QLineEdit:focus, QComboBox:focus, QTextEdit:focus, QDateEdit:focus {{
                    border: 1px solid {cfg['ACCENT_COLOR']};
                }}
                QTableWidget {{
                    background-color: #1a1a24;
                    alternate-background-color: #222230;
                    color: #ffffff;
                    gridline-color: #2d2d3f;
                    border: 1px solid #2d2d3f;
                    border-radius: 6px;
                }}
                QTableWidget::item {{
                    color: #ffffff;
                    padding: 4px;
                }}
                QHeaderView::section {{
                    background-color: #242436;
                    color: {cfg['ACCENT_COLOR']};
                    font-weight: bold;
                    padding: 6px;
                    border: 1px solid #2d2d3f;
                }}
                QTableView QTableCornerButton::section {{
                    background-color: #242436;
                    border: 1px solid #2d2d3f;
                }}
                QPushButton#PrimaryBtn {{
                    background-color: {cfg['ACCENT_COLOR']};
                    color: #ffffff;
                    border: none;
                    border-radius: 6px;
                    font-weight: bold;
                    padding: 10px 20px;
                }}
                QPushButton#PrimaryBtn:hover {{
                    background-color: #27ae60;
                }}
                QPushButton#SecondaryBtn {{
                    background-color: #2d2d3f;
                    color: #ffffff;
                    border: 1px solid #3d3d5f;
                    border-radius: 6px;
                    font-weight: bold;
                    padding: 10px 20px;
                }}
                QPushButton#SecondaryBtn:hover {{
                    background-color: #35354e;
                }}
                QPushButton#AccentBtn {{
                    background-color: #e74c3c;
                    color: #ffffff;
                    border: none;
                    border-radius: 6px;
                    font-weight: bold;
                    padding: 10px 20px;
                }}
                QPushButton#AccentBtn:hover {{
                    background-color: #c0392b;
                }}
                QLabel#TabTitle {{
                    font-size: 22px;
                    font-weight: bold;
                    color: #ffffff;
                    border-bottom: 2px solid #2d2d3f;
                    padding-bottom: 8px;
                    margin-bottom: 15px;
                }}
            """
        else:
            return f"""
                QMainWindow {{
                    background-color: {cfg['PRIMARY_BG_LIGHT']};
                }}
                QWidget {{
                    color: #2c3e50;
                    font-family: '{cfg['FONT_FAMILY']}', Arial;
                    font-size: 13px;
                }}
                QDialog, QMessageBox {{
                    background-color: #ffffff;
                    color: #2c3e50;
                }}
                QMessageBox QLabel {{
                    color: #2c3e50;
                    font-size: 14px;
                }}
                QMessageBox QPushButton {{
                    background-color: #e2e8f0;
                    color: #475569;
                    border: 1px solid #cbd5e1;
                    border-radius: 6px;
                    padding: 6px 16px;
                    font-weight: bold;
                }}
                QMessageBox QPushButton:hover {{
                    background-color: #cbd5e1;
                }}
                QFrame#SidebarFrame {{
                    background-color: #1a252f;
                    border-right: 1px solid #cbd5e1;
                }}
                QLabel#SidebarTitle {{
                    color: #2ecc71;
                    font-size: 18px;
                    font-weight: bold;
                    padding: 15px 10px;
                }}
                QPushButton#SidebarBtn {{
                    background-color: transparent;
                    color: #95a5a6;
                    border: none;
                    border-radius: 6px;
                    padding: 12px 15px;
                    text-align: left;
                    font-weight: 500;
                }}
                QPushButton#SidebarBtn:hover {{
                    background-color: #2c3e50;
                    color: #ffffff;
                }}
                QPushButton#SidebarBtn:checked {{
                    background-color: #2ecc71;
                    color: #ffffff;
                    font-weight: bold;
                }}
                QFrame#MetricCard {{
                    background-color: {cfg['CARD_BG_LIGHT']};
                    border: 1px solid #e2e8f0;
                    border-radius: 12px;
                    padding: 15px;
                }}
                QFrame#MetricCard:hover {{
                    border: 1px solid #2ecc71;
                }}
                QLineEdit, QComboBox, QTextEdit, QDateEdit {{
                    background-color: #ffffff;
                    border: 1px solid #cbd5e1;
                    border-radius: 6px;
                    padding: 8px 12px;
                    color: #2c3e50;
                    font-weight: 500;
                }}
                QLineEdit::placeholder, QTextEdit::placeholder {{
                    color: #2ecc71;
                }}
                QComboBox QAbstractItemView {{
                    background-color: #ffffff;
                    color: #2c3e50;
                    selection-background-color: #2ecc71;
                    selection-color: #ffffff;
                }}
                QLineEdit:focus, QComboBox:focus, QTextEdit:focus, QDateEdit:focus {{
                    border: 1px solid #2ecc71;
                }}
                QTableWidget {{
                    background-color: #ffffff;
                    alternate-background-color: #f1f5f9;
                    color: #2c3e50;
                    gridline-color: #cbd5e1;
                    border: 1px solid #cbd5e1;
                    border-radius: 6px;
                }}
                QTableWidget::item {{
                    color: #2c3e50;
                    padding: 4px;
                }}
                QHeaderView::section {{
                    background-color: #f8fafc;
                    color: #2ecc71;
                    font-weight: bold;
                    padding: 6px;
                    border: 1px solid #cbd5e1;
                }}
                QTableView QTableCornerButton::section {{
                    background-color: #f8fafc;
                    border: 1px solid #cbd5e1;
                }}
                QPushButton#PrimaryBtn {{
                    background-color: #2ecc71;
                    color: #ffffff;
                    border: none;
                    border-radius: 6px;
                    font-weight: bold;
                    padding: 10px 20px;
                }}
                QPushButton#PrimaryBtn:hover {{
                    background-color: #27ae60;
                }}
                QPushButton#SecondaryBtn {{
                    background-color: #e2e8f0;
                    color: #475569;
                    border: 1px solid #cbd5e1;
                    border-radius: 6px;
                    font-weight: bold;
                    padding: 10px 20px;
                }}
                QPushButton#SecondaryBtn:hover {{
                    background-color: #cbd5e1;
                }}
                QPushButton#AccentBtn {{
                    background-color: #e74c3c;
                    color: #ffffff;
                    border: none;
                    border-radius: 6px;
                    font-weight: bold;
                    padding: 10px 20px;
                }}
                QPushButton#AccentBtn:hover {{
                    background-color: #c0392b;
                }}
                QLabel#TabTitle {{
                    font-size: 22px;
                    font-weight: bold;
                    color: #2c3e50;
                    border-bottom: 2px solid #cbd5e1;
                    padding-bottom: 8px;
                    margin-bottom: 15px;
                }}
            """
