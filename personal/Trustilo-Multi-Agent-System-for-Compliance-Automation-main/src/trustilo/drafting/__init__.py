"""Grounded answer drafting (FR5) and citation generation (FR6).

See specs/06-drafting.md and this package's AGENTS.md.
SAFETY-CRITICAL: read .cursor/rules/llm-prompting-and-grounding.mdc first.
"""

from trustilo.drafting.service import draft


__all__ = ["draft"]
