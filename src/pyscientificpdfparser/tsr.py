# src/pyscientificpdfparser/tsr.py
"""
Performs Table Structure Recognition (TSR) on table regions.

Responsibilities:
- Use a specialized model (e.g., Table Transformer) to understand table structure.
- Identify rows, columns, headers, and spanning cells.
- Extract cell content and map it to the recognized structure.
"""

from __future__ import annotations

import torch
from PIL import Image
from transformers import AutoModelForObjectDetection, AutoProcessor

from .models import Table, TableCell, TextBlock


class TableRecognizer:
    """
    Recognizes the structure of a table from its image using a Table Transformer model.
    """

    def __init__(
        self,
        model_name: str = "microsoft/table-transformer-structure-recognition-v1.1-all",  # noqa: E501
    ):
        """Initializes the TableRecognizer."""
        try:
            self.processor = AutoProcessor.from_pretrained(model_name, apply_ocr=False)
            self.model = AutoModelForObjectDetection.from_pretrained(model_name)
            self.model.eval()
        except OSError:
            print(f"Could not load model '{model_name}'. Skipping TSR.")
            self.processor = None
            self.model = None

    def recognize_table(
        self,
        table_image: Image.Image,
        table_element: Table,
        ocr_blocks: list[TextBlock],
    ) -> Table:
        """
        Recognizes the structure of a single table and populates the Table object.

        Args:
            table_image: A PIL Image of the cropped table.
            table_element: The Table object from DLA, containing the bbox.
            ocr_blocks: A list of all OCR TextBlocks on the page.

        Returns:
            The populated Table object with structured rows and cells.
        """
        if not self.model or not self.processor:
            return table_element  # Return the original element if model failed

        width, height = table_image.size
        inputs = self.processor(images=table_image, return_tensors="pt")

        with torch.no_grad():
            self.model(**inputs)

        # The logic to convert model outputs (boxes and labels) to a structured
        # grid of cells is highly complex. It involves:
        # 1. Filtering boxes for rows, columns, headers, spanning cells.
        # 2. Calculating the intersections of row and column boxes to define cell geometry.
        # 3. Handling spanning cells by merging grid locations.
        # 4. Associating OCR text with each final cell.
        #
        # This is a significant engineering task. For this implementation, we
        # will create a placeholder logic that extracts all text within the
        # table's bounding box and places it into a single cell, acknowledging
        # that the full structure recognition is not yet implemented.

        print(
            "Full Table Structure Recognition is complex and not fully "
            "implemented. Using placeholder logic."
        )

        # Placeholder logic:
        # Get all text from OCR blocks that are inside the table's main bounding box.
        table_bbox = table_element.bbox
        contained_texts = []
        for ocr_block in ocr_blocks:
            ocr_center_x = (ocr_block.bbox[0] + ocr_block.bbox[2]) / 2
            ocr_center_y = (ocr_block.bbox[1] + ocr_block.bbox[3]) / 2
            if (
                table_bbox[0] <= ocr_center_x <= table_bbox[2]
                and table_bbox[1] <= ocr_center_y <= table_bbox[3]
            ):
                contained_texts.append(ocr_block.text)

        # Create a single cell with all the extracted text.
        if contained_texts:
            full_text = " ".join(contained_texts)
            cell = TableCell(
                text=full_text,
                bbox=table_bbox,
                row_span=1,
                col_span=1,
                is_header=False,
            )
            table_element.rows = [[cell]]
        else:
            table_element.rows = []

        return table_element
