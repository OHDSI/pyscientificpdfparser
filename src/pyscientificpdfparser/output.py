# src/pyscientificpdfparser/output.py
"""
Generates the final output files from the structured document model.

Responsibilities:
- Convert the Document object into a GitHub Flavored Markdown file.
- Generate GFM tables for structured table data.
- Save extracted figures to an assets directory and link them in the Markdown.
- Provide a structured JSON output of the Document model.
"""

from __future__ import annotations

import pathlib

from PIL import Image
from py_markdown_table.markdown_table import markdown_table

from .models import Document, Figure, Table, TextBlock
from .sectioning import is_section_header


def write_outputs(
    document: Document,
    output_dir: pathlib.Path,
    page_images: list[Image.Image],
    filename: str | None = None,
) -> None:
    """
    Writes all output files (JSON, Markdown, assets) to the specified directory.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    # Use the PDF name (without extension) if provided, otherwise fallback to
    # folder name
    if filename is None:
        filename = output_dir.name

    # Write JSON output
    json_path = output_dir / f"{filename}.json"
    with open(json_path, "w", encoding="utf-8") as f:
        f.write(document.model_dump_json(indent=2))

    # Write Markdown output
    md_path = output_dir / f"{filename}.md"
    assets_dir = output_dir / "assets"
    assets_dir.mkdir(exist_ok=True)

    md_content = _generate_markdown(document, assets_dir, page_images)
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_content)


def _generate_markdown(
    document: Document, assets_dir: pathlib.Path, page_images: list[Image.Image]
) -> str:
    """Generates the full Markdown string from a Document object."""
    md_lines = []

    # Add a title
    md_lines.append(f"# Parsed Document: {document.source_pdf}\n")

    for section in document.sections:
        # Use a level 2 heading for sections
        md_lines.append(f"## {section.title}\n")

        for i, element in enumerate(section.elements):
            if isinstance(element, TextBlock):
                # Don't repeat the section header text itself
                if i == 0 and is_section_header(element.text):
                    continue
                md_lines.append(element.text + "\n")

            elif isinstance(element, Table):
                # Placeholder logic creates a simple 1x1 table
                if element.rows and element.rows[0]:
                    cell_text = element.rows[0][0].text.replace("\n", " ")
                    table_data = [{"Content": cell_text}]
                    md_table = markdown_table(table_data).get_markdown()
                    md_lines.append(md_table + "\n")

            elif isinstance(element, Figure):
                # Crop the figure from the original page image
                page_img = page_images[element.page_number - 1]
                # The bounding box needs to be a tuple of integers for cropping
                bbox_int: tuple[int, int, int, int] = (
                    int(element.bbox[0]),
                    int(element.bbox[1]),
                    int(element.bbox[2]),
                    int(element.bbox[3]),
                )
                figure_img = page_img.crop(bbox_int)

                # Save the figure image
                figure_filename = f"figure_{element.page_number}_{i}.png"
                figure_path = assets_dir / figure_filename
                figure_img.save(figure_path)

                # Add the markdown link
                caption = element.caption or f"Figure {i+1}"
                md_lines.append(f"![{caption}](assets/{figure_filename})\n")

    return "\n".join(md_lines)
