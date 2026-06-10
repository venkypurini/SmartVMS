from PyQt5.QtWidgets import QFrame, QVBoxLayout, QLabel
from PyQt5.QtCore import Qt, pyqtSlot
from PyQt5.QtGui import QFont, QPixmap, QImage

class MetricCard(QFrame):
    """Custom Reusable Metric Card Widget with Glassmorphism styles."""
    def __init__(self, title, value="0", footer="", accent_color="#2ecc71", parent=None):
        super().__init__(parent)
        self.setObjectName("MetricCard")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(4)
        
        self.title_lbl = QLabel(title)
        self.title_lbl.setObjectName("MetricTitle")
        self.title_lbl.setFont(QFont("Segoe UI", 10, QFont.Bold))
        layout.addWidget(self.title_lbl)
        
        self.value_lbl = QLabel(value)
        self.value_lbl.setObjectName("MetricValue")
        self.value_lbl.setFont(QFont("Segoe UI", 24, QFont.Bold))
        self.value_lbl.setStyleSheet(f"color: {accent_color};")
        layout.addWidget(self.value_lbl)
        
        self.footer_lbl = QLabel(footer)
        self.footer_lbl.setObjectName("MetricTrend")
        self.footer_lbl.setFont(QFont("Segoe UI", 8))
        self.footer_lbl.setStyleSheet("color: #7f8c8d;")
        layout.addWidget(self.footer_lbl)

    def set_value(self, value):
        self.value_lbl.setText(str(value))

    def set_footer(self, text):
        self.footer_lbl.setText(str(text))


class CameraWidget(QLabel):
    """Custom webcam renderer widget."""
    def __init__(self, width=640, height=480, placeholder="Webcam Feed Offline", parent=None):
        super().__init__(parent)
        self.setFixedSize(width, height)
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet("background-color: #1a1a24; border-radius: 8px;")
        self.setText(placeholder)
        self.setFont(QFont("Segoe UI", 12))

    @pyqtSlot(QImage)
    def render_frame(self, q_img):
        """Receive QImage frame and render it scaled."""
        scaled_img = q_img.scaled(self.width(), self.height(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.setPixmap(QPixmap.fromImage(scaled_img))
        
    def set_offline(self, placeholder="Webcam Feed Offline"):
        self.clear()
        self.setText(placeholder)
