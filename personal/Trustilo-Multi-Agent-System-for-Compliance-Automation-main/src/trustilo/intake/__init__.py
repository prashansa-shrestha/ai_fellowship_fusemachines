"""Questionnaire parsing (FR1) and question classification (FR2).

See specs/04-intake-classification.md and this package's AGENTS.md.
"""

from trustilo.intake.classifier import classify
from trustilo.intake.parser import parse

__all__ = ["classify", "parse"]
