# src/pyscientificpdfparser/core.py
"""
Core pipeline orchestration for the pyScientificPdfParser.

This module contains the main function(s) that connect the different stages
of the parsing pipeline, from input processing to final output generation.
"""
from __future__ import annotations

import pathlib

from . import models, ocr, output, preprocessing, sectioning, tsr
from .dla import LayoutAnalyzer

# Instantiate the ML model analyzers once at the module level.
# This is a form of singleton pattern to avoid reloading the heavy models
# on every function call.
print("Initializing Layout and Table models...")
layout_analyzer = LayoutAnalyzer()
table_recognizer = tsr.TableRecognizer()
print("Models initialized.")


def parse_pdf(
    pdf_path: pathlib.Path,
    output_dir: pathlib.Path | None = None,
    llm_refine: bool = False,
) -> models.Document:
    """
    Parses a single scientific PDF document and returns a structured Document object.

    This function orchestrates the entire pipeline.
    """
    print(f"1. Preprocessing: Rendering PDF pages for {pdf_path.name}...")
    preprocessed_pages = preprocessing.render_pdf_to_images(pdf_path)
    print(f"DEBUG: Number of preprocessed pages: {len(preprocessed_pages)}")

    all_elements = []
    page_images = [p.image for p in preprocessed_pages]

    for page in preprocessed_pages:
        print(f"  - Processing page {page.page_number}...")
        # 2. OCR
        ocr_blocks = ocr.extract_text_from_page(page)

        # 3. Document Layout Analysis
        # The DLA uses the original (not preprocessed for OCR) image
        original_image = page_images[page.page_number - 1]
        layout_elements = layout_analyzer.analyze_page(
            original_image, page.page_number, ocr_blocks
        )

        # 4. Table Structure Recognition
        processed_layout_elements = []
        for element in layout_elements:
            if isinstance(element, models.Table):
                table_image = original_image.crop(element.bbox)
                # Pass all OCR blocks from the page to the recognizer
                # so it can find the text within the table's bbox.
                element = table_recognizer.recognize_table(
                    table_image, element, ocr_blocks
                )
            processed_layout_elements.append(element)

        all_elements.extend(processed_layout_elements)

    print(f"DEBUG: Total elements before sectioning: {len(all_elements)}")
    # 5. Section Segmentation
    print("5. Segmenting document into logical sections...")
    sections = sectioning.segment_into_sections(all_elements)

    # 6. Construct final Document object
    document = models.Document(
        source_pdf=str(pdf_path),
        sections=sections,
    )

    if llm_refine:
        # Placeholder for future LLM refinement step
        print("Refining with LLM...")
        document.llm_processing_log.append("Refining with LLM...")
        from pyscientificpdfparser import llm_refinement

        document = llm_refinement.refine_document(document)

    # 7. Write output files
    if output_dir:
        print(f"6. Writing output files to {output_dir}...")
        # output.write_outputs(document, output_dir, page_images)
        # Use the PDF filename (without extension) for the markdown
        pdf_stem = pdf_path.stem
        output.write_outputs(document, output_dir, page_images, filename=pdf_stem)

    print("Parsing complete.")
    return document
