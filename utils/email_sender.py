"""
utils/email_sender.py
Handles all outgoing email notifications for SmartVMS.
Uses SMTP (Gmail by default). Settings are stored in smtp_settings.json.
"""
import os
import json
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage

import config

SETTINGS_PATH = os.path.join(os.path.dirname(config.DB_PATH), "smtp_settings.json")

# ------------------------------------------------------------------
# Settings helpers
# ------------------------------------------------------------------
DEFAULT_SETTINGS = {
    "enabled":     False,
    "host":        "smtp.gmail.com",
    "port":        465,
    "username":    "",
    "password":    "",
    "sender_name": "SmartVMS"
}

def load_smtp_settings():
    if os.path.exists(SETTINGS_PATH):
        try:
            with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            return {**DEFAULT_SETTINGS, **data}
        except Exception:
            pass
    return dict(DEFAULT_SETTINGS)

def save_smtp_settings(settings: dict):
    os.makedirs(os.path.dirname(SETTINGS_PATH), exist_ok=True)
    with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=2)

# ------------------------------------------------------------------
# Core sender
# ------------------------------------------------------------------
def _send_email(to_address: str, subject: str, html_body: str,
                attachments: list = None) -> tuple:
    cfg = load_smtp_settings()
    if not cfg.get("enabled"):
        return False, "Email notifications are disabled. Enable them in Settings tab."
    if not cfg.get("username") or not cfg.get("password"):
        return False, "SMTP credentials not configured. Go to Settings tab."
    if not to_address or "@" not in to_address:
        return False, f"Invalid recipient email: '{to_address}'"

    try:
        sender = f"{cfg['sender_name']} <{cfg['username']}>"
        msg = MIMEMultipart("related")
        msg["Subject"] = subject
        msg["From"]    = sender
        msg["To"]      = to_address
        msg.attach(MIMEText(html_body, "html", "utf-8"))

        if attachments:
            for path in attachments:
                if path and os.path.exists(path):
                    with open(path, "rb") as f:
                        img_data = f.read()
                    img = MIMEImage(img_data)
                    img.add_header("Content-ID", f"<{os.path.basename(path)}>")
                    img.add_header("Content-Disposition", "attachment",
                                   filename=os.path.basename(path))
                    msg.attach(img)

        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        if int(cfg["port"]) == 465:
            with smtplib.SMTP_SSL(cfg["host"], int(cfg["port"]), context=context, timeout=20) as server:
                server.login(cfg["username"], cfg["password"])
                server.sendmail(cfg["username"], to_address, msg.as_string())
        else:
            with smtplib.SMTP(cfg["host"], int(cfg["port"]), timeout=30) as server:
                server.ehlo()
                server.starttls(context=context)
                server.login(cfg["username"], cfg["password"])
                server.sendmail(cfg["username"], to_address, msg.as_string())

        print(f"[Email] Sent → {to_address} | {subject}")
        return True, None

    except smtplib.SMTPAuthenticationError:
        return False, ("Gmail auth failed. Use an App Password:\n"
                       "Google Account → Security → 2-Step Verification → App Passwords")
    except Exception as e:
        return False, str(e)

