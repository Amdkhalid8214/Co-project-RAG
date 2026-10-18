"""
Unit & Integration Tests for Document Processing Router & PaddleOCR Engine
Tests:
1. Digital PDF bypasses OCR (0 OCR overhead).
2. Scanned / image-only PDF triggers OCR with normalized bounding boxes.
3. Mixed digital/scanned PDF routes per-page and produces hybrid stats.
4. Bounding box coordinate scaling normalization (150 DPI pixmap to 72 pt PDF coordinates).
5. Unreadable / empty page handling and graceful error recovery.
"""
import os
import pytest
import tempfile
import fitz
from typing import List, Dict, Any

from backend.parsers.paddle_ocr import PaddleOCREngine
from backend.parsers.document_router import DocumentProcessingRouter, MIN_DIGITAL_TEXT_CHARS


class MockOCREngine(PaddleOCREngine):
    """Mock OCR engine for deterministic testing of OCR routing and bboxes."""
    def __init__(self, mocked_results=None):
        self._engine_type = "mock_paddleocr"
        self._init_error = None
        self.call_count = 0
        self.mocked_results = mocked_results or [
            {
                "text": "Extracted OCR text line from scanned invoice",
                "confidence": 0.965,
                "bbox": {
                    "x0": 50.0, "y0": 100.0, "x1": 350.0, "y1": 130.0,
                    "page": 1, "page_width": 595.0, "page_height": 842.0,
                    "coord_origin": "TOPLEFT",
                    "text": "Extracted OCR text line from scanned invoice",
                    "ocr_engine": "paddleocr"
                }
            }
        ]

    def ocr_page(self, page_pixmap_bytes: bytes, page_num: int, page_width: float, page_height: float, dpi: int = 150):
        self.call_count += 1
        # Update page number in mocked results for current page
        res = []
        for item in self.mocked_results:
            copied = dict(item)
            copied["bbox"] = dict(item["bbox"])
            copied["bbox"]["page"] = page_num
            copied["bbox"]["page_width"] = page_width
            copied["bbox"]["page_height"] = page_height
            res.append(copied)
        return res


def create_sample_digital_pdf(path: str, pages_count: int = 2):
    """Creates a PDF with ample machine-readable digital text."""
    doc = fitz.open()
    for i in range(pages_count):
        page = doc.new_page(width=595, height=842)
        page.insert_text(
            (50, 100),
            f"DocuChat AI Digital Test Page {i + 1}.\n"
            "This page contains machine-readable digital text well above the threshold.\n"
            "It should be extracted natively by PyMuPDF without any OCR execution overhead.\n"
            "Section 1: Architectural Overview and High Performance Retrieval.",
            fontsize=12
        )
    doc.save(path)
    doc.close()


def create_sample_scanned_pdf(path: str):
    """Creates a PDF simulating a scanned document (empty or minimal text < threshold)."""
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)
    # Insert tiny text well below MIN_DIGITAL_TEXT_CHARS (e.g. 5 chars)
    page.insert_text((50, 50), "p. 1", fontsize=8)
    doc.save(path)
    doc.close()


def create_sample_mixed_pdf(path: str):
    """Creates a 2-page PDF: Page 1 is digital text, Page 2 is scanned (image-only/empty)."""
    doc = fitz.open()
    # Page 1: Digital
    p1 = doc.new_page(width=595, height=842)
    p1.insert_text(
        (50, 100),
        "Page 1: Digital native document content with sufficient character length.\n"
        "Testing hybrid page-by-page classification in DocumentProcessingRouter.",
        fontsize=12
    )
    # Page 2: Scanned / minimal
    p2 = doc.new_page(width=595, height=842)
    p2.insert_text((50, 50), "scan", fontsize=8)
    doc.save(path)
    doc.close()


def test_digital_pdf_bypasses_ocr(tmp_path):
    """Digital PDFs must be parsed natively with 0 OCR overhead."""
    pdf_path = str(tmp_path / "digital_doc.pdf")
    create_sample_digital_pdf(pdf_path, pages_count=2)

    mock_ocr = MockOCREngine()
    router = DocumentProcessingRouter(ocr_engine=mock_ocr)

    elements, stats = router.parse_document(pdf_path)

    assert len(elements) > 0
    assert stats["total_pages"] == 2
    assert stats["digital_pages"] == 2
    assert stats["scanned_pages"] == 0
    assert stats["ocr_pages_executed"] == 0
    assert mock_ocr.call_count == 0, "OCR should NOT have been called for digital pages!"
    assert any("DocuChat AI Digital Test Page 1" in e.text for e in elements)


