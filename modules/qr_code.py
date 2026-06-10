import os
import qrcode
from PIL import Image

try:
    import cv2
    HAS_OPENCV = True
except ImportError:
    HAS_OPENCV = False

# ReportLab imports for generating printable badges
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

QR_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "qr_codes"))
REPORTS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "reports"))

class QRPassGenerator:
    @staticmethod
    def generate_pass(visitor_id, full_name, company, employee_name, department_name):
        """Generate a QR Code PNG and save it."""
        os.makedirs(QR_DIR, exist_ok=True)
        filename = f"{visitor_id}.png"
        filepath = os.path.join(QR_DIR, filename)

        # Structure QR payload
        qr_data = f"SMARTVMS_PASS:{visitor_id}"

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_data)
        qr.make(fit=True)

        # Generate QR code image with high-contrast color scheme
        img = qr.make_image(fill_color="#1a252f", back_color="#ffffff")
        img.save(filepath)
        print(f"[QR] QR Code image saved to {filepath}")
        return filepath

    @staticmethod
    def generate_printable_badge_pdf(visitor, photo_path=None):
        """Generate a professional printable PDF visitor badge using ReportLab."""
        os.makedirs(REPORTS_DIR, exist_ok=True)
        pdf_path = os.path.join(REPORTS_DIR, f"Badge_{visitor['id']}.pdf")
        
        # 1. Ensure QR Code is generated
        qr_path = os.path.join(QR_DIR, f"{visitor['id']}.png")
        if not os.path.exists(qr_path):
            QRPassGenerator.generate_pass(
                visitor['id'], visitor['full_name'], visitor.get('company_name', 'N/A'),
                visitor.get('employee_name', 'N/A'), visitor.get('department_name', 'N/A')
            )
            
        # 2. Build Document
        doc = SimpleDocTemplate(pdf_path, pagesize=letter,
                                rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
        
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'TitleStyle',
            parent=styles['Heading1'],
            fontName='Helvetica-Bold',
            fontSize=16,
            textColor=colors.HexColor('#1a252f'),
            alignment=1, # Center
            spaceAfter=15
        )
        
        normal_style = ParagraphStyle(
            'NormalStyle',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=10,
            textColor=colors.HexColor('#2c3e50'),
            spaceAfter=6
        )

        label_style = ParagraphStyle(
            'LabelStyle',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=10,
            textColor=colors.HexColor('#7f8c8d'),
            spaceAfter=6
        )

        elements = []
        
        # Title
        elements.append(Paragraph("SMART VMS - VISITOR PASS", title_style))
        elements.append(Spacer(1, 10))
        
        # Badge layout - Table structure
        # Left side: Photo & QR. Right side: Text details.
        
        # Prepare photo
        if photo_path and os.path.exists(photo_path):
            try:
                # Resize photo for PDF
                photo_element = RLImage(photo_path, width=110, height=110)
            except Exception:
                photo_element = Paragraph("[Photo Error]", normal_style)
        else:
            photo_element = Paragraph("[No Photo Captured]", normal_style)
            
        qr_element = RLImage(qr_path, width=110, height=110)
        
        # Details text
        details = [
            [Paragraph("Visitor ID:", label_style), Paragraph(visitor['id'], normal_style)],
            [Paragraph("Full Name:", label_style), Paragraph(visitor['full_name'], normal_style)],
            [Paragraph("Company:", label_style), Paragraph(visitor.get('company_name', 'N/A'), normal_style)],
            [Paragraph("Purpose:", label_style), Paragraph(visitor['purpose'], normal_style)],
            [Paragraph("To Meet:", label_style), Paragraph(f"{visitor.get('employee_name', 'N/A')} ({visitor.get('department_name', 'N/A')})", normal_style)],
            [Paragraph("Entry Date:", label_style), Paragraph(visitor.get('created_at', '').split()[0], normal_style)],
        ]
        
        details_table = Table(details, colWidths=[90, 200])
        details_table.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ]))
        
        # Left column (Media), Right column (Text)
        media_table = Table([[photo_element], [Spacer(1, 10)], [qr_element]], colWidths=[130])
        media_table.setStyle(TableStyle([
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ]))
        
        badge_data = [[media_table, details_table]]
        badge_table = Table(badge_data, colWidths=[150, 310])
        badge_table.setStyle(TableStyle([
            ('BOX', (0,0), (-1,-1), 2, colors.HexColor('#00adb5')),
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f8fafc')),
            ('PADDING', (0,0), (-1,-1), 15),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ]))
        
        elements.append(badge_table)
        doc.build(elements)
        print(f"[QR] Printable Badge PDF generated at {pdf_path}")
        return pdf_path

    @staticmethod
    def scan_qr_from_frame(frame):
        """
        Detect and decode a QR Code from an OpenCV frame.
        Returns visitor_id (string) if a valid SmartVMS pass is found, otherwise None.
        """
        if not HAS_OPENCV:
            return None

        detector = cv2.QRCodeDetector()
        try:
            data, bbox, _ = detector.detectAndDecode(frame)
            if data and data.startswith("SMARTVMS_PASS:"):
                visitor_id = data.split(":")[-1]
                print(f"[QR] QR Pass detected: {visitor_id}")
                return visitor_id
        except Exception as e:
            print(f"[QR] Error scanning frame: {e}")
            
        return None
