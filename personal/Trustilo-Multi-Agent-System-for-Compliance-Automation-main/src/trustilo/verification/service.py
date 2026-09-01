"""Independent, deterministic verification for the local Phase 3 demo."""

from __future__ import annotations

import hashlib
import re
from collections.abc import Sequence
from datetime import datetime, timezone

from trustilo.common.schemas import Answer, Citation, EvidenceChunk, VerificationResult


_TOKEN_RE = re.compile(r"\w+", re.UNICODE)
_VERIFIER_VERSION = "deterministic-rule-verifier-v1"
_POLARITY_PAIRS: tuple[tuple[str, str], ...] = (
    ("required", "optional"),
    ("enabled", "disabled"),
    ("allowed", "prohibited"),
    ("permitted", "prohibited"),
    ("supported", "unsupported"),
)
_NEGATIONS = frozenset({"no", "not", "never"})
_CLAUSE_SPLIT_RE = re.compile(r"[.!?;,]+|\b(?:and|but|whereas|while)\b", re.IGNORECASE)
_SUBJECT_STOP_WORDS = frozenset(
    {"a", "an", "the", "to", "for", "of", "in", "on", "by", "our", "your"}
)
_SUBJECT_BOUNDARIES = frozenset(
    {"am", "are", "be", "been", "being", "is", "was", "were"}
) | _NEGATIONS | frozenset(word for pair in _POLARITY_PAIRS for word in pair)


def _tokens(text: str) -> tuple[str, ...]:
    return tuple(_TOKEN_RE.findall(text.casefold()))


def _stable_id(prefix: str, *parts: str) -> str:
    digest = hashlib.sha256()
    for part in parts:
        encoded = part.encode("utf-8")
        digest.update(len(encoded).to_bytes(8, "big"))
        digest.update(encoded)
    return f"{prefix}_{digest.hexdigest()[:24]}"


def _aware_utc(value: datetime, *, label: str) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{label} must be timezone-aware")
    return value.astimezone(timezone.utc)


def _validated_lookup(
    answer: Answer,
    evidence: Sequence[EvidenceChunk],
) -> dict[str, EvidenceChunk]:
    if isinstance(evidence, (str, bytes)) or not isinstance(evidence, Sequence):
        raise TypeError("evidence must be a sequence of EvidenceChunk objects")

    lookup: dict[str, EvidenceChunk] = {}
    for chunk in evidence:
        if not isinstance(chunk, EvidenceChunk):
            raise TypeError("evidence must contain only EvidenceChunk objects")
        if chunk.tenant_id != answer.tenant_id:
            raise ValueError(
                f"evidence chunk {chunk.chunk_id!r} belongs to a different tenant"
            )
        if chunk.chunk_id in lookup:
            raise ValueError(
                f"duplicate evidence chunk_id {chunk.chunk_id!r} makes verification ambiguous"
            )
        lookup[chunk.chunk_id] = chunk
    return lookup


def _textually_supported(claim_text: str, evidence_text: str) -> bool:
    """Require a contiguous whole-token passage, ignoring punctuation and case."""

    claim_tokens = _tokens(claim_text)
    evidence_tokens = _tokens(evidence_text)
    if not claim_tokens or len(claim_tokens) > len(evidence_tokens):
        return False
    width = len(claim_tokens)
    return any(
        evidence_tokens[start : start + width] == claim_tokens
        for start in range(len(evidence_tokens) - width + 1)
    )


def _clause_relations(text: str) -> tuple[tuple[frozenset[str], bool, frozenset[str]], ...]:
    """Extract small subject/polarity relations without joining separate clauses."""

    polarity_terms = frozenset(word for pair in _POLARITY_PAIRS for word in pair)
    relations: list[tuple[frozenset[str], bool, frozenset[str]]] = []
    for raw_clause in _CLAUSE_SPLIT_RE.split(text):
        tokens = _tokens(raw_clause)
        if not tokens:
            continue

        boundary = next(
            (index for index, token in enumerate(tokens) if token in _SUBJECT_BOUNDARIES),
            len(tokens),
        )
        subject = frozenset(
            token for token in tokens[:boundary] if token not in _SUBJECT_STOP_WORDS
        )
        polarities = frozenset(token for token in tokens if token in polarity_terms)
        negated = bool(set(tokens) & _NEGATIONS)
        if subject and (polarities or negated):
            relations.append((subject, negated, polarities))
    return tuple(relations)


