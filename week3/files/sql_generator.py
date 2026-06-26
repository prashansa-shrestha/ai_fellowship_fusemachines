"""sql_generator.py — parse task decompositions and produce SELECT statements.

Decompositions are read from a Markdown file that uses the numbered format::

    1) Question: <text>
    - Intent: <text>
    - Tables: <comma-separated list>
    - Columns: <comma-separated list>
    - Filters: <expression or None>
    - Joins: <expression or None>

SQL is generated locally from the structured fields; the Anthropic API is
called only for questions that cannot be resolved deterministically (e.g.
when the decomposition is ambiguous or incomplete).
"""

from __future__ import annotations

import os
import re
from typing import Any, Dict, List, Optional, Tuple

import anthropic  # pip install anthropic


# ---------------------------------------------------------------------------
# Markdown parser
# ---------------------------------------------------------------------------

def _split_top_level(text: str) -> List[str]:
    """Split *text* on commas, but skip commas inside parentheses."""
    parts: List[str] = []
    buf = ""
    depth = 0
    for ch in text:
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth = max(0, depth - 1)
        if ch == "," and depth == 0:
            parts.append(buf)
            buf = ""
        else:
            buf += ch
    if buf.strip():
        parts.append(buf)
    return parts


def parse_decompositions(md_path: str) -> List[Dict[str, Any]]:
    """Parse *md_path* and return a list of decomposition dicts.

    Each dict has the keys:
    ``question``, ``intent``, ``tables``, ``columns``,
    ``filters``, ``joins``, ``table_aliases``.
    """
    with open(md_path, encoding="utf-8") as fh:
        raw = fh.read()

    # Each entry starts with a numbered marker like "1) Question:"
    chunks = re.split(r"\n\d+\) Question:", "\n" + raw)

    entries: List[Dict[str, Any]] = []
    for chunk in chunks[1:]:
        lines = chunk.strip().splitlines()
        entry: Dict[str, Any] = {
            "question":      lines[0].strip(),
            "intent":        None,
            "tables":        None,
            "columns":       None,
            "filters":       None,
            "joins":         None,
            "table_aliases": {},
        }

        for line in lines[1:]:
            line = line.strip()

            if line.startswith("- Intent:"):
                entry["intent"] = line.split(":", 1)[1].strip()

            elif line.startswith("- Tables:"):
                raw_tables = [t.strip() for t in line.split(":", 1)[1].split(",")]
                cleaned: List[str] = []
                for rt in raw_tables:
                    alias_match = re.match(r"(.+?)\s*\(alias\s+([a-zA-Z0-9_]+)\)", rt)
                    if alias_match:
                        tbl   = alias_match.group(1).strip()
                        alias = alias_match.group(2).strip()
                        cleaned.append(tbl)
                        entry["table_aliases"][alias] = tbl
                    else:
                        tbl = re.sub(r"\s*\(.*?\)", "", rt).strip()
                        cleaned.append(tbl)
                entry["tables"] = cleaned

            elif line.startswith("- Columns:"):
                raw_cols = line.split(":", 1)[1].strip()
                entry["columns"] = [c.strip() for c in _split_top_level(raw_cols)]

            elif line.startswith("- Filters:"):
                val = line.split(":", 1)[1].strip()
                entry["filters"] = val if val and val.lower() != "none" else None

            elif line.startswith("- Joins:"):
                val = line.split(":", 1)[1].strip()
                entry["joins"] = val if val and val.lower() != "none" else None

        entries.append(entry)
    return entries


# ---------------------------------------------------------------------------
# SQL builder (local, deterministic)
# ---------------------------------------------------------------------------

_ALIAS_RE = re.compile(r"\b([a-z]{1,3})\.")


def _build_alias_map(tables: List[str], explicit: Dict[str, str]) -> Dict[str, str]:
    mapping = dict(explicit)
    for t in tables:
        tn = re.sub(r"[^0-9a-zA-Z]", "", t.strip()).lower()
        for length in (2, 1):
            key = tn[:length]
            if key and key not in mapping:
                mapping[key] = t.strip()
    return mapping


def _fuzzy_alias(alias: str, tables: List[str]) -> Optional[str]:
    """Return the first table whose letters contain all letters in *alias* in order."""
    for t in tables:
        tn = re.sub(r"[^0-9a-zA-Z]", "", t.strip()).lower()
        pos = 0
        ok = True
        for ch in alias:
            idx = tn.find(ch, pos)
            if idx == -1:
                ok = False
                break
            pos = idx + 1
        if ok:
            return t.strip()
    return None


