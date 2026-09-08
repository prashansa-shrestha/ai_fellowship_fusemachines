"""Focused tests for deterministic Phase 1 intake and classification."""

from __future__ import annotations

import io

import pytest
from openpyxl import Workbook

from trustilo.common.schemas import Question, SourceFormat
from trustilo.intake import classify, parse


def _xlsx_bytes(rows: list[list[str | None]]) -> bytes:
    workbook = Workbook()
    worksheet = workbook.active
    for row in rows:
        worksheet.append(row)
    output = io.BytesIO()
    workbook.save(output)
    workbook.close()
    return output.getvalue()


def test_text_parsing_normalizes_whitespace_and_is_deterministic() -> None:
    raw = b"  Do you require   MFA?  \n\nHow often are backups tested?\n"

    first = parse(raw, SourceFormat.TEXT, "tenant-a")
    second = parse(raw, "text", "tenant-a")

    assert [question.normalized_text for question in first] == [
        "Do you require MFA?",
        "How often are backups tested?",
    ]
    assert first[0].raw_text == "  Do you require   MFA?  "
    assert [question.question_id for question in first] == [question.question_id for question in second]
    assert first[0].questionnaire_id == second[0].questionnaire_id


def test_csv_preserves_physical_rows_and_sections() -> None:
    raw = (
        "Section,QUESTION TEXT,Notes\r\n"
        "Access Control,Do you require MFA?,required\r\n"
        ",,\r\n"
        'Resilience,"How often are\nbackups tested?",annual\r\n'
    ).encode()

    questions = parse(raw, SourceFormat.CSV, "tenant-a")

    assert [question.source_row_index for question in questions] == [2, 4]
    assert [question.section for question in questions] == ["Access Control", "Resilience"]
    assert questions[1].normalized_text == "How often are backups tested?"


def test_csv_rejects_nonblank_row_without_a_question() -> None:
    with pytest.raises(ValueError, match="row 2.*no question"):
        parse(b"Question,Section\n,Access\n", SourceFormat.CSV, "tenant-a")


def test_xlsx_preserves_worksheet_rows_and_sections() -> None:
    raw = _xlsx_bytes(
        [
            ["Section", "Question"],
            ["Access Control", "Do you require   MFA?"],
            [None, None],
            ["Resilience", "How often are backups tested?"],
        ]
    )

    questions = parse(raw, SourceFormat.XLSX, "tenant-a")

    assert [question.source_row_index for question in questions] == [2, 4]
    assert [question.section for question in questions] == ["Access Control", "Resilience"]
    assert questions[0].normalized_text == "Do you require MFA?"
    assert [q.question_id for q in questions] == [
        q.question_id for q in parse(raw, SourceFormat.XLSX, "tenant-a")
    ]


def test_pdf_is_explicitly_deferred() -> None:
    with pytest.raises(NotImplementedError, match="PDF"):
        parse(b"%PDF", SourceFormat.PDF, "tenant-a")


def test_classifier_is_pure_transparent_and_preserves_fields() -> None:
    question = Question(
        tenant_id="tenant-a",
        question_id="q-1",
        questionnaire_id="questionnaire-1",
        raw_text="Do you require MFA for privileged access?",
        normalized_text="Do you require MFA for privileged access?",
        section="Access Control",
        source_format=SourceFormat.TEXT,
    )

    classified = classify(question)

    assert classified is not question
    assert question.domain_label is None
    assert classified.domain_label == "identity_and_access_management"
    assert classified.answer_type == "yes_no"
    assert classified.model_dump(exclude={"domain_label", "answer_type"}) == question.model_dump(
        exclude={"domain_label", "answer_type"}
    )


@pytest.mark.parametrize(
    ("text", "answer_type"),
    [
        ("How often are backups tested?", "frequency"),
        ("How many incidents occurred?", "numeric"),
        ("Describe your security program.", "free_text"),
    ],
)
def test_classifier_answer_type_rules(text: str, answer_type: str) -> None:
    question = parse(text.encode(), SourceFormat.TEXT, "tenant-a")[0]
    assert classify(question).answer_type == answer_type
