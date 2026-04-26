import fitz
from typing import List, Dict
from unstructured.partition.text import partition_text
from src.models.state import PaperChunkInput

class PDFIngester:
    def parse_pdf(self, filepath: str) -> List[PaperChunkInput]:
        """
        Parses a PDF file, sanitizes it using PyMuPDF, and segments it using unstructured.
        """
        raw_text = self._extract_text(filepath)
        chunks = self._segment_text(raw_text)
        return chunks

    def _extract_text(self, filepath: str) -> str:
        doc = fitz.open(filepath)
        clean_text_blocks = []
        skip_rest = False
        
        for page in doc:
            if skip_rest:
                break
            blocks = page.get_text("blocks")
            for b in blocks:
                if b[6] == 0:  # Text block
                    text = b[4].strip()
                    if not text:
                        continue
                    text_lower = text.lower()
                    if text_lower == "references" or text_lower == "bibliography":
                        skip_rest = True
                        break
                    if text.isdigit():
                        continue
                    clean_text_blocks.append(text)
        return "\n\n".join(clean_text_blocks)

    def _segment_text(self, raw_text: str) -> List[PaperChunkInput]:
        elements = partition_text(text=raw_text)
        chunks: List[PaperChunkInput] = []
        current_header = "Introduction"
        current_text = []
        
        for element in elements:
            element_type = element.category
            element_text = str(element).strip()
            if not element_text:
                continue
            if element_type == "Title":
                if current_text:
                    chunks.append({
                        "raw_text": "\n".join(current_text),
                        "section_header": current_header
                    })
                    current_text = []
                current_header = element_text
            else:
                current_text.append(element_text)
                
        if current_text:
            chunks.append({
                "raw_text": "\n".join(current_text),
                "section_header": current_header
            })
        return chunks