def generate_sql(decomp: Dict[str, Any]) -> str:
    """Produce a SELECT statement from a parsed decomposition dict.

    Raises ``ValueError`` for invalid or unsafe inputs.
    """
    tables  = [t for t in (decomp.get("tables") or [])]
    columns = list(decomp.get("columns") or [])
    joins   = decomp.get("joins")
    filters = decomp.get("filters")

    if not tables:
        raise ValueError("Decomposition contains no tables")

    # Strip trailing parenthetical annotations from join expressions
    if joins:
        joins = re.sub(r"\s*\([^)]*\)$", "", joins).strip()

    alias_map = _build_alias_map(tables, decomp.get("table_aliases") or {})

    # Detect aliases referenced in column / join expressions
    used_aliases: set = set()
    for col in columns:
        used_aliases.update(_ALIAS_RE.findall(col))
    if joins:
        used_aliases.update(_ALIAS_RE.findall(joins))

    # Resolve any unknown aliases via fuzzy matching
    for alias in list(used_aliases):
        if alias not in alias_map:
            resolved = _fuzzy_alias(alias, tables)
            if resolved:
                alias_map[alias] = resolved

    using_aliases = bool(used_aliases)

    if not using_aliases:
        # Expand short alias prefixes to full table names
        def _expand(text: str) -> str:
            def _sub_quoted(m: re.Match) -> str:
                a = m.group(1)
                return (alias_map[a] + '."') if a in alias_map else (a + '."')

            def _sub_plain(m: re.Match) -> str:
                a, col = m.group(1), m.group(2)
                return (alias_map[a] + "." + col) if a in alias_map else (a + "." + col)

            text = re.sub(r'\b([a-z]{1,2})\."', _sub_quoted, text)
            text = re.sub(r"\b([a-z]{1,2})\.([a-zA-Z_]\w*)", _sub_plain, text)
            return text

        columns = [_expand(c) for c in columns]
        if joins:
            joins = _expand(joins)

    # SELECT clause
    if len(columns) == 1 and columns[0].lower().startswith("all columns"):
        select_clause = "*"
    elif len(columns) == 1 and columns[0].upper().startswith("DISTINCT"):
        select_clause = columns[0]
    else:
        select_clause = ", ".join(columns)

    # JOIN type
    join_kw = "LEFT JOIN" if joins and "LEFT" in (decomp.get("joins") or "").upper() else "JOIN"

    # FROM / JOIN clause
    if joins and len(tables) >= 2:
        if using_aliases:
            assigned: set = set()
            rev = alias_map  # alias -> table

            def _alias_for(tbl: str) -> Optional[str]:
                for a in used_aliases:
                    if rev.get(a) == tbl and a not in assigned:
                        assigned.add(a)
                        return a
                return None

            first      = tables[0].strip()
            first_alias = _alias_for(first)
            from_clause = f"{first} AS {first_alias}" if first_alias else first

            for tbl in tables[1:]:
                tname = tbl.strip()
                ta    = _alias_for(tname)
                if ta:
                    from_clause += f" {join_kw} {tname} AS {ta} ON {joins}"
                else:
                    from_clause += f" {join_kw} {tname} ON {joins}"
        else:
            from_clause = tables[0].strip()
            for tbl in tables[1:]:
                from_clause += f" {join_kw} {tbl.strip()} ON {joins}"
    else:
        from_clause = ", ".join(t.strip() for t in tables)

    sql = f"SELECT {select_clause} FROM {from_clause}"
    if filters:
        sql += f" WHERE {filters}"

    # Append GROUP BY when aggregates and plain columns coexist
    agg_present = False
    plain_cols: List[str] = []
    for col in columns:
        if "(" in col and ")" in col:
            agg_present = True
        elif not col.strip().upper().startswith("DISTINCT"):
            plain_cols.append(col.strip())

    if agg_present and plain_cols:
        group_expr = ", ".join(c.split(" AS ")[0].strip() for c in plain_cols)
        sql += f" GROUP BY {group_expr}"

    sql += ";"

    if not sql.strip().upper().startswith("SELECT"):
        raise ValueError(f"Generated statement is not a SELECT: {sql!r}")

    return sql


# ---------------------------------------------------------------------------
# Anthropic-powered fallback (replaces the previous Ollama call)
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = (
    "You are a PostgreSQL expert. "
    "Given a natural-language question and optional metadata (tables, columns, filters, joins), "
    "return a single valid SELECT statement and nothing else — no explanations, no markdown fences."
)


def generate_sql_via_llm(decomp: Dict[str, Any]) -> str:
    """Ask the Anthropic API to produce SQL for *decomp*.

    Used as a fallback when the local builder cannot handle a decomposition.
    """
    client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from environment

    user_content = (
        f"Question: {decomp.get('question', '')}\n"
        f"Tables: {', '.join(decomp.get('tables') or [])}\n"
        f"Columns: {', '.join(decomp.get('columns') or [])}\n"
        f"Filters: {decomp.get('filters') or 'none'}\n"
        f"Joins: {decomp.get('joins') or 'none'}\n\n"
        "Write the SQL query."
    )

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=512,
        system=_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_content}],
    )

    raw = message.content[0].text.strip()
    # Strip accidental markdown fences
    raw = re.sub(r"^```[a-z]*\n?", "", raw, flags=re.IGNORECASE)
    raw = re.sub(r"\n?```$", "", raw)
    return raw.strip()
