"""Tests for the tenant-isolated Phase 2 in-memory retriever."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from trustilo.common.schemas import EvidenceChunk, Question, SourceFormat, VersionInfo
from trustilo.retrieval import InMemoryEvidenceIndex


AS_OF = datetime(2026, 8, 1, 12, tzinfo=timezone.utc)


def _chunk(
    chunk_id: str,
    text: str,
    *,
    tenant_id: str = "tenant-a",
    valid_from: datetime | None = None,
    valid_until: datetime | None = None,
) -> EvidenceChunk:
    return EvidenceChunk(
        tenant_id=tenant_id,
        chunk_id=chunk_id,
        doc_id=f"doc-{chunk_id}",
        text=text,
        version_info=VersionInfo(
            version="2026-01-01",
            source="synthetic_test",
            valid_from=valid_from,
            valid_until=valid_until,
        ),
    )


def _question(
    text: str = "Do you require multifactor authentication for privileged access?",
    *,
    tenant_id: str = "tenant-a",
    normalized_text: str | None = None,
) -> Question:
    return Question(
        tenant_id=tenant_id,
        question_id="q-1",
        questionnaire_id="questionnaire-1",
        raw_text=text,
        normalized_text=normalized_text,
        source_format=SourceFormat.TEXT,
    )


def test_adversarial_same_content_never_crosses_tenant_boundary() -> None:
    shared_text = "Privileged access requires multifactor authentication."
    index = InMemoryEvidenceIndex(
        [
            _chunk("a-only", shared_text, tenant_id="tenant-a"),
            _chunk("b-identical", shared_text, tenant_id="tenant-b"),
            _chunk(
                "b-perfect-phrase",
                "multifactor authentication privileged access",
                tenant_id="tenant-b",
            ),
        ]
    )

    results = index.search(_question(), "tenant-a", 10, as_of=AS_OF)

    assert [chunk.chunk_id for chunk in results] == ["a-only"]
    assert all(chunk.tenant_id == "tenant-a" for chunk in results)


def test_exact_phrase_and_full_coverage_rank_ahead_of_partial_overlap() -> None:
    index = InMemoryEvidenceIndex(
        [
            _chunk("partial", "Privileged users receive individual accounts."),
            _chunk(
                "full-scattered",
                "Privileged access is reviewed; multifactor controls provide authentication.",
            ),
            _chunk(
                "exact",
                "Our control requires multifactor authentication privileged access reviews.",
            ),
        ]
    )
    question = _question("multifactor authentication privileged access")

    results = index.search(question, "tenant-a", 10, as_of=AS_OF)

    assert [chunk.chunk_id for chunk in results] == [
        "exact",
        "full-scattered",
        "partial",
    ]


def test_irrelevant_evidence_is_not_used_to_pad_top_k() -> None:
    index = InMemoryEvidenceIndex(
        [
            _chunk("relevant", "Backups are tested every quarter."),
            _chunk("irrelevant", "Visitors sign in at reception."),
        ]
    )

    results = index.search(_question("How often are backups tested?"), "tenant-a", 5, as_of=AS_OF)

    assert [chunk.chunk_id for chunk in results] == ["relevant"]


def test_revised_query_fully_replaces_original_query_and_changes_results() -> None:
    index = InMemoryEvidenceIndex(
        [
            _chunk("backup", "Backups are tested quarterly."),
            _chunk("mfa", "Production database access requires hardware MFA."),
        ]
    )
    question = _question(
        "How often are backups tested?",
        normalized_text="How often are backups tested?",
    )

    original = index.search(question, "tenant-a", 5, as_of=AS_OF)
    revised = index.search(
        question,
        "tenant-a",
        5,
        revised_query="hardware MFA production database access",
        as_of=AS_OF,
    )

    assert [chunk.chunk_id for chunk in original] == ["backup"]
    assert [chunk.chunk_id for chunk in revised] == ["mfa"]


def test_expired_and_not_yet_valid_versions_are_excluded() -> None:
    index = InMemoryEvidenceIndex(
        [
            _chunk("active", "Backups are tested monthly."),
            _chunk(
                "expired",
                "Backups are tested weekly.",
                valid_until=AS_OF - timedelta(seconds=1),
            ),
            _chunk(
                "future",
                "Backups are tested daily.",
                valid_from=AS_OF + timedelta(seconds=1),
            ),
            _chunk("starts-now", "Backups are tested.", valid_from=AS_OF),
            _chunk("ends-now", "Backups are tested.", valid_until=AS_OF),
        ]
    )

    results = index.search(_question("backups tested"), "tenant-a", 10, as_of=AS_OF)

    assert {chunk.chunk_id for chunk in results} == {"active", "starts-now", "ends-now"}


def test_top_k_truncates_ranked_results() -> None:
    index = InMemoryEvidenceIndex(
        [
            _chunk("first", "Encryption keys rotate automatically."),
            _chunk("second", "Encryption keys are documented."),
            _chunk("third", "Encryption is enabled."),
        ]
    )

    results = index.search(_question("encryption keys rotate"), "tenant-a", 2, as_of=AS_OF)

    assert [chunk.chunk_id for chunk in results] == ["first", "second"]


@pytest.mark.parametrize("top_k", [0, -1, 1.5, True])
def test_top_k_must_be_a_positive_integer(top_k: object) -> None:
    index = InMemoryEvidenceIndex([])

    with pytest.raises(ValueError, match="top_k"):
        index.search(_question(), "tenant-a", top_k, as_of=AS_OF)  # type: ignore[arg-type]


def test_question_and_requested_tenant_must_match() -> None:
    index = InMemoryEvidenceIndex([_chunk("a", "MFA is required.")])

    with pytest.raises(ValueError, match="must match"):
        index.search(_question(tenant_id="tenant-a"), "tenant-b", 5, as_of=AS_OF)


@pytest.mark.parametrize("revised_query", ["", "   ", 42])
def test_revised_query_must_be_non_blank_text(revised_query: object) -> None:
    index = InMemoryEvidenceIndex([])

    with pytest.raises(ValueError, match="revised_query"):
        index.search(
            _question(),
            "tenant-a",
            5,
            revised_query=revised_query,  # type: ignore[arg-type]
            as_of=AS_OF,
        )


def test_as_of_must_be_timezone_aware() -> None:
    index = InMemoryEvidenceIndex([])

    with pytest.raises(ValueError, match="timezone-aware"):
        index.search(_question(), "tenant-a", 5, as_of=datetime(2026, 8, 1))


def test_ties_are_broken_by_stable_ids_not_input_order() -> None:
    chunks = [
        _chunk("z-chunk", "Backups are tested."),
        _chunk("a-chunk", "Backups are tested."),
    ]

    forward = InMemoryEvidenceIndex(chunks).search(
        _question("backups tested"), "tenant-a", 10, as_of=AS_OF
    )
    reversed_results = InMemoryEvidenceIndex(reversed(chunks)).search(
        _question("backups tested"), "tenant-a", 10, as_of=AS_OF
    )

    assert [chunk.chunk_id for chunk in forward] == ["a-chunk", "z-chunk"]
    assert [chunk.chunk_id for chunk in reversed_results] == ["a-chunk", "z-chunk"]


def test_input_and_result_mutation_cannot_change_index_snapshot() -> None:
    source = _chunk("original", "MFA is required.")
    index = InMemoryEvidenceIndex([source])
    source.tenant_id = "tenant-b"
    source.text = "Changed outside the index."

    first = index.search(_question("MFA"), "tenant-a", 5, as_of=AS_OF)
    first[0].tenant_id = "tenant-b"
    first[0].text = "Changed returned result."
    second = index.search(_question("MFA"), "tenant-a", 5, as_of=AS_OF)

    assert [(chunk.tenant_id, chunk.text) for chunk in second] == [
        ("tenant-a", "MFA is required.")
    ]
