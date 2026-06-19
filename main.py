import sys
import os
import traceback

# Put root directory in Python path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import Qt

from database.db_manager import initialize_database
from ui.login_window import LoginWindow
from ui.main_window import MainWindow
from utils.helpers import ensure_project_directories

LOG_PATH = os.path.join(os.path.dirname(__file__), "logs", "crash.log")

def global_exception_handler(exc_type, exc_value, exc_traceback):
    """Catch ALL unhandled exceptions, log to file and show a dialog."""
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    error_msg = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    print(f"[CRITICAL] Unhandled exception:\n{error_msg}")
    # Write to crash log
    try:
        os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            import datetime
            f.write(f"\n{'='*60}\n")
            f.write(f"CRASH at {datetime.datetime.now()}\n")
            f.write(error_msg)
    except Exception:
        pass
    try:
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        msg.setWindowTitle("SmartVMS - Unexpected Error")
        msg.setText("An unexpected error occurred.\nThe application will stay open.\n\nSee logs/crash.log for full details.")
        msg.setDetailedText(error_msg)
        msg.exec_()
    except Exception:
        pass

sys.excepthook = global_exception_handler



class VMSApp:
    def __init__(self):
        # 1. Setup local folders (reports, qr_codes, visitor_images, logs)
        print("[App] Enforcing project directories...")
        ensure_project_directories()

        # 2. Setup database connection and seeding
        print("[App] Setting up database tables and indices...")
        initialize_database()

        # 3. Create PyQt App
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
        self.app = QApplication(sys.argv)
        
        self.login_window = None
        self.main_window = None

    def show_login(self):
        """Display secure authentication login dialog."""
        self.login_window = LoginWindow()
        self.login_window.login_successful.connect(self.on_login_success)
        self.login_window.show()

    def on_login_success(self, user_session):
        """Callback triggered upon successful login. Displays a 3D moving frame splash screen for 3 seconds."""
        print(f"[App] Authenticated user: '{user_session['username']}' with role: '{user_session['role']}'.")
        
        # 1. Show the 3D rotating splash window
        from ui.splash_3d import Splash3DWindow
        self.splash = Splash3DWindow()
        self.splash.show()
        
        # 2. Instantiate main window in background
        self.main_window = MainWindow(user_session)
        self.main_window.logout_requested.connect(self.on_logout)
        
        # 3. Create a timer to transition after exactly 3 seconds (3000ms)
        from PyQt5.QtCore import QTimer
        self.splash_timer = QTimer()
        self.splash_timer.setSingleShot(True)
        self.splash_timer.timeout.connect(self.transition_to_main)
        self.splash_timer.start(3000)

    def transition_to_main(self):
        """Close the 3D splash screen and display the main workspace dashboard."""
        if hasattr(self, 'splash') and self.splash:
            self.splash.close()
            self.splash = None
        if hasattr(self, 'main_window') and self.main_window:
            self.main_window.show()

    def on_logout(self):
        """Callback triggered upon logout, returning operator to login dialog."""
        self.main_window = None
        self.show_login()

    def run(self):
        """Start the app event loop by displaying the login dialog first."""
        self.show_login()
        return self.app.exec_()

if __name__ == "__main__":
    app_instance = VMSApp()
    sys.exit(app_instance.run())
