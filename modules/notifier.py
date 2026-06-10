import os
import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

REPORTS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "reports"))
LOG_PATH = os.path.join(REPORTS_DIR, "notifications_log.txt")

class Notifier:
    # Optional SMTP configuration class variables (can be loaded from DB/config)
    SMTP_ENABLED = False
    SMTP_HOST = "smtp.gmail.com"
    SMTP_PORT = 587
    SMTP_USER = "your-email@gmail.com"
    SMTP_PASS = "your-app-password"
    SMTP_SENDER = "SmartVMS Alert <alerts@smartvms.com>"

    @staticmethod
    def _log_local_notification(subject, recipient_email, body):
        """Log the notification to a local file for audit and demonstration purposes."""
        os.makedirs(REPORTS_DIR, exist_ok=True)
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"========================================\n" \
                    f"TIME: {timestamp}\n" \
                    f"TO: {recipient_email}\n" \
                    f"SUBJECT: {subject}\n" \
                    f"----------------------------------------\n" \
                    f"{body}\n" \
                    f"========================================\n\n"
        
        try:
            with open(LOG_PATH, "a") as f:
                f.write(log_entry)
            print(f"[Notifier] Local notification logged to {LOG_PATH}")
        except Exception as e:
            print(f"[Notifier] Failed to write local log: {e}")

    @staticmethod
    def _send_email(recipient, subject, body_html, body_text):
        """Send an HTML email using SMTP if enabled, otherwise fall back to local logging."""
        if not Notifier.SMTP_ENABLED:
            Notifier._log_local_notification(subject, recipient, body_text)
            return True, "Local log created (SMTP disabled)"

        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = Notifier.SMTP_SENDER
            msg['To'] = recipient

            part1 = MIMEText(body_text, 'plain')
            part2 = MIMEText(body_html, 'html')

            msg.attach(part1)
            msg.attach(part2)

            with smtplib.SMTP(Notifier.SMTP_HOST, Notifier.SMTP_PORT) as server:
                server.starttls()
                server.login(Notifier.SMTP_USER, Notifier.SMTP_PASS)
                server.sendmail(Notifier.SMTP_SENDER, recipient, msg.as_string())
            
            print(f"[Notifier] Email sent successfully to {recipient}")
            return True, "Email sent successfully"
        except Exception as e:
            err_msg = str(e)
            print(f"[Notifier] Email delivery failed: {err_msg}")
            # Fall back to logging it locally
            Notifier._log_local_notification(f"[FAILED EMAIL] {subject}", recipient, body_text)
            return False, err_msg

    @classmethod
    def notify_employee_arrival(cls, visitor, employee):
        """Send arrival notification to the employee that a visitor is waiting for them."""
        subject = f"SmartVMS Alert: Visitor {visitor['full_name']} has arrived"
        
        body_text = f"Hello {employee['name']},\n\n" \
                    f"This is to notify you that a visitor has checked in to meet you:\n\n" \
                    f"Visitor ID: {visitor['id']}\n" \
                    f"Name: {visitor['full_name']}\n" \
                    f"Company: {visitor.get('company_name', 'N/A')}\n" \
                    f"Purpose: {visitor['purpose']}\n" \
                    f"Check-In Time: {datetime.datetime.now().strftime('%H:%M')}\n\n" \
                    f"Please proceed to the reception desk or contact security if you did not expect this visit.\n\n" \
                    f"Best Regards,\nSmartVMS Admin Team"
                    
        body_html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; color: #333333; line-height: 1.6;">
            <div style="max-width: 600px; margin: 0 auto; border: 1px solid #e2e8f0; padding: 20px; border-radius: 8px; background-color: #ffffff;">
                <div style="background-color: #00adb5; color: white; padding: 10px 20px; border-radius: 6px 6px 0 0; text-align: center;">
                    <h2>SmartVMS Check-In Alert</h2>
                </div>
                <div style="padding: 20px 10px;">
                    <p>Hello <strong>{employee['name']}</strong>,</p>
                    <p>This is to notify you that a visitor has checked in to meet you:</p>
                    <table style="width: 100%; border-collapse: collapse; margin-top: 15px;">
                        <tr style="background-color: #f8fafc;">
                            <td style="padding: 8px; font-weight: bold; width: 35%;">Visitor ID:</td>
                            <td style="padding: 8px;">{visitor['id']}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px; font-weight: bold;">Name:</td>
                            <td style="padding: 8px;">{visitor['full_name']}</td>
                        </tr>
                        <tr style="background-color: #f8fafc;">
                            <td style="padding: 8px; font-weight: bold;">Company:</td>
                            <td style="padding: 8px;">{visitor.get('company_name', 'N/A')}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px; font-weight: bold;">Purpose:</td>
                            <td style="padding: 8px;">{visitor['purpose']}</td>
                        </tr>
                        <tr style="background-color: #f8fafc;">
                            <td style="padding: 8px; font-weight: bold;">Check-In Time:</td>
                            <td style="padding: 8px;">{datetime.datetime.now().strftime('%H:%M:%S')}</td>
                        </tr>
                    </table>
                    <p style="margin-top: 25px; font-size: 13px; color: #7f8c8d;">Please contact reception or go to the lobby to receive your visitor.</p>
                </div>
                <div style="border-top: 1px solid #e2e8f0; padding-top: 15px; font-size: 11px; color: #95a5a6; text-align: center;">
                    This is an automated notification from SmartVMS. Please do not reply directly to this email.
                </div>
            </div>
        </body>
        </html>
        """
        return cls._send_email(employee['email'], subject, body_html, body_text)

    @classmethod
    def notify_employee_checkout(cls, visitor, employee, duration_minutes):
        """Send exit notification to the employee that their visitor has checked out."""
        subject = f"SmartVMS Alert: Visitor {visitor['full_name']} has checked out"
        
        body_text = f"Hello {employee['name']},\n\n" \
                    f"This is to notify you that your visitor {visitor['full_name']} ({visitor['id']}) has checked out.\n\n" \
                    f"Visit Duration: {duration_minutes} minutes\n" \
                    f"Check-Out Time: {datetime.datetime.now().strftime('%H:%M')}\n\n" \
                    f"Best Regards,\nSmartVMS Admin Team"
                    
        body_html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; color: #333333; line-height: 1.6;">
            <div style="max-width: 600px; margin: 0 auto; border: 1px solid #e2e8f0; padding: 20px; border-radius: 8px; background-color: #ffffff;">
                <div style="background-color: #34495e; color: white; padding: 10px 20px; border-radius: 6px 6px 0 0; text-align: center;">
                    <h2>SmartVMS Check-Out Alert</h2>
                </div>
                <div style="padding: 20px 10px;">
                    <p>Hello <strong>{employee['name']}</strong>,</p>
                    <p>This is to notify you that your visitor has checked out of the premises:</p>
                    <table style="width: 100%; border-collapse: collapse; margin-top: 15px;">
                        <tr style="background-color: #f8fafc;">
                            <td style="padding: 8px; font-weight: bold; width: 35%;">Visitor ID:</td>
                            <td style="padding: 8px;">{visitor['id']}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px; font-weight: bold;">Name:</td>
                            <td style="padding: 8px;">{visitor['full_name']}</td>
                        </tr>
                        <tr style="background-color: #f8fafc;">
                            <td style="padding: 8px; font-weight: bold;">Visit Duration:</td>
                            <td style="padding: 8px;">{duration_minutes} minutes</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px; font-weight: bold;">Check-Out Time:</td>
                            <td style="padding: 8px;">{datetime.datetime.now().strftime('%H:%M:%S')}</td>
                        </tr>
                    </table>
                </div>
                <div style="border-top: 1px solid #e2e8f0; padding-top: 15px; font-size: 11px; color: #95a5a6; text-align: center;">
                    This is an automated notification from SmartVMS. Please do not reply directly to this email.
                </div>
            </div>
        </body>
        </html>
        """
        return cls._send_email(employee['email'], subject, body_html, body_text)
