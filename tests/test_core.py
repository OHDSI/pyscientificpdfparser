# tests/test_core.py
from pathlib import Path
from unittest import mock

from PIL import Image

from pyscientificpdfparser import core
from pyscientificpdfparser.models import Document, Section, Table, TextBlock
from pyscientificpdfparser.preprocessing import PreprocessedPage


@mock.patch("pyscientificpdfparser.core.output")
@mock.patch("pyscientificpdfparser.core.sectioning")
@mock.patch("pyscientificpdfparser.core.table_recognizer")
@mock.patch("pyscientificpdfparser.core.layout_analyzer")
@mock.patch("pyscientificpdfparser.core.ocr")
@mock.patch("pyscientificpdfparser.core.preprocessing")
def test_parse_pdf_orchestration(
    mock_preprocessing: mock.MagicMock,
    mock_ocr: mock.MagicMock,
    mock_layout_analyzer: mock.MagicMock,
    mock_table_recognizer: mock.MagicMock,
    mock_sectioning: mock.MagicMock,
    mock_output: mock.MagicMock,
) -> None:
    """
    Tests that the main parse_pdf function calls all pipeline stages in order.
    """
    # --- Arrange ---
    # 1. Mock the return values for each stage of the pipeline
    mock_page_image = Image.new("RGB", (100, 100))
    mock_preprocessed_page = PreprocessedPage(
        page_number=1, image=mock_page_image, is_scanned=False
    )
    mock_preprocessing.render_pdf_to_images.return_value = [mock_preprocessed_page]

    mock_ocr_block = TextBlock(text="ocr text", bbox=(10, 10, 20, 20), page_number=1)
    mock_ocr.extract_text_from_page.return_value = [mock_ocr_block]

    # DLA returns a Table and a TextBlock
    mock_dla_table = Table(bbox=(30, 30, 80, 80), page_number=1, rows=[])
    mock_dla_text = TextBlock(text="dla text", bbox=(5, 5, 25, 25), page_number=1)
    mock_layout_analyzer.analyze_page.return_value = [mock_dla_table, mock_dla_text]

    # TSR returns the populated table
    mock_populated_table = Table(bbox=(30, 30, 80, 80), page_number=1, rows=[[]])
    mock_table_recognizer.recognize_table.return_value = mock_populated_table

    # Sectioning returns a single section
    mock_section = Section(title="Test Section", elements=[])
    mock_sectioning.segment_into_sections.return_value = [mock_section]

    dummy_pdf_path = Path("dummy.pdf")
    dummy_output_dir = Path("output")

    # --- Act ---
    document = core.parse_pdf(pdf_path=dummy_pdf_path, output_dir=dummy_output_dir)

    # --- Assert ---
    # 1. Verify that each pipeline stage was called once with expected args
    mock_preprocessing.render_pdf_to_images.assert_called_once_with(dummy_pdf_path)
    mock_ocr.extract_text_from_page.assert_called_once_with(mock_preprocessed_page)
    mock_layout_analyzer.analyze_page.assert_called_once_with(
        mock_page_image, 1, [mock_ocr_block]
    )
    mock_table_recognizer.recognize_table.assert_called_once_with(
        mock.ANY,  # The cropped image is hard to assert, so we check for any image
        mock_dla_table,
        [mock_ocr_block],
    )
    # The final elements passed to sectioning should be the populated table and
    # the text block
    mock_sectioning.segment_into_sections.assert_called_once_with(
        [mock_populated_table, mock_dla_text]
    )

    # 2. Verify the final Document object
    assert isinstance(document, Document)
    assert document.source_pdf == str(dummy_pdf_path)
    assert document.sections == [mock_section]

    # 3. Verify that the output function was called
    mock_output.write_outputs.assert_called_once_with(
        document, dummy_output_dir, [mock_page_image], filename="dummy"
    )


def test_parse_pdf_integration() -> None:
    """
    Tests the full PDF parsing pipeline on a real document.
    This is a slow-running integration test.
    """
    # --- Arrange ---
    # Get the path to the test PDF in the fixtures directory
    # We construct the path relative to this test file
    current_dir = Path(__file__).parent
    pdf_path = current_dir / "fixtures" / "arxiv-1410.6579.pdf"
    output_dir = current_dir / "test_output" / pdf_path.stem

    # --- Act ---
    # Run the actual parsing function without mocks
    print(f"DEBUG: PDF path: {pdf_path}")
    print(f"DEBUG: PDF path exists: {pdf_path.exists()}")
    document = core.parse_pdf(pdf_path=pdf_path, output_dir=output_dir)
    print(f"DEBUG: Returned document: {document}")

    # --- Assert ---
    # 1. Check the Document object
    assert isinstance(document, Document)
    assert document.source_pdf == str(pdf_path)
    assert len(document.sections) > 0, "The document should have at least one section."

    # 2. Check that some content was extracted
    first_section = document.sections[0]
    assert len(first_section.elements) > 0, "The first section should have elements."

    # 3. Check that output files were created
    assert output_dir.exists()
    # Check for the main markdown file
    markdown_file = output_dir / f"{pdf_path.stem}.md"
    assert markdown_file.exists()
    assert markdown_file.stat().st_size > 100  # Check it's not empty