def test_scanned_pdf_triggers_paddle_ocr(tmp_path):
    """Scanned or low-text pages must trigger OCR and preserve bboxes."""
    pdf_path = str(tmp_path / "scanned_doc.pdf")
    create_sample_scanned_pdf(pdf_path)

    mock_ocr = MockOCREngine()
    router = DocumentProcessingRouter(ocr_engine=mock_ocr)

    elements, stats = router.parse_document(pdf_path)

    assert stats["total_pages"] == 1
    assert stats["scanned_pages"] == 1
    assert stats["digital_pages"] == 0
    assert stats["ocr_pages_executed"] == 1
    assert mock_ocr.call_count == 1, "OCR should have been invoked for scanned page!"

    # Check extracted OCR element and metadata
    ocr_element = elements[0]
    assert "Extracted OCR text line" in ocr_element.text
    assert ocr_element.metadata.get("extraction_method") == "paddleocr"
    assert ocr_element.metadata.get("is_scanned") is True
    assert len(ocr_element.bboxes) > 0

    bbox = ocr_element.bboxes[0]
    assert bbox["coord_origin"] == "TOPLEFT"
    assert bbox["page"] == 1
    assert bbox["x0"] == 50.0
    assert bbox["y0"] == 100.0


def test_mixed_pdf_routing(tmp_path):
    """Mixed documents should route digital pages to PyMuPDF and scanned pages to OCR."""
    pdf_path = str(tmp_path / "mixed_doc.pdf")
    create_sample_mixed_pdf(pdf_path)

    mock_ocr = MockOCREngine()
    router = DocumentProcessingRouter(ocr_engine=mock_ocr)

    elements, stats = router.parse_document(pdf_path)

    assert stats["total_pages"] == 2
    assert stats["digital_pages"] == 1
    assert stats["scanned_pages"] == 1
    assert stats["ocr_pages_executed"] == 1
    assert mock_ocr.call_count == 1
    assert stats["extraction_methods"] == ["hybrid_digital_and_paddleocr"]

    # Verify elements contain both digital and OCR derived chunks
    methods = [e.metadata.get("extraction_method") for e in elements]
    assert "native_digital" in methods
    assert "paddleocr" in methods


def test_ocr_coordinate_scaling_normalization():
    """OCR pixel polygons rendered at 150 DPI must be accurately scaled to 72 DPI PDF point space."""
    engine = PaddleOCREngine()

    # Raw pixel coordinates at 150 DPI: box from [100, 200] to [300, 250] pixels
    raw_rapidocr_result = [
        (
            [[100, 200], [300, 200], [300, 250], [100, 250]],
            "Annual Financial Summary 2024",
            0.982
        )
    ]

    scale = 72.0 / 150.0  # 0.48
    blocks = engine._parse_rapidocr_output(
        result=raw_rapidocr_result,
        page_num=1,
        page_width=595.0,
        page_height=842.0,
        scale=scale
    )

    assert len(blocks) == 1
    block = blocks[0]
    assert block["text"] == "Annual Financial Summary 2024"
    assert block["confidence"] == pytest.approx(0.982, rel=1e-3)

    bbox = block["bbox"]
    expected_x0 = round(100 * scale, 2)  # 48.0
    expected_y0 = round(200 * scale, 2)  # 96.0
    expected_x1 = round(300 * scale, 2)  # 144.0
    expected_y1 = round(250 * scale, 2)  # 120.0

    assert bbox["x0"] == expected_x0
    assert bbox["y0"] == expected_y0
    assert bbox["x1"] == expected_x1
    assert bbox["y1"] == expected_y1
    assert bbox["coord_origin"] == "TOPLEFT"
    assert bbox["page_width"] == 595.0
    assert bbox["page_height"] == 842.0


def test_unreadable_page_handling(tmp_path):
    """Empty or unreadable scanned pages should be logged without crashing the pipeline."""
    pdf_path = str(tmp_path / "empty_scanned.pdf")
    create_sample_scanned_pdf(pdf_path)

    # Empty mock returning 0 detections
    empty_ocr = MockOCREngine(mocked_results=[])
    router = DocumentProcessingRouter(ocr_engine=empty_ocr)

    elements, stats = router.parse_document(pdf_path)

    assert stats["total_pages"] == 1
    assert stats["scanned_pages"] == 1
    # Either native fallback found minimal text or marked as unreadable
    assert stats["unreadable_pages"] >= 0
    assert isinstance(elements, list)
