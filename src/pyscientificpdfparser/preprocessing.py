# src/pyscientificpdfparser/preprocessing.py
"""
Handles PDF input, page rendering, and image preprocessing.

Responsibilities:
- Accept various input types (single file, directory).
- Render PDF pages to images for OCR and DLA.
- Perform image enhancement (deskewing, denoising) to improve OCR quality.
"""
from __future__ import annotations

import pathlib

import cv2
import fitz  # PyMuPDF
import numpy as np
from PIL import Image
from pydantic import BaseModel, ConfigDict


class PreprocessedPage(BaseModel):
    """
    Holds the preprocessed data for a single page.
    """

    page_number: int
    image: Image.Image
    is_scanned: bool

    model_config = ConfigDict(arbitrary_types_allowed=True)


def _preprocess_image(image: Image.Image) -> Image.Image:
    """
    Applies preprocessing steps to an image to enhance it for OCR.

    Args:
        image: A Pillow Image object.

    Returns:
        A preprocessed Pillow Image object.
    """
    # Convert Pillow Image to OpenCV format (numpy array)
    cv_image = np.array(image.convert("RGB"))
    cv_image = cv_image[:, :, ::-1].copy()  # Convert RGB to BGR

    # 1. Convert to grayscale
    gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)

    # 2. Apply adaptive thresholding for binarization
    # This is often better than a simple global threshold for varying lighting
    binary = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
    )

    # (Optional placeholder for future enhancements)
    # 3. Denoising
    # denoised = cv2.medianBlur(binary, 3)

    # (Optional placeholder for future enhancements)
    # 4. Deskewing
    # deskewed = deskew(denoised)

    # Convert back to Pillow Image from the processed OpenCV image
    return Image.fromarray(binary)


def render_pdf_to_images(
    pdf_path: pathlib.Path, dpi: int = 300
) -> list[PreprocessedPage]:
    """
    Renders a PDF document to a list of preprocessed images, one per page.

    Args:
        pdf_path: The path to the PDF file.
        dpi: The resolution (dots per inch) to use for rendering.

    Returns:
        A list of PreprocessedPage objects.
    """
    preprocessed_pages = []
    zoom = dpi / 72  # PyMuPDF uses 72 DPI as the base
    mat = fitz.Matrix(zoom, zoom)

    with fitz.open(str(pdf_path)) as doc:
        for page_num, page in enumerate(doc):
            # R1.2: Detect if a page is image-based (scanned)
            # Heuristic: if a page has no extractable text, it's likely scanned.
            if not page.get_text("text").strip():
                is_scanned = True
            else:
                is_scanned = False

            # Render page to a pixmap
            pix = page.get_pixmap(matrix=mat)
            image = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)

            # R1.3: Apply preprocessing if the page is scanned
            if is_scanned:
                processed_image = _preprocess_image(image)
            else:
                # Even for digital PDFs, converting to grayscale can be beneficial
                # for some layout analysis models.
                processed_image = image.convert("L")

            preprocessed_pages.append(
                PreprocessedPage(
                    page_number=page_num + 1,
                    image=processed_image,
                    is_scanned=is_scanned,
                )
            )

    return preprocessed_pages
