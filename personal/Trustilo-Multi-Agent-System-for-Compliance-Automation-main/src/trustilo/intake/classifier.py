"""Small, transparent rule-based classifier for Phase 1 demos."""

from __future__ import annotations

import re

from trustilo.common.schemas import Question


_DOMAIN_RULES: tuple[tuple[str, tuple[str, ...]], ...] = (
    (
        "identity_and_access_management",
        ("access", "authentication", "authorization", "mfa", "password", "identity"),
    ),
    ("data_security", ("data", "encrypt", "retention", "deletion", "privacy")),
    ("incident_management", ("incident", "breach", "response plan", "forensic")),
    ("business_continuity", ("backup", "disaster recovery", "business continuity", "resilience")),
    ("logging_and_monitoring", ("log", "logs", "logging", "monitor", "monitoring", "alert", "audit trail")),
    (
        "application_security",
        ("application", "software", "secure development", "source code", "vulnerability"),
    ),
    ("infrastructure_security", ("network", "firewall", "infrastructure", "server", "cloud")),
    ("supply_chain", ("vendor", "supplier", "third party", "subprocessor")),
    ("governance_risk_and_compliance", ("policy", "compliance", "audit", "risk", "governance")),
)


def _contains_keyword(text: str, keyword: str) -> bool:
    return re.search(rf"(?<!\w){re.escape(keyword)}(?!\w)", text) is not None


def _domain(text: str) -> str:
    for label, keywords in _DOMAIN_RULES:
        if any(_contains_keyword(text, keyword) for keyword in keywords):
            return label
    return "general_security"


def _answer_type(text: str) -> str:
    if any(_contains_keyword(text, keyword) for keyword in ("how often", "frequency", "cadence")):
        return "frequency"
    if any(_contains_keyword(text, keyword) for keyword in ("how many", "number of", "percentage", "count")):
        return "numeric"
    if any(_contains_keyword(text, keyword) for keyword in ("when", "what date", "which year")):
        return "date"
    if re.match(r"^(do|does|did|is|are|was|were|can|could|will|would|has|have)\b", text):
        return "yes_no"
    return "free_text"


def classify(question: Question) -> Question:
    """Return a classified copy while preserving every other field."""

    text = (question.normalized_text or question.raw_text).casefold()
    return question.model_copy(update={"domain_label": _domain(text), "answer_type": _answer_type(text)})
