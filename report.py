from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import io

def make_pdf(summary, errors, jira_url):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    
    c.setFont("Helvetica-Bold", 18)
    c.drawString(50, height - 50, "🚨 Incident Report")
    
    c.setFont("Helvetica", 12)
    c.drawString(50, height - 100, f"Root Cause: {summary}")
    c.drawString(50, height - 130, f"Jira Ticket: {jira_url}")
    
    c.drawString(50, height - 170, "Top Errors:")
    y = height - 190
    for e in errors[:7]:
        c.drawString(70, y, f"Line {e['line']}: {e['text'][:80]}...")
        y -= 20
    
    c.drawString(50, y - 30, "Checklist: [ ] Review logs [ ] Scale DB [ ] Notify team")
    
    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer