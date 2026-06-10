import time
import math
import numpy as np

try:
    import cv2
    HAS_OPENCV = True
except ImportError:
    HAS_OPENCV = False

# Import PyQt5 classes safely
try:
    from PyQt5.QtCore import QThread, pyqtSignal, Qt
    from PyQt5.QtGui import QImage
    HAS_PYQT = True
except ImportError:
    HAS_PYQT = False
    # Mocking basic QThread if not available (to avoid syntax errors on import)
    class QThread:
        pass
    class pyqtSignal:
        def __init__(self, *args): pass

class CameraThread(QThread):
    # Signal that emits the QImage to be displayed in the QLabel
    if HAS_PYQT:
        frame_ready = pyqtSignal(QImage)
    else:
        frame_ready = None

    def __init__(self, parent=None):
        super().__init__(parent)
        self.running = False
        self.cap = None
        self.width = 640
        self.height = 480

    def run(self):
        self.running = True
        
        # Try to initialize physical camera
        if HAS_OPENCV:
            try:
                # VideoCapture(0, cv2.CAP_DSHOW) on Windows reduces startup latency
                self.cap = cv2.VideoCapture(0)
                # Check if it opened successfully
                if not self.cap.isOpened():
                    self.cap = None
            except Exception as e:
                print(f"[Camera] Error initializing webcam: {e}")
                self.cap = None

        if self.cap:
            print("[Camera] Physical webcam initialized successfully.")
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
            
            while self.running:
                ret, frame = self.cap.read()
                if not ret:
                    # If physical read fails temporarily, use simulation frame
                    self._emit_simulated_frame()
                    time.sleep(0.04) # ~25 FPS
                    continue
                
                # Flip frame horizontally for natural mirror effect
                frame = cv2.flip(frame, 1)
                self._emit_opencv_frame(frame)
                time.sleep(0.03) # ~30 FPS
                
            self.cap.release()
            self.cap = None
        else:
            print("[Camera] No physical webcam detected. Starting simulated feed.")
            # Run simulation loop
            while self.running:
                self._emit_simulated_frame()
                time.sleep(0.04) # ~25 FPS

    def stop(self):
        """Request the camera loop to stop and wait for thread to finish."""
        self.running = False
        self.wait()

    def _emit_opencv_frame(self, frame):
        """Convert OpenCV BGR image to QImage and emit it."""
        if not HAS_PYQT:
            return
            
        rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        q_img = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888).copy()
        self.frame_ready.emit(q_img)

    def _emit_simulated_frame(self):
        """Generate a simulated animated frame with a grid and facial wireframe for UI feedback."""
        if not HAS_PYQT:
            return
            
        # Create dark blue background
        img = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        img[:, :] = [24, 24, 36] # HEX #181824
        
        # Draw dynamic tech grid lines
        grid_spacing = 40
        t = time.time()
        offset_y = int((t * 20) % grid_spacing)
        offset_x = int((t * 20) % grid_spacing)
        
        for y in range(offset_y, self.height, grid_spacing):
            cv2.line(img, (0, y), (self.width, y), (40, 40, 60), 1) if HAS_OPENCV else None
        for x in range(offset_x, self.width, grid_spacing):
            cv2.line(img, (x, 0), (x, self.height), (40, 40, 60), 1) if HAS_OPENCV else None
            
        # Draw moving scanner bar
        scan_y = int((self.height / 2) + math.sin(t * 3) * (self.height / 2.5))
        if HAS_OPENCV:
            # Draw gradient line
            cv2.line(img, (50, scan_y), (self.width - 50, scan_y), (0, 173, 181), 2)
            cv2.putText(img, "SCANNING ACTIVE...", (60, scan_y - 10), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 173, 181), 1)
            
            # Draw facial outline oval
            center_x, center_y = self.width // 2, self.height // 2
            cv2.ellipse(img, (center_x, center_y), (100, 140), 0, 0, 360, (0, 173, 181), 1)
            
            # Draw target indicators
            size = 20
            # Top-left corner
            cv2.line(img, (center_x - 100, center_y - 140), (center_x - 100 + size, center_y - 140), (0, 173, 181), 2)
            cv2.line(img, (center_x - 100, center_y - 140), (center_x - 100, center_y - 140 + size), (0, 173, 181), 2)
            # Top-right
            cv2.line(img, (center_x + 100, center_y - 140), (center_x + 100 - size, center_y - 140), (0, 173, 181), 2)
            cv2.line(img, (center_x + 100, center_y - 140), (center_x + 100, center_y - 140 + size), (0, 173, 181), 2)
            # Bottom-left
            cv2.line(img, (center_x - 100, center_y + 140), (center_x - 100 + size, center_y + 140), (0, 173, 181), 2)
            cv2.line(img, (center_x - 100, center_y + 140), (center_x - 100, center_y + 140 - size), (0, 173, 181), 2)
            # Bottom-right
            cv2.line(img, (center_x + 100, center_y + 140), (center_x + 100 - size, center_y + 140), (0, 173, 181), 2)
            cv2.line(img, (center_x + 100, center_y + 140), (center_x + 100, center_y + 140 - size), (0, 173, 181), 2)

            # Draw Simulated Text
            cv2.putText(img, "WEBCAM EMULATOR ACTIVE", (30, 40), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (160, 160, 180), 1)
            cv2.putText(img, "Align face in the box to register", (center_x - 140, self.height - 30), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (160, 160, 180), 1)

            # Convert BGR to RGB
            rgb_image = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        else:
            # Very basic fallback in case OpenCV is entirely missing (draw plain color)
            rgb_image = img
            
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        q_img = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888).copy()
        self.frame_ready.emit(q_img)
