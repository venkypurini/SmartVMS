import math
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QFrame, QGraphicsDropShadowEffect, QWidget
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPainter, QPen, QColor, QBrush, QFont, QLinearGradient

class RotatingCubeWidget(QWidget):
    """A custom widget that mathematically projects and draws a rotating 3D wireframe cube."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.angle_x = 0.0
        self.angle_y = 0.0
        self.angle_z = 0.0
        
        # 3D vertices of a cube centered at origin
        self.vertices = [
            [-1, -1, -1],
            [ 1, -1, -1],
            [ 1,  1, -1],
            [-1,  1, -1],
            [-1, -1,  1],
            [ 1, -1,  1],
            [ 1,  1,  1],
            [-1,  1,  1]
        ]
        
        # Edges linking the vertices
        self.edges = [
            (0, 1), (1, 2), (2, 3), (3, 0), # Back face
            (4, 5), (5, 6), (6, 7), (7, 4), # Front face
            (0, 4), (1, 5), (2, 6), (3, 7)  # Connecting edges
        ]
        
        # 30 FPS animation timer (~33 milliseconds interval)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.rotate_step)
        self.timer.start(33)
        
    def rotate_step(self):
        # Increment angles of rotation on multiple axes to make it spin dynamically
        self.angle_x += 0.015
        self.angle_y += 0.02
        self.angle_z += 0.008
        self.update() # Triggers paintEvent
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        cx = self.width() / 2.0
        cy = self.height() / 2.0
        scale = min(self.width(), self.height()) * 0.28
        
        projected = []
        for x, y, z in self.vertices:
            # 1. Rotate X-axis
            cos_x, sin_x = math.cos(self.angle_x), math.sin(self.angle_x)
            y1 = y * cos_x - z * sin_x
            z1 = y * sin_x + z * cos_x
            
            # 2. Rotate Y-axis
            cos_y, sin_y = math.cos(self.angle_y), math.sin(self.angle_y)
            x2 = x * cos_y + z1 * sin_y
            z2 = -x * sin_y + z1 * cos_y
            
            # 3. Rotate Z-axis
            cos_z, sin_z = math.cos(self.angle_z), math.sin(self.angle_z)
            x3 = x2 * cos_z - y1 * sin_z
            y3 = x2 * sin_z + y1 * cos_z
            
            # Perspective projection with a virtual camera distance
            distance = 3.5
            factor = 1.0 / (distance - z2 / 2.0)
            
            px = cx + x3 * scale * factor
            py = cy + y3 * scale * factor
            projected.append((int(px), int(py)))
            
        # Draw edges with a glowing cyan neon pen
        pen = QPen(QColor(0, 240, 255, 180), 2)
        painter.setPen(pen)
        for edge in self.edges:
            p1 = projected[edge[0]]
            p2 = projected[edge[1]]
            painter.drawLine(p1[0], p1[1], p2[0], p2[1])
            
        # Draw shiny silver/white vertices as glowing nodes
        painter.setBrush(QBrush(QColor(255, 255, 255, 220)))
        painter.setPen(Qt.NoPen)
        for px, py in projected:
            painter.drawEllipse(px - 4, py - 4, 8, 8)


class Splash3DWindow(QDialog):
    """A stunning dark-glassmorphic frameless loading screen displaying a 3D moving frame."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("SmartVMS")
        self.setFixedSize(500, 380)
        
        # Make the dialog completely frameless, translucently styled and staying on top
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.SubWindow)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        
        self.init_ui()
        self.apply_effects()
        
    def init_ui(self):
        # 1. Main background container frame
        self.container = QFrame(self)
        self.container.setGeometry(10, 10, 480, 360) # Leave margins for drop shadow glow
        
        # Styled with a beautiful gradient (deep space/tech theme) and cyan borders
        self.container.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                                            stop:0 #08111e, stop:0.5 #0d1e36, stop:1 #162f4c);
                border: 2px solid rgba(0, 240, 255, 0.45);
                border-radius: 20px;
            }
        """)
        
        # 2. Main layout within the container
        layout = QVBoxLayout(self.container)
        layout.setContentsMargins(20, 30, 20, 25)
        layout.setSpacing(10)
        
        # 3. Add 3D Rotating Cube
        self.cube = RotatingCubeWidget(self)
        self.cube.setFixedSize(200, 180)
        layout.addWidget(self.cube, 0, Qt.AlignCenter)
        
        # 4. Add Glowing App Title
        self.title_lbl = QLabel("SmartVMS", self)
        self.title_lbl.setFont(QFont("Segoe UI", 26, QFont.Bold))
        self.title_lbl.setStyleSheet("""
            QLabel {
                color: #00f0ff;
                background: transparent;
                border: none;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-weight: 800;
                letter-spacing: 3px;
            }
        """)
        self.title_lbl.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.title_lbl)
        
        # 5. Add Subtitle / Loading Status
        self.status_lbl = QLabel("Initializing Secure Environment...", self)
        self.status_lbl.setFont(QFont("Segoe UI", 10))
        self.status_lbl.setStyleSheet("""
            QLabel {
                color: rgba(255, 255, 255, 0.7);
                background: transparent;
                border: none;
            }
        """)
        self.status_lbl.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_lbl)
        
    def apply_effects(self):
        # Add a gorgeous neon blue drop-shadow glow to the glass container
        glow_effect = QGraphicsDropShadowEffect(self)
        glow_effect.setBlurRadius(25)
        glow_effect.setColor(QColor(0, 240, 255, 140)) # Cyan glow
        glow_effect.setOffset(0, 0)
        self.container.setGraphicsEffect(glow_effect)
