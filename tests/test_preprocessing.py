# tests/test_preprocessing.py
import pathlib
from typing import Any
from unittest import mock

from PIL import Image

from pyscientificpdfparser.preprocessing import render_pdf_to_images


class MockPixmap:
    """A mock class for the fitz.Pixmap object."""

    def __init__(self, width: int = 10, height: int = 10) -> None:
        self.width = width
        self.height = height
        # Create a simple black image sample
        self.samples = bytes(width * height * 3)


class MockPage:
    """A mock class for the fitz.Page object."""

    def __init__(self, has_text: bool = True) -> None:
        self._has_text = has_text

    def get_text(self, format: str = "text") -> str:
        return "some text" if self._has_text else ""

    def get_pixmap(self, matrix: Any = None) -> MockPixmap:
        return MockPixmap()


@mock.patch("fitz.open")
def test_render_pdf_to_images(mock_fitz_open: mock.MagicMock) -> None:
    """
    Tests the render_pdf_to_images function with a mock PDF.

    Verifies that:
    - It correctly identifies digital vs. scanned pages.
    - It returns the correct number of pages.
    - The returned images have the expected properties.
    """
    # Arrange: Configure the mock to simulate a 2-page document
    mock_doc = mock.MagicMock()
    mock_doc.__enter__.return_value = [
        MockPage(has_text=True),  # Page 1: Digital
        MockPage(has_text=False),  # Page 2: Scanned
    ]
    mock_fitz_open.return_value = mock_doc

    # Act: Call the function with a dummy path
    dummy_path = pathlib.Path("test.pdf")
    preprocessed_pages = render_pdf_to_images(dummy_path, dpi=72)

    # Assert: Check the results
    # 1. Correct number of pages returned
    assert len(preprocessed_pages) == 2

    # 2. Check Page 1 (Digital)
    page1 = preprocessed_pages[0]
    assert page1.page_number == 1
    assert not page1.is_scanned
    assert isinstance(page1.image, Image.Image)
    assert page1.image.mode == "L"  # Should be converted to grayscale
    assert page1.image.size == (10, 10)

    # 3. Check Page 2 (Scanned)
    page2 = preprocessed_pages[1]
    assert page2.page_number == 2
    assert page2.is_scanned
    assert isinstance(page2.image, Image.Image)
    assert page2.image.mode == "L"  # Binarization results in a grayscale mode image
    assert page2.image.size == (10, 10)

    # 4. Verify that fitz.open was called correctly
    mock_fitz_open.assert_called_once_with(str(dummy_path))
