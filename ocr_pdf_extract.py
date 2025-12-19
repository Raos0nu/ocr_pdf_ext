import argparse                     # AUTHOR (@raos0nu)(https://github.com/Raos0nu)
import os
import re
from pathlib import Path

# Import dependencies with error handling
try:
    import pytesseract
    # Set Tesseract path based on environment (Windows vs Linux/Vercel)
    if os.name == "nt":  # Windows
        pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    # On Linux/Vercel, Tesseract should be in PATH, so we don't set it explicitly
    # If Tesseract is not found, pytesseract will raise TesseractNotFoundError
    PYTESSERACT_AVAILABLE = True
except ImportError:
    PYTESSERACT_AVAILABLE = False
    pytesseract = None  # type: ignore

try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False
    fitz = None  # type: ignore

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    Image = None  # type: ignore


def ocr_page(page, dpi: int = 200) -> str:
    """
    Render a single PDF page to an image and run OCR on it.
    """
    if not PYMUPDF_AVAILABLE:
        raise RuntimeError("PyMuPDF (fitz) is not available. Please install it: pip install PyMuPDF")
    if not PIL_AVAILABLE:
        raise RuntimeError("Pillow (PIL) is not available. Please install it: pip install Pillow")
    if not PYTESSERACT_AVAILABLE:
        raise RuntimeError("pytesseract is not available. Please install it: pip install pytesseract")
    
    # PyMuPDF uses a matrix to control resolution; 72 dpi is 1.0
    zoom = dpi / 72.0
    mat = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat, alpha=False)

    image = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    try:
        text = pytesseract.image_to_string(image)
    except pytesseract.TesseractNotFoundError:  # type: ignore
        raise RuntimeError(
            "Tesseract OCR is not installed or not found in PATH. "
            "Please install Tesseract OCR on your system. "
            "On Linux: sudo apt-get install tesseract-ocr"
        )
    except Exception as e:
        raise RuntimeError(f"OCR failed: {e}")
    return text


def extract_text_from_pdf(input_path: Path) -> str:
    """
    Extract text directly from PDF (if it has text layers).
    This works without OCR and is much faster.
    """
    if not PYMUPDF_AVAILABLE:
        raise RuntimeError("PyMuPDF (fitz) is not available. Please install it: pip install PyMuPDF")
    
    doc = fitz.open(input_path)
    texts = []
    
    try:
        for page_index in range(len(doc)):
            page = doc.load_page(page_index)
            # Try to extract text directly (works for PDFs with text layers)
            page_text = page.get_text()
            if page_text.strip():  # If we got text, use it
                header = f"\n\n===== PAGE {page_index + 1} =====\n\n"
                texts.append(header + page_text)
    finally:
        doc.close()
    
    return "".join(texts)


def ocr_pdf(input_path: Path, dpi: int = 300, fallback_to_direct_extraction: bool = True) -> str:
    """
    Run OCR over all pages in a PDF and return the concatenated text.
    Enhanced version with better text extraction and OCR quality.
    If OCR is not available and fallback_to_direct_extraction is True,
    tries to extract text directly from PDF (works for PDFs with text layers).
    """
    if not PYMUPDF_AVAILABLE:
        raise RuntimeError("PyMuPDF (fitz) is not available. Please install it: pip install PyMuPDF")
    
    # If OCR dependencies are not available, try direct text extraction
    if not (PYTESSERACT_AVAILABLE and PIL_AVAILABLE):
        if fallback_to_direct_extraction:
            return extract_text_from_pdf(input_path)
        else:
            raise RuntimeError(
                "OCR dependencies not available. Install pytesseract and Pillow, "
                "or use fallback_to_direct_extraction=True to extract text directly from PDF."
            )
    
    doc = fitz.open(input_path)
    texts = []

    try:
        for page_index in range(len(doc)):
            page = doc.load_page(page_index)
            # Try direct text extraction first (faster, works for text-based PDFs)
            direct_text = page.get_text()
            
            # Also try text extraction with layout preservation
            direct_text_layout = page.get_text("text")
            
            # Use the longer/more complete text
            if len(direct_text_layout) > len(direct_text):
                direct_text = direct_text_layout
            
            if direct_text.strip() and len(direct_text.strip()) > 50:
                # PDF has text layer, use it directly
                # Clean up the text
                direct_text = re.sub(r'\s+', ' ', direct_text)  # Normalize whitespace
                texts.append(direct_text + "\n")
            else:
                # No text layer or insufficient text, use OCR
                # Try higher DPI for better accuracy
                page_text = ocr_page(page, dpi=max(dpi, 300))
                if page_text.strip():
                    # Clean OCR output
                    page_text = re.sub(r'\s+', ' ', page_text)  # Normalize whitespace
                    texts.append(page_text + "\n")
    finally:
        doc.close()
    
    # Combine all pages and clean up
    full_text = " ".join(texts)
    # Remove excessive newlines and spaces
    full_text = re.sub(r'\n\s*\n', '\n', full_text)
    full_text = re.sub(r' {2,}', ' ', full_text)
    
    return full_text


def main():
    parser = argparse.ArgumentParser(
        description="Simple OCR utility: extract text from a PDF using Tesseract."
    )
    parser.add_argument(
        "pdf_path",
        type=str,
        help="Path to the input PDF file.",
    )
    parser.add_argument(
        "--dpi",
        type=int,
        default=200,
        help="Rendering DPI for OCR (higher = slower, but more accurate). Default: 200.",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="",
        help="Optional path to save OCR text. If omitted, prints to stdout.",
    )

    args = parser.parse_args()

    pdf_path = Path(args.pdf_path)
    if not pdf_path.is_file():
        raise SystemExit(f"PDF not found: {pdf_path}")

    text = ocr_pdf(pdf_path, dpi=args.dpi)

    if args.output:
        out_path = Path(args.output)
        out_path.write_text(text, encoding="utf-8")
        print(f"OCR text saved to: {out_path}")
    else:
        # Print to console
        print(text)


if __name__ == "__main__":
    main()