# ------------------------------------------------------------------
# Email 1: Approval request → Employee (host)
# ------------------------------------------------------------------
def send_approval_request_to_employee(employee_email, employee_name,
                                       visitor_name, visitor_mobile,
                                       visitor_company, purpose,
                                       visitor_code, visit_date,
                                       visitor_photo_path=None,
                                       visit_id=None,
                                       public_url=None) -> tuple:
    subject = f"[SmartVMS] Visitor Approval Request — {visitor_name}"
    
    # Auto-resolve visit_id if not provided
    if not visit_id:
        try:
            from database.db_manager import get_db_connection
            conn = get_db_connection()
            row = conn.execute("""
                SELECT vt.id FROM visits vt
                JOIN visitors v ON vt.visitor_id = v.id
                WHERE v.visitor_code = ? AND vt.approval_status = 'pending'
                ORDER BY vt.id DESC LIMIT 1;
            """, (visitor_code,)).fetchone()
            conn.close()
            if row:
                visit_id = row['id']
        except Exception as db_err:
            print(f"[Email] Failed to lookup visit_id: {db_err}")

    # Auto-resolve public_url if not provided
    if not public_url:
        try:
            from web.app import app
            public_url = app.config.get('PUBLIC_URL')
        except Exception as app_err:
            print(f"[Email] Failed to lookup PUBLIC_URL: {app_err}")

    # Build action buttons or fallback warning
    if public_url and visit_id:
        approve_url = f"{public_url.rstrip('/')}/web_approve/{visit_id}"
        reject_url = f"{public_url.rstrip('/')}/web_reject/{visit_id}"
        action_html = f"""
        <div style="margin: 28px 0; text-align: center;">
          <a href="{approve_url}" style="display: inline-block; padding: 12px 24px; margin: 0 10px; background-color: #00ff66; color: #1a1a2e; text-decoration: none; font-weight: bold; border-radius: 6px; font-size: 15px; box-shadow: 0 4px 10px rgba(0,255,102,0.2);">Approve Request</a>
          <a href="{reject_url}" style="display: inline-block; padding: 12px 24px; margin: 0 10px; background-color: #ff4444; color: #ffffff; text-decoration: none; font-weight: bold; border-radius: 6px; font-size: 15px; box-shadow: 0 4px 10px rgba(255,68,68,0.2);">Reject Request</a>
        </div>
        """
    else:
        action_html = """
        <div style="background:#fff8e1;border-left:4px solid #ffc107;padding:14px 18px;border-radius:0 8px 8px 0;margin:20px 0;">
          <p style="margin:0;color:#7a6000;font-size:13px;">
            ⚠️ Open <strong>SmartVMS → ✅ Approvals tab</strong> to Approve or Reject this request.
          </p>
        </div>
        """

    html = f"""
    <html><body style="font-family:Segoe UI,sans-serif;background:#f4f6f9;padding:20px;">
    <div style="max-width:540px;margin:auto;background:#fff;border-radius:12px;
                box-shadow:0 4px 20px rgba(0,0,0,0.08);overflow:hidden;">
      <div style="background:linear-gradient(135deg,#0d2b1e,#1a1a2e);padding:28px 32px;">
        <h1 style="color:#00ff66;margin:0;font-size:22px;">🔔 Visitor Approval Request</h1>
        <p style="color:#a0c0a8;margin:6px 0 0;">SmartVMS — Visitor Management System</p>
      </div>
      <div style="padding:28px 32px;">
        {f'''
        <div style="text-align: center; margin-bottom: 20px;">
          <img src="cid:{os.path.basename(visitor_photo_path)}" alt="Visitor Photo" style="width: 130px; height: 130px; border-radius: 8px; object-fit: cover; border: 3px solid #00ff66;">
        </div>
        ''' if visitor_photo_path and os.path.exists(visitor_photo_path) else ''}
        <p style="color:#333;font-size:15px;">Dear <strong>{employee_name}</strong>,</p>
        <p style="color:#555;">A visitor has requested to meet you. Please review:</p>
        <table style="width:100%;border-collapse:collapse;margin:16px 0;font-size:14px;">
          <tr style="background:#f0f9f4;"><td style="padding:10px 14px;color:#555;font-weight:bold;width:40%;">👤 Visitor</td><td style="padding:10px 14px;color:#222;">{visitor_name}</td></tr>
          <tr><td style="padding:10px 14px;color:#555;font-weight:bold;">📱 Mobile</td><td style="padding:10px 14px;color:#222;">{visitor_mobile}</td></tr>
          <tr style="background:#f0f9f4;"><td style="padding:10px 14px;color:#555;font-weight:bold;">🏢 Company</td><td style="padding:10px 14px;color:#222;">{visitor_company or 'N/A'}</td></tr>
          <tr><td style="padding:10px 14px;color:#555;font-weight:bold;">📋 Purpose</td><td style="padding:10px 14px;color:#222;">{purpose}</td></tr>
          <tr style="background:#f0f9f4;"><td style="padding:10px 14px;color:#555;font-weight:bold;">🔖 Code</td><td style="padding:10px 14px;color:#222;font-family:monospace;">{visitor_code}</td></tr>
          <tr><td style="padding:10px 14px;color:#555;font-weight:bold;">📅 Date</td><td style="padding:10px 14px;color:#222;">{visit_date}</td></tr>
        </table>
        {action_html}
        <p style="color:#888;font-size:12px;margin-top:24px;">Automated message from SmartVMS. Do not reply.</p>
      </div>
    </div></body></html>"""
    attachments = [visitor_photo_path] if visitor_photo_path and os.path.exists(visitor_photo_path) else []
    return _send_email(employee_email, subject, html, attachments=attachments)