def _polarity_conflicts(claim_text: str, evidence_text: str) -> tuple[str, ...]:
    """Return explicit polarity disagreements for the same local subject."""

    conflicts: list[str] = []
    for claim_subject, claim_negated, claim_polarities in _clause_relations(claim_text):
        for evidence_subject, evidence_negated, evidence_polarities in _clause_relations(
            evidence_text
        ):
            if claim_subject != evidence_subject:
                continue

            if (
                claim_negated != evidence_negated
                and bool(claim_polarities & evidence_polarities)
                and "negation" not in conflicts
            ):
                conflicts.append("negation")

            for left, right in _POLARITY_PAIRS:
                if left in claim_polarities and right in evidence_polarities:
                    opposed = (not claim_negated) != evidence_negated
                elif right in claim_polarities and left in evidence_polarities:
                    opposed = claim_negated != (not evidence_negated)
                else:
                    opposed = False
                flag = f"{left}_vs_{right}"
                if opposed and flag not in conflicts:
                    conflicts.append(flag)
    return tuple(conflicts)


def _citation_freshness(
    citation: Citation,
    chunk: EvidenceChunk,
    as_of: datetime,
) -> tuple[str, ...]:
    flags: list[str] = []
    valid_from = chunk.version_info.valid_from
    if valid_from is not None and as_of < _aware_utc(
        valid_from,
        label=f"valid_from for chunk {chunk.chunk_id!r}",
    ):
        flags.append(
            f"future_evidence:{citation.claim_id}:{citation.citation_id}:{chunk.chunk_id}"
        )

    valid_until = chunk.version_info.valid_until
    if valid_until is not None and as_of > _aware_utc(
        valid_until,
        label=f"valid_until for chunk {chunk.chunk_id!r}",
    ):
        flags.append(
            f"expired_evidence:{citation.claim_id}:{citation.citation_id}:{chunk.chunk_id}"
        )
    return tuple(flags)


def check(
    answer: Answer,
    evidence: Sequence[EvidenceChunk],
    *,
    as_of: datetime | None = None,
) -> VerificationResult:
    """Independently verify claims against tenant-scoped cited evidence.

    ``support_score`` is the fraction of claims for which every citation
    resolves, matches its declared provenance, and textually supports the
    claim.  Freshness is reported separately and does not alter textual
    support.  The current canonical schema has no general support-issue list,
    so resolution/support codes use ``contradiction_flags`` with explicit
    prefixes; real contradictions use the ``contradiction:`` prefix.
    """

    if not isinstance(answer, Answer):
        raise TypeError("answer must be an Answer")
    effective_as_of = _aware_utc(
        as_of if as_of is not None else datetime.now(timezone.utc),
        label="as_of",
    )
    lookup = _validated_lookup(answer, evidence)

    issue_flags: list[str] = []
    freshness_flags: list[str] = []
    if answer.abstained and not answer.claims:
        issue_flags.append("abstention:no_claims_to_verify")
        support_score = 1.0
    else:
        if answer.abstained:
            issue_flags.append("abstention:partial_claims_present")
        supported_claims = 0
        for claim in answer.claims:
            claim_supported = bool(claim.citations)
            if not claim.citations:
                issue_flags.append(f"uncited_claim:{claim.claim_id}")
            for citation in claim.citations:
                prefix = f"{claim.claim_id}:{citation.citation_id}:{citation.chunk_id}"
                if citation.claim_id != claim.claim_id:
                    issue_flags.append(f"citation_claim_mismatch:{prefix}")
                    claim_supported = False

                chunk = lookup.get(citation.chunk_id)
                if chunk is None:
                    issue_flags.append(f"unresolved_citation:{prefix}")
                    claim_supported = False
                    continue

                if citation.doc_id != chunk.doc_id:
                    issue_flags.append(f"citation_doc_mismatch:{prefix}")
                    claim_supported = False
                if citation.version != chunk.version_info.version:
                    issue_flags.append(f"citation_version_mismatch:{prefix}")
                    claim_supported = False

                freshness_flags.extend(_citation_freshness(citation, chunk, effective_as_of))

                if not _textually_supported(claim.text, chunk.text):
                    issue_flags.append(f"unsupported_claim:{prefix}")
                    claim_supported = False
                    for conflict in _polarity_conflicts(claim.text, chunk.text):
                        issue_flags.append(f"contradiction:{prefix}:{conflict}")

            if claim_supported:
                supported_claims += 1

        total_claims = len(answer.claims)
        support_score = supported_claims / total_claims if total_claims else 0.0

    flag_fingerprint = "|".join((*issue_flags, *freshness_flags))
    verification_id = _stable_id(
        "verification",
        answer.tenant_id,
        answer.answer_id,
        f"{support_score:.12f}",
        flag_fingerprint,
    )
    return VerificationResult(
        verification_id=verification_id,
        answer_id=answer.answer_id,
        support_score=support_score,
        contradiction_flags=issue_flags,
        freshness_flags=freshness_flags,
        consistent_with_prior=None,
        requested_requery=False,
        requery_query=None,
        verifier_model_version=_VERIFIER_VERSION,
    )
