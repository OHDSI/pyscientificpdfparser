# pyScientificPdfParser

A Python package to parse scientific PDF documents into structured Markdown, leveraging modern Document AI models.

## Overview

This package provides a pipeline to process scientific PDFs (both born-digital and scanned) and convert them into structured, machine-readable formats like GitHub Flavored Markdown and JSON. It uses a series of state-of-the-art models for layout analysis, table recognition, and optional LLM-based refinement.

## Features

- **PDF Processing:** Handles single files, lists of files, or entire directories.
- **OCR:** Uses Tesseract for robust text extraction from scanned documents.
- **Document Layout Analysis (DLA):** Employs models like LayoutLMv3 or DiT to identify page regions (title, text, tables, figures).
- **Table Structure Recognition (TSR):** Utilizes models like Table Transformer to parse the structure of complex tables.
- **Section Segmentation:** Logically groups content into IMRaD sections.
- **LLM Refinement (Optional):** Uses Large Language Models for OCR correction, text flow normalization, and structured data extraction (e.g., references).
- **Multiple Output Formats:** Generates clean Markdown, structured JSON, and extracts image assets.

## Installation

Install the package from PyPI:

```bash
# Base installation
pip install pyscientificpdfparser

# To include machine learning models for layout analysis and table recognition
pip install pyscientificpdfparser[ml]

# For full functionality, including LLM-based refinement
pip install pyscientificpdfparser[ml,llm]
```

**Note:** This package requires a system-level installation of Tesseract for OCR. Please see the [full installation guide](HOW_TO.md) for details.

## Usage

### Command-Line Interface (CLI)

```bash
scipdfparser process path/to/your/document.pdf --output-dir ./output
```

### Python API

```python
import pathlib
from pyscientificpdfparser.core import parse_pdf

# Define the path to your PDF and the desired output directory
pdf_path = pathlib.Path("path/to/your/document.pdf")
output_dir = pathlib.Path("path/to/output")

# Create the output directory if it doesn't exist
output_dir.mkdir(parents=True, exist_ok=True)

print(f"Processing {pdf_path.name}...")

# Call the parser
# The 'document' object contains all the parsed data.
document = parse_pdf(
    pdf_path=pdf_path,
    output_dir=output_dir,
    llm_refine=False,  # Optional: set to True to enable LLM refinement
)

print("Done.")
print(f"Markdown and assets saved to: {output_dir}")
```

## Development

This project uses `poetry` for dependency management and `pre-commit` for code quality.
Initially developed https://github.com/gowthamrao/pyScientificPdfParser/tree/develop

```bash
# Install development dependencies
poetry install

# Activate pre-commit hooks
poetry run pre-commit install
```
