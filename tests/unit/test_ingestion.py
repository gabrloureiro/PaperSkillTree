import pytest
import json
from src.services.ingestion_service import PDFIngester

def test_parse_pdf(ingester, test_pdf_path):
    chunks = ingester.parse_pdf(test_pdf_path)
    
    assert len(chunks) >= 2
    
    # Check for Abstract chunk
    abstract_chunk = next((c for c in chunks if c["section_header"] == "Abstract"), None)
    assert abstract_chunk is not None
    assert "abstract" in abstract_chunk["raw_text"]
    
    # Check for Introduction chunk
    intro_chunk = next((c for c in chunks if c["section_header"] == "Introduction"), None)
    assert intro_chunk is not None
    assert "introduction" in intro_chunk["raw_text"]

def test_references_exclusion(ingester, test_pdf_path):
    chunks = ingester.parse_pdf(test_pdf_path)
    
    # Ensure References section is NOT in chunks (based on ingestion.py logic)
    ref_chunk = next((c for c in chunks if c["section_header"] == "References"), None)
    assert ref_chunk is None
