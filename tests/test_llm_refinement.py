# tests/test_llm_refinement.py

import logging
from typing import Any, Callable

import pytest

import pyscientificpdfparser.llm_refinement as llm_refinement
from pyscientificpdfparser import models


class DummyDocument(models.Document):
    """Minimal Document stub for testing."""

    def __init__(self, source_pdf: str = "dummy.pdf") -> None:
        super().__init__(source_pdf=source_pdf, sections=[])
        self.llm_processing_log = []


def test_refine_document_with_mocked_client(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    """Ensure refine_document runs with a mocked AzureChatOpenAI client."""

    class FakeClient:
        def __init__(self, **kwargs: Any) -> None:
            self.kwargs = kwargs

    monkeypatch.setattr(llm_refinement, "AzureChatOpenAI", FakeClient)

    doc = DummyDocument()

    with caplog.at_level(logging.INFO):
        result = llm_refinement.refine_document(doc)

    assert result is doc
    assert "Starting LLM refinement" in caplog.text
    assert "Using AzureChatOpenAI" in caplog.text


def test_refine_document_without_client(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    """If AzureChatOpenAI is None, refinement should be skipped."""
    monkeypatch.setattr(llm_refinement, "AzureChatOpenAI", None)

    doc = DummyDocument()
    with caplog.at_level(logging.WARNING):
        result = llm_refinement.refine_document(doc)

    assert result is doc
    assert "Skipping LLM refinement" in caplog.text


@pytest.mark.parametrize(  # type: ignore[misc]
    "func",
    [
        llm_refinement._correct_ocr,
        llm_refinement._refine_sections,
        llm_refinement._parse_references,
        llm_refinement._extract_entities,
    ],
)
def test_stub_functions_return_document(
    func: Callable[[models.Document, Any], models.Document],
) -> None:
    """All private stub functions should return the document unchanged."""
    doc = DummyDocument()
    client = object()
    result = func(doc, client)
    assert result is doc
