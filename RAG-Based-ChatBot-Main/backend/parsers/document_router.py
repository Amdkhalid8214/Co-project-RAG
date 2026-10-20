"""
DocuChat AI - Intelligent Document Processing & OCR Router
Performs page-by-page classification and routes each page between:
1. Native machine-readable text extraction (PyMuPDF / Docling) - 0 OCR overhead for digital PDFs.
2. High-precision PaddleOCR / PP-OCRv4 vision extraction for scanned or image-only pages.
3. Hybrid multi-page orchestration for mixed digital/scanned documents.
Preserves full structural provenance, reading order, table markdown, and normalized bounding boxes.
"""
import os
import logging
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

from backend.parsers.docling_parser import ParsedElement, docling_parser
from backend.parsers.paddle_ocr import paddle_ocr_engine, PaddleOCREngine

logger = logging.getLogger("document_router")

# Minimum characters required on a page to classify it as machine-readable digital text
MIN_DIGITAL_TEXT_CHARS = 40

class DocumentProcessingRouter:
    def __init__(self, ocr_engine: Optional[PaddleOCREngine] = None):
        self.ocr_engine = ocr_engine or paddle_ocr_engine

    def parse_document(
        self,
        filepath: str,
        pdf_path: Optional[str] = None
    ) -> Tuple[List[ParsedElement], Dict[str, Any]]:
        """
        Parses document using conditional extraction routing.
        Returns:
            Tuple of (List[ParsedElement], processing_stats_dict)
        """
        target_path = pdf_path if pdf_path and os.path.exists(pdf_path) else filepath
        stats = {
            "total_pages": 0,
            "digital_pages": 0,
            "scanned_pages": 0,
            "ocr_pages_executed": 0,
            "unreadable_pages": 0,
            "extraction_methods": [],
            "mean_ocr_confidence": 0.0,
        }

        # If spreadsheet (XLSX, XLS, CSV), extract structure directly with openpyxl/csv
        ext = Path(filepath).suffix.lower()
        if ext in (".xlsx", ".xls", ".csv"):
            elements = docling_parser.parse_file(filepath)
            stats["extraction_methods"].append("spreadsheet_parser")
            return elements, stats

        # If not a PDF (e.g. pure txt/html), delegate directly to docling_parser
        if not target_path.lower().endswith(".pdf"):
            elements = docling_parser.parse_file(filepath, pdf_path=pdf_path)
            stats["extraction_methods"].append("non_pdf_parser")
            return elements, stats

        # 1. Try Docling-serve container if available and healthy
        try:
            docling_elements = docling_parser._parse_with_docling_serve(target_path)
            if docling_elements and len(docling_elements) > 0:
                logger.info(f"Document processed successfully via Docling-serve container ({len(docling_elements)} elements).")
                stats["extraction_methods"].append("docling_serve")
                stats["digital_pages"] = max(e.page for e in docling_elements)
                stats["total_pages"] = stats["digital_pages"]
                return docling_elements, stats
        except Exception as e:
            logger.debug(f"Docling-serve container bypass/unavailable: {e}")

        # 2. Page-by-Page Conditional Pipeline (PyMuPDF Native + PaddleOCR)
        elements, page_stats = self._process_pdf_pages_conditionally(target_path)
        stats.update(page_stats)
        return elements, stats

    def _process_pdf_pages_conditionally(self, pdf_path: str) -> Tuple[List[ParsedElement], Dict[str, Any]]:
        import fitz

        elements: List[ParsedElement] = []
        heading_stack: List[str] = []

        try:
            doc = fitz.open(pdf_path)
        except Exception as e:
            logger.error(f"Failed to open PDF document at '{pdf_path}': {e}")
            return [], {"error": str(e)}

        total_pages = len(doc)
        digital_pages = 0
        scanned_pages = 0
        ocr_executed = 0
        unreadable_pages = 0
        ocr_confidences: List[float] = []

        for page_idx in range(total_pages):
            page_num = page_idx + 1
            page = doc[page_idx]
            page_rect = page.rect
            width, height = float(page_rect.width), float(page_rect.height)

            # Check digital text presence
            blocks = page.get_text("blocks")
            total_text_len = sum(len(b[4].strip()) for b in blocks if len(b) >= 5)

            # Classification: Digital vs Scanned
            is_scanned = total_text_len < MIN_DIGITAL_TEXT_CHARS

            if is_scanned:
                scanned_pages += 1
                logger.info(f"Page {page_num}/{total_pages}: Classified as SCANNED ({total_text_len} chars). Triggering PaddleOCR...")

                # Render page image at 150 DPI for OCR detection
                pix = page.get_pixmap(dpi=150)
                pix_bytes = pix.tobytes(output="png")

                # Run PaddleOCR
                ocr_results = self.ocr_engine.ocr_page(
                    page_pixmap_bytes=pix_bytes,
                    page_num=page_num,
                    page_width=width,
                    page_height=height,
                    dpi=150
                )

                if ocr_results:
                    ocr_executed += 1
                    for item in ocr_results:
                        text = item["text"].strip()
                        conf = item.get("confidence", 0.9)
                        ocr_confidences.append(conf)
                        bbox = item["bbox"]

                        # Check if line looks like a header
                        is_heading = len(text) < 60 and (text.isupper() or text.startswith("#"))
                        if is_heading:
                            heading_stack = [text.lstrip("#").strip()]

                        elements.append(
                            ParsedElement(
                                text=text,
                                page=page_num,
                                bboxes=[bbox],
                                heading_path=list(heading_stack),
                                elem_type="heading" if is_heading else "paragraph",
                                metadata={
                                    "extraction_method": "paddleocr",
                                    "confidence": conf,
                                    "is_scanned": True
                                }
                            )
                        )
                else:
                    # Fallback to PyMuPDF native blocks or record unreadable page
                    logger.warning(f"Page {page_num}: PaddleOCR returned 0 entries. Attempting native fallback blocks...")
                    page_elements = self._extract_native_page_blocks(page, page_num, width, height, heading_stack)
                    if page_elements:
                        elements.extend(page_elements)
                    else:
                        unreadable_pages += 1
                        logger.warning(f"Page {page_num}: Completely unreadable / empty image page.")
            else:
                digital_pages += 1
                logger.debug(f"Page {page_num}/{total_pages}: Classified as DIGITAL ({total_text_len} chars). Using native extraction.")
                page_elements = self._extract_native_page_blocks(page, page_num, width, height, heading_stack)
                elements.extend(page_elements)

        doc.close()

        stats = {
            "total_pages": total_pages,
            "digital_pages": digital_pages,
            "scanned_pages": scanned_pages,
            "ocr_pages_executed": ocr_executed,
            "unreadable_pages": unreadable_pages,
            "mean_ocr_confidence": round(sum(ocr_confidences) / len(ocr_confidences), 4) if ocr_confidences else 0.0,
            "extraction_methods": (
                ["paddleocr" if scanned_pages > 0 else "native_pymupdf"]
                if not (digital_pages > 0 and scanned_pages > 0)
                else ["hybrid_digital_and_paddleocr"]
            )
        }

        return elements, stats

    def _extract_native_page_blocks(
        self,
        page: Any,
        page_num: int,
        width: float,
        height: float,
        heading_stack: List[str]
    ) -> List[ParsedElement]:
        """Extracts text blocks and markdown tables natively using PyMuPDF."""
        elements: List[ParsedElement] = []

        # 1. Extract tables natively if present
        try:
            tabs = page.find_tables()
            for tab in tabs:
                table_md = tab.extract()
                if table_md and len(table_md) > 0:
                    header = table_md[0]
                    header_line = "| " + " | ".join(str(c or "").replace("\n", " ") for c in header) + " |"
                    sep_line = "| " + " | ".join("---" for _ in header) + " |"
                    body_lines = [
                        "| " + " | ".join(str(c or "").replace("\n", " ") for c in row) + " |"
                        for row in table_md[1:]
                    ]
                    full_table_text = "\n".join([header_line, sep_line] + body_lines)
                    t_rect = tab.bbox
                    elements.append(
                        ParsedElement(
                            text=f"[TABLE]\n{full_table_text}",
                            page=page_num,
                            bboxes=[{
                                "x0": float(t_rect[0]), "y0": float(t_rect[1]),
                                "x1": float(t_rect[2]), "y1": float(t_rect[3]),
                                "page": page_num, "page_width": width, "page_height": height,
                                "coord_origin": "TOPLEFT", "text": full_table_text
                            }],
                            heading_path=list(heading_stack),
                            elem_type="table",
                            metadata={"is_table": True, "extraction_method": "native_table"}
                        )
                    )
        except Exception as e:
            logger.debug(f"Native table extraction skipped on page {page_num}: {e}")

        # 2. Extract standard paragraph blocks
        blocks = page.get_text("blocks")
        for b in blocks:
            if len(b) < 5:
                continue
            x0, y0, x1, y1, btext = b[0], b[1], b[2], b[3], b[4]
            text = btext.strip()
            if not text or len(text) < 2:
                continue

            lines = text.splitlines()
            first_line = lines[0].strip() if lines else ""
            is_heading = first_line.startswith("#") or (len(first_line) < 60 and first_line.isupper() and len(lines) == 1)
            if is_heading:
                heading_stack.clear()
                heading_stack.append(first_line.lstrip("#").strip())

            bbox = {
                "x0": round(float(x0), 2),
                "y0": round(float(y0), 2),
                "x1": round(float(x1), 2),
                "y1": round(float(y1), 2),
                "text": text,
                "page": page_num,
                "page_width": round(float(width), 2),
                "page_height": round(float(height), 2),
                "coord_origin": "TOPLEFT"
            }

            elements.append(
                ParsedElement(
                    text=text,
                    page=page_num,
                    bboxes=[bbox],
                    heading_path=list(heading_stack),
                    elem_type="heading" if is_heading else "paragraph",
                    metadata={"extraction_method": "native_digital"}
                )
            )

        return elements

document_router = DocumentProcessingRouter()
