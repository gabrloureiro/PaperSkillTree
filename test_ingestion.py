import fitz
from src.services.ingestion_service import PDFIngester
import json

def create_dummy_pdf(filepath):
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text(fitz.Point(50, 50), "Abstract", fontsize=14, fontname="helv", fontfile=None)
    page.insert_text(fitz.Point(50, 70), "This is the abstract of the paper. It summarizes things.", fontsize=12)
    
    page.insert_text(fitz.Point(50, 120), "Introduction", fontsize=14, fontname="helv", fontfile=None)
    page.insert_text(fitz.Point(50, 140), "This is the introduction. We introduce the topic here.", fontsize=12)
    
    page.insert_text(fitz.Point(50, 200), "References", fontsize=14, fontname="helv", fontfile=None)
    page.insert_text(fitz.Point(50, 220), "[1] John Doe, 2023. A great paper.", fontsize=12)
    
    doc.save(filepath)

if __name__ == "__main__":
    pdf_path = "dummy_test.pdf"
    create_dummy_pdf(pdf_path)
    
    ingester = PDFIngester()
    try:
        chunks = ingester.parse_pdf(pdf_path)
        print("Successfully parsed PDF into chunks:")
        print(json.dumps(chunks, indent=2))
    except Exception as e:
        print("Error during parsing:", e)
