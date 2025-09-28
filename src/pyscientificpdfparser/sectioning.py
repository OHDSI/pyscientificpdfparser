# src/pyscientificpdfparser/sectioning.py
"""
Segments the document into logical sections (e.g., IMRaD).

Responsibilities:
- Group document elements under section headers.
- Identify standard scientific sections (Abstract, Introduction, Methods, etc.).
- Handle variations in section naming.
"""

from __future__ import annotations

import re

from .dla import LayoutElement
from .models import Section, TextBlock


def is_section_header(text: str) -> bool:
    """
    Determines if a text block is likely a section header using regex.
    This is a rule-based approach.
    """
    # Regex to match patterns like "1. Introduction", "II. METHODS", "Abstract"
    # It looks for optional numbering (digits, roman numerals, dots) followed by
    # a keyword.
    header_pattern = re.compile(
        r"^\s*([IVXLCDM\d\.]*)\s*"  # Lenient numbering check
        r"(Abstract|Introduction|Background|Methods|Methodology|"
        r"Materials and Methods|Results|Discussion|Conclusion|Acknowledgments|"
        r"References)\s*$",
        re.IGNORECASE,
    )
    return bool(header_pattern.match(text.strip()))


def segment_into_sections(elements: list[LayoutElement]) -> list[Section]:
    """
    Segments a flat list of layout elements into logical sections.

    Args:
        elements: A sorted list of LayoutElement objects from a document.

    Returns:
        A list of Section objects.
    """
    if not elements:
        return []

    sections = []
    # Start with a default "Header" section for title, authors, etc.
    current_section = Section(title="Header", elements=[])

    for element in elements:
        # Check if a TextBlock looks like a new section header
        if isinstance(element, TextBlock) and is_section_header(element.text):
            # If the current section has elements, save it.
            # Avoid saving an empty "Header" section if the first element is a header.
            if current_section.elements:
                sections.append(current_section)
            # Start a new section
            current_section = Section(title=element.text.strip(), elements=[element])
        else:
            # Add the element to the current section
            current_section.elements.append(element)

    # Append the last processed section
    if current_section.elements:
        sections.append(current_section)

    # If only the default "Header" section exists, rename it to "Content"
    if len(sections) == 1 and sections[0].title == "Header":
        sections[0].title = "Content"

    return sections
