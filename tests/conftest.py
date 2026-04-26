import pytest
import os
import fitz
from src.services.ingestion_service import PDFIngester

@pytest.fixture
def test_pdf_path(tmp_path):
    pdf_path = tmp_path / "test.pdf"
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text(fitz.Point(50, 50), "Abstract", fontsize=14, fontname="helv")
    page.insert_text(fitz.Point(50, 70), "This is the abstract of the paper.", fontsize=12)
    
    page.insert_text(fitz.Point(50, 120), "Introduction", fontsize=14, fontname="helv")
    page.insert_text(fitz.Point(50, 140), "This is the introduction. We introduce the topic.", fontsize=12)
    
    page.insert_text(fitz.Point(50, 200), "References", fontsize=14, fontname="helv")
    page.insert_text(fitz.Point(50, 220), "[1] John Doe, 2023.", fontsize=12)
    
    doc.save(str(pdf_path))
    return str(pdf_path)

@pytest.fixture
def ingester():
    return PDFIngester()
