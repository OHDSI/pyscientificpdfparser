# src/pyscientificpdfparser/dla.py
"""
Performs Document Layout Analysis (DLA) using a deep learning model.

Responsibilities:
- Use a SOTA model (e.g., LayoutLMv3, DiT) to identify page regions.
- Classify regions into types (Title, Text, Table, Figure, etc.).
- Determine the logical reading order of the identified regions.
"""
from __future__ import annotations

from typing import Union

import torch
from PIL import Image
from transformers import (
    AutoModelForObjectDetection,
    AutoProcessor,
)

from .models import Figure, Table, TextBlock

# A Union of all possible layout elements that DLA can produce
LayoutElement = Union[TextBlock, Table, Figure]


class LayoutAnalyzer:
    """
    A class to analyze the layout of a document page using a LayoutLMv3 model.
    """

    def __init__(
        self, model_name: str = "HYPJUDY/layoutlmv3-base-finetuned-publaynet"
    ):
        """
        Initializes the LayoutAnalyzer by loading the model and processor.
        """
        try:
            self.processor = AutoProcessor.from_pretrained(model_name)
            self.model = (
                AutoModelForObjectDetection.from_pretrained(model_name)
            )
            self.model.eval()  # Set model to evaluation mode
        except Exception as e:
            print(f"CRITICAL: Failed to load LayoutAnalyzer model '{model_name}'.")
            print(f"CRITICAL: Error details: {e}")
            print(
                "CRITICAL: Document Layout Analysis will be skipped. "
                "This may be due to a missing internet connection, "
                "a problem with the Tesseract installation, or other "
                "dependency issues."
            )
            # Handle model loading failure gracefully
            self.processor = None
            self.model = None

    def analyze_page(
        self, image: Image.Image, page_number: int, ocr_blocks: list[TextBlock]
    ) -> list[LayoutElement]:
        """
        Analyzes a single page image to identify and structure layout elements.

        Args:
            image: The PIL Image of the page.
            page_number: The page number.
            ocr_blocks: A list of TextBlock objects from the OCR step.

        Returns:
            A sorted list of LayoutElement objects found on the page.
        """
        if not self.model or not self.processor:
            print("LayoutAnalyzer not initialized. Skipping DLA.")
            return ocr_blocks  # type: ignore

        # 1. Prepare image for the model
        inputs = self.processor(images=image, return_tensors="pt")

        # 2. Perform inference
        with torch.no_grad():
            outputs = self.model(**inputs)

        # 3. Post-process the predictions
        width, height = image.size
        predictions = outputs["logits"].argmax(-1).squeeze().tolist()
        boxes = outputs["pred_boxes"].squeeze().tolist()

        # Denormalize bounding boxes
        def denormalize_box(
            box: list[float], w: int, h: int
        ) -> tuple[float, float, float, float]:
            return (box[0] * w, box[1] * h, box[2] * w, box[3] * h)

        denormalized_boxes = [
            denormalize_box(box, width, height) for box in boxes
        ]

        # 4. Create initial layout elements from predictions
        # The model's config contains the mapping from id to label
        id2label = self.model.config.id2label
        raw_elements: list[LayoutElement] = []
        for label_id, bbox in zip(predictions, denormalized_boxes):
            label = id2label.get(label_id, "unknown")
            # For now, we only care about a few key types
            if label == "text":
                # TextBlocks will be populated by associating OCR blocks
                raw_elements.append(
                    TextBlock(text="", bbox=bbox, page_number=page_number, confidence=None)
                )  # noqa: E501
            elif label == "table":
                raw_elements.append(Table(bbox=bbox, page_number=page_number, rows=[]))
            elif label == "figure":
                # Placeholder, figure extraction happens later
                raw_elements.append(
                    Figure(bbox=bbox, page_number=page_number, image_path="")
                )
            # Other labels like 'title', 'list', etc., are ignored for now but can be added.

        # 5. Associate OCR text with the DLA text blocks
        layout_elements = self._associate_ocr_to_layout(raw_elements, ocr_blocks)

        # 6. Sort elements by reading order
        sorted_elements = self._sort_elements_by_reading_order(layout_elements)

        return sorted_elements

    def _associate_ocr_to_layout(
        self, layout_elements: list[LayoutElement], ocr_blocks: list[TextBlock]
    ) -> list[LayoutElement]:
        """
        Assigns text from OCR blocks to the containing DLA-identified layout elements.
        """
        # This is a simple association based on containment. More complex logic
        # could handle overlapping regions.
        for element in layout_elements:
            if isinstance(element, TextBlock):
                contained_texts = []
                for ocr_block in ocr_blocks:
                    # Check if the center of the OCR block is inside the DLA element
                    ocr_center_x = (ocr_block.bbox[0] + ocr_block.bbox[2]) / 2
                    ocr_center_y = (ocr_block.bbox[1] + ocr_block.bbox[3]) / 2
                    if (
                        element.bbox[0] <= ocr_center_x <= element.bbox[2]
                        and element.bbox[1]
                        <= ocr_center_y
                        <= element.bbox[3]
                    ):
                        contained_texts.append(ocr_block.text)

                element.text = " ".join(contained_texts)

        # Filter out text blocks that didn't get any text assigned
        # and keep non-text blocks (tables, figures)
        final_elements = [
            elem
            for elem in layout_elements
            if (isinstance(elem, TextBlock) and elem.text.strip())
            or not isinstance(elem, TextBlock)
        ]
        return final_elements

    def _sort_elements_by_reading_order(
        self, elements: list[LayoutElement]
    ) -> list[LayoutElement]:
        """
        Sorts elements in a top-to-bottom, left-to-right reading order.
        This is a simple heuristic and may not work for complex multi-column layouts.
        """
        # Sort primarily by top coordinate, then by left coordinate
        return sorted(elements, key=lambda e: (e.bbox[1], e.bbox[0]))
