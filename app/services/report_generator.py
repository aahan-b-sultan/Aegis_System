from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from io import BytesIO
from datetime import datetime

def generate_pdf_report(scan_data):
    """
    Generates a PDF file in memory based on a Scan Log.
    """
    # Create a file buffer in RAM (not on disk)
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    # --- 1. HEADER SECTION (Purple/Dark Theme) ---
    # Draw a top banner
    c.setFillColorRGB(0.1, 0.1, 0.2) # Dark Blue/Grey
    c.rect(0, height - 120, width, 120, fill=1, stroke=0)
    
    # Title text
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 28)
    c.drawString(50, height - 60, "AEGIS SURVEILLANCE")
    
    c.setFont("Helvetica", 12)
    c.setFillColorRGB(0.6, 0.8, 1) # Light Blue
    c.drawString(50, height - 85, "Micro-Doppler Target Classification System | v2.0")

    # --- 2. INCIDENT SUMMARY ---
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, height - 170, "INCIDENT REPORT SUMMARY")
    
    # Draw a line
    c.setStrokeColor(colors.gray)
    c.line(50, height - 180, width - 50, height - 180)

    # Data Fields
    y = height - 220
    spacing = 30
    
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "Scan Reference ID:")
    c.setFont("Helvetica", 12)
    c.drawString(200, y, f"#{scan_data.id:06d}") # e.g. #000005
    
    y -= spacing
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "Timestamp:")
    c.setFont("Helvetica", 12)
    # Format: 11 Jan 2026, 14:30:00
    c.drawString(200, y, scan_data.timestamp.strftime('%d %b %Y, %H:%M:%S'))
    
    y -= spacing
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "Data Source:")
    c.setFont("Courier", 12) # Monospace for filenames
    c.drawString(200, y, scan_data.filename)

    # --- 3. THREAT ANALYSIS BOX ---
    y -= 80
    
    # Logic for Color
    if scan_data.is_threat:
        box_color = colors.mistyrose
        border_color = colors.red
        text_color = colors.red
        status_text = "THREAT CONFIRMED"
    else:
        box_color = colors.lightcyan
        border_color = colors.blue
        text_color = colors.blue
        status_text = "CLEARED / NEUTRAL"

    # Draw the box
    c.setFillColor(box_color)
    c.setStrokeColor(border_color)
    c.setLineWidth(2)
    c.roundRect(50, y - 60, 400, 80, 10, fill=1, stroke=1)
    
    # Text inside box
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(70, y - 10, "AI CLASSIFICATION:")
    
    c.setFont("Helvetica-Bold", 24)
    c.drawString(230, y - 10, scan_data.target_class.upper())
    
    c.setFont("Helvetica-Bold", 12)
    c.drawString(70, y - 40, "CONFIDENCE SCORE:")
    c.drawString(230, y - 40, f"{scan_data.confidence:.2f}%")

    # Status Badge
    c.setFillColor(text_color)
    c.setFont("Helvetica-Bold", 14)
    c.drawRightString(430, y - 40, status_text)

    # --- 4. FOOTER ---
    c.setFillColor(colors.gray)
    c.setFont("Helvetica-Oblique", 9)
    c.drawString(50, 50, "This document was generated automatically by the AEGIS Neural Network.")
    c.drawString(50, 38, "Unauthorized distribution is prohibited.")
    
    # Page Number
    c.drawRightString(width - 50, 50, "Page 1 of 1")

    # Finalize
    c.showPage()
    c.save()
    
    buffer.seek(0)
    return buffer