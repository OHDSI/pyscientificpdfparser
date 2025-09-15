# src/pyscientificpdfparser/ocr.py
"""
Performs Optical Character Recognition (OCR) on page images.

Responsibilities:
- Use Tesseract to extract text, bounding boxes, and confidence scores.
- Provide configuration options for Tesseract (e.g., language, PSM).
- Output OCR data in a structured format (e.g., mapping to internal models).
"""
from __future__ import annotations

import platform
from collections import defaultdict
from typing import TypedDict

import pytesseract

from .models import BoundingBox, TextBlock
from .preprocessing import PreprocessedPage


# R2.4: Add OS-specific path for Tesseract on Windows
if platform.system() == "Windows":
    # Default path for Tesseract installed via Chocolatey on GitHub Actions
    pytesseract.pytesseract.tesseract_cmd = (
        r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    )


class OcrBlock(TypedDict):
    text: list[str]
    conf: list[int]
    left: list[int]
    top: list[int]
    width: list[int]
    height: list[int]


def extract_text_from_page(
    page: PreprocessedPage, lang: str = "eng", config: str = ""
) -> list[TextBlock]:
    """
    Extracts text and layout information from a single preprocessed page image.

    Args:
        page: A PreprocessedPage object containing the image to process.
        lang: The language for Tesseract to use.
        config: Additional configuration options for Tesseract (e.g., "--psm 6").

    Returns:
        A list of TextBlock objects found on the page.
    """
    try:
        # R2.3: Use image_to_data to get detailed information
        ocr_data = pytesseract.image_to_data(
            page.image, lang=lang, config=config, output_type=pytesseract.Output.DICT
        )
    except pytesseract.TesseractNotFoundError:
        print("Tesseract is not installed or not in your PATH.")
        # Depending on desired behavior, could raise an exception or return empty
        return []

    return _process_ocr_data(ocr_data, page.page_number)


def _process_ocr_data(
    ocr_data: dict[str, list[str | int]], page_number: int
) -> list[TextBlock]:
    """
    Processes the raw dictionary output from Tesseract into TextBlock objects.

    Groups words into blocks based on their 'block_num'.
    """
    blocks: defaultdict[int, OcrBlock] = defaultdict(
        lambda: {
            "text": [],
            "conf": [],
            "left": [],
            "top": [],
            "width": [],
            "height": [],
        }
    )

    # Group data by block number
    num_items = len(ocr_data["level"])
    for i in range(num_items):
        # Skip items with no text or very low confidence (often noise)
        if not str(ocr_data["text"][i]).strip() or int(str(ocr_data["conf"][i])) < 0:
            continue

        block_num = int(str(ocr_data["block_num"][i]))
        blocks[block_num]["text"].append(str(ocr_data["text"][i]))
        blocks[block_num]["conf"].append(int(str(ocr_data["conf"][i])))
        blocks[block_num]["left"].append(int(str(ocr_data["left"][i])))
        blocks[block_num]["top"].append(int(str(ocr_data["top"][i])))
        blocks[block_num]["width"].append(int(str(ocr_data["width"][i])))
        blocks[block_num]["height"].append(int(str(ocr_data["height"][i])))

    # Create TextBlock objects from the grouped data
    text_blocks = []
    for block_num, data in blocks.items():
        if not data["text"]:
            continue

        # Calculate bounding box for the entire block
        min_left = min(data["left"])
        min_top = min(data["top"])
        max_right = max(left + w for left, w in zip(data["left"], data["width"]))
        max_bottom = max(t + h for t, h in zip(data["top"], data["height"]))
        bbox: BoundingBox = (min_left, min_top, max_right, max_bottom)

        # Calculate average confidence
        avg_conf = sum(data["conf"]) / len(data["conf"]) if data["conf"] else 0.0

        text_blocks.append(
            TextBlock(
                text=" ".join(data["text"]),
                bbox=bbox,
                page_number=page_number,
                confidence=avg_conf,
            )
        )

    return text_blocks
