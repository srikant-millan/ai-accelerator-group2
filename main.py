from fastapi import FastAPI, File, UploadFile
from fastapi.staticfiles import StaticFiles
from fastapi.responses import StreamingResponse
import shutil
import os
from parser import parse_log
from ai import analyze_errors
from alert import send_alerts
from report import make_pdf
from dotenv import load_dotenv

load_dotenv()
app = FastAPI()
app.mount("/", StaticFiles(directory="static", html=True), name="static")

@app.post("/analyze")
async def analyze(file: UploadFile = File(...)):
    path = f"uploads/{file.filename}"
    with open(path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    
    parsed = parse_log(path)
    summary = "No errors found."
    if parsed["errors"]:
        summary = analyze_errors(parsed["errors"])
    
    ticket_url = send_alerts(summary, parsed["errors"])
    
    pdf_buffer = make_pdf(summary, parsed["errors"], ticket_url)
    
    os.remove(path)  # Clean up
    return StreamingResponse(pdf_buffer, media_type="application/pdf",
                            headers={"Content-Disposition": "attachment; filename=incident-report.pdf"})