# ------------------------------------------------------------------
# Email 2: QR Pass → Visitor
# ------------------------------------------------------------------
def send_qr_to_visitor(visitor_email, visitor_name, qr_path,
                        host_name, dept_name, visit_date) -> tuple:
    if not visitor_email or "@" not in visitor_email:
        return False, "Visitor has no email address on file."

    subject = "[SmartVMS] Your Visit is APPROVED — QR Pass Enclosed 🎉"
    html = f"""
    <html><body style="font-family:Segoe UI,sans-serif;background:#f4f6f9;padding:20px;">
    <div style="max-width:540px;margin:auto;background:#fff;border-radius:12px;
                box-shadow:0 4px 20px rgba(0,0,0,0.08);overflow:hidden;">
      <div style="background:linear-gradient(135deg,#0d2b1e,#1a1a2e);padding:28px 32px;">
        <h1 style="color:#00ff66;margin:0;font-size:22px;">✅ Visit Approved!</h1>
        <p style="color:#a0c0a8;margin:6px 0 0;">Your QR Pass is ready — SmartVMS</p>
      </div>
      <div style="padding:28px 32px;">
        <p style="color:#333;font-size:15px;">Dear <strong>{visitor_name}</strong>,</p>
        <p style="color:#555;">Your visit request has been <strong style="color:#00a854;">approved</strong>.
           Your QR Pass is attached to this email.</p>
        <table style="width:100%;border-collapse:collapse;margin:16px 0;font-size:14px;">
          <tr style="background:#f0f9f4;"><td style="padding:10px 14px;color:#555;font-weight:bold;width:40%;">🧑‍💼 Host</td><td style="padding:10px 14px;color:#222;">{host_name}</td></tr>
          <tr><td style="padding:10px 14px;color:#555;font-weight:bold;">🏢 Department</td><td style="padding:10px 14px;color:#222;">{dept_name or 'N/A'}</td></tr>
          <tr style="background:#f0f9f4;"><td style="padding:10px 14px;color:#555;font-weight:bold;">📅 Date</td><td style="padding:10px 14px;color:#222;">{visit_date}</td></tr>
        </table>
        <div style="background:#e8f5e9;border-left:4px solid #00c853;padding:14px 18px;border-radius:0 8px 8px 0;margin:20px 0;">
          <p style="margin:0;color:#1b5e20;font-size:13px;">
            📎 <strong>Show the attached QR code</strong> at the reception gate to check in.
          </p>
        </div>
        <p style="color:#888;font-size:12px;margin-top:24px;">Automated message from SmartVMS. Do not reply.</p>
      </div>
    </div></body></html>"""
    attachments = [qr_path] if qr_path and os.path.exists(qr_path) else []
    return _send_email(visitor_email, subject, html, attachments=attachments)


# ------------------------------------------------------------------
# Test connection
# ------------------------------------------------------------------
def test_smtp_connection() -> tuple:
    cfg = load_smtp_settings()
    if not cfg.get("username") or not cfg.get("password"):
        return False, "Enter username and password first."
    try:
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        if int(cfg["port"]) == 465:
            with smtplib.SMTP_SSL(cfg["host"], int(cfg["port"]), context=context, timeout=15) as server:
                server.login(cfg["username"], cfg["password"])
        else:
            with smtplib.SMTP(cfg["host"], int(cfg["port"]), timeout=30) as server:
                server.ehlo()
                server.starttls(context=context)
                server.login(cfg["username"], cfg["password"])
        return True, None
    except smtplib.SMTPAuthenticationError:
        return False, ("Authentication failed.\nUse a Gmail App Password:\n"
                       "Google Account → Security → 2-Step Verification → App Passwords")
    except Exception as e:
        return False, str(e)
