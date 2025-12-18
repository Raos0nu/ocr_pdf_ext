import argparse                     # AUTHOR (@raos0nu)(https://github.com/Raos0nu)
import os
from pathlib import Path

import pytesseract
# Set Tesseract path based on environment (Windows vs Linux/Vercel)
if os.name == "nt":  # Windows
    pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
# On Linux/Vercel, Tesseract should be in PATH, so we don't set it explicitly

import fitz  # PyMuPDF
from PIL import Image


def ocr_page(page, dpi: int = 200) -> str:
    """
    Render a single PDF page to an image and run OCR on it.
    """
    # PyMuPDF uses a matrix to control resolution; 72 dpi is 1.0
    zoom = dpi / 72.0
    mat = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat, alpha=False)

    image = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    text = pytesseract.image_to_string(image)
    return text


def ocr_pdf(input_path: Path, dpi: int = 200) -> str:
    """
    Run OCR over all pages in a PDF and return the concatenated text.
    """
    doc = fitz.open(input_path)
    texts = []

    for page_index in range(len(doc)):
        page = doc.load_page(page_index)
        page_text = ocr_page(page, dpi=dpi)
        header = f"\n\n===== PAGE {page_index + 1} =====\n\n"
        texts.append(header + page_text)

    doc.close()
    return "".join(texts)


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




