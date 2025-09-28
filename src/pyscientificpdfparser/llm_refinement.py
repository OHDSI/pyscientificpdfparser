# src/pyscientificpdfparser/llm_refinement.py
"""
Provides optional, LLM-powered refinement and extraction capabilities.

Responsibilities:
- Correct OCR errors in context.
- Refine text flow and section segmentation.
- Parse unstructured reference sections into structured data.
- Extract specific entities (e.g., datasets, funding sources).
- Use structured output techniques (e.g., instructor) for reliability.
"""

from __future__ import annotations

import logging
from typing import Any

from langchain_openai import AzureChatOpenAI

from . import models

logger = logging.getLogger(__name__)


def _get_llm_client() -> AzureChatOpenAI | None:
    """
    Create an Azure LLM client.
    """
    azure_endpoint = "https://ai-proxy.lab.epam.com"
    azure_model = "gpt-4o-mini-2024-07-18"
    azure_api_version = "2024-02-01"

    try:
        llm_gem = AzureChatOpenAI(
            openai_api_version=azure_api_version,
            azure_endpoint=azure_endpoint,
            deployment_name=azure_model,
            temperature=0,
            max_tokens=None,
            max_retries=2,
        )
        return llm_gem
    except Exception as e:
        logger.error("Failed to initialize AzureChatOpenAI: %s", e)
        return None


def refine_document(document: models.Document) -> models.Document:
    logger.info("Using AzureChatOpenAI")
    """
    Refine a parsed Document using an LLM.
    """
    client = _get_llm_client()
    if not client:
        logger.warning("Skipping LLM refinement – no client available.")
        return document

    logger.info(
        "Starting LLM refinement for %s",
        getattr(document, "source_pdf", "Unknown PDF"),
    )

    document = _correct_ocr(document, client)
    document = _refine_sections(document, client)
    document = _parse_references(document, client)
    document = _extract_entities(document, client)

    return document


# -------------------------
# LLM refinement functions
# -------------------------


def _call_llm(client: Any, prompt: str) -> str:
    """
    Send text to LLM and return response.
    """
    logger.debug(f"Sending prompt to LLM (first 200 chars): {prompt[:200]}...")
    response = client.predict_messages([{"role": "user", "content": prompt}])
    content = getattr(response, "content", str(response))
    logger.debug(f"LLM response (first 200 chars): {content[:200]}...")
    return content


def _correct_ocr(document: models.Document, client: Any) -> models.Document:
    if hasattr(document, "sections") and document.sections:
        for section in document.sections:
            if hasattr(section, "text") and section.text:
                section.text = _call_llm(
                    client, f"Correct OCR errors:\n\n{section.text}"
                )
        document.llm_processing_log.append("OCR correction applied.")
    elif hasattr(document, "pages") and document.pages:
        for i, page_text in enumerate(document.pages):
            document.pages[i] = _call_llm(
                client,
                f"Correct OCR errors in the following text:\n\n{page_text}",
            )
        document.llm_processing_log.append("OCR correction applied.")
    else:
        logger.warning("No text found in document for OCR correction.")
    return document


def _refine_sections(document: models.Document, client: Any) -> models.Document:
    """
    Refine sections for better structure and flow.
    """
    if hasattr(document, "sections") and document.sections:
        for section in document.sections:
            if hasattr(section, "text") and section.text:
                section.text = _call_llm(
                    client,
                    (
                        "Refine this section text for clarity and "
                        f"structure:\n\n{section.text}"
                    ),
                )
        document.llm_processing_log.append("Sections refined by LLM.")
    return document


def _parse_references(document: models.Document, client: Any) -> models.Document:
    """
    Parse references into structured format.
    """
    refs = getattr(document, "references", [])
    if refs:
        refs_text = "\n".join(refs)
        structured_refs = _call_llm(
            client,
            f"Parse the following references into structured data "
            f"(title, authors, journal, year):\n\n{refs_text}",
        )
        document.structured_references = structured_refs
        document.llm_processing_log.append("Parsed references using LLM.")
    return document


def _extract_entities(document: models.Document, client: Any) -> models.Document:
    """
    Extract entities like datasets, compounds, funding sources.
    """
    text = ""
    if hasattr(document, "sections") and document.sections:
        # Access attribute, not dictionary key
        text = "\n".join(
            [s.text for s in document.sections if hasattr(s, "text") and s.text]
        )
    elif hasattr(document, "pages") and document.pages:
        text = "\n".join(document.pages)

    if text:
        entities = _call_llm(
            client,
            f"Extract key entities (datasets, compounds, funding sources) "
            f"from this text:\n\n{text}",
        )
        document.extracted_entities = entities
        document.llm_processing_log.append("Extracted entities using LLM.")
    return document
