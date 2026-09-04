"""Callables Gemini can invoke via automatic function calling."""
import re

from . import config
from .rag import RagIndex


def make_tools(rag_index: RagIndex, sources_used: list[str] | None = None):
    def search_course_materials(query: str) -> str:
        """Search the Fusemachines AI Fellowship course materials for relevant passages.

        Use this whenever the user asks anything about course content, assignments,
        or concepts covered in the fellowship -- do not answer from memory alone.

        Args:
            query: A short search query describing what to look for.
        """
        hits = rag_index.search(query, top_k=config.TOP_K)
        if not hits:
            return "No relevant course material found."

        if sources_used is not None:
            for hit in hits:
                if hit.source not in sources_used:
                    sources_used.append(hit.source)

        parts = [f"[Source: {hit.source}]\n{hit.text}" for hit in hits]
        return "\n\n".join(parts)

    def list_available_weeks() -> str:
        """List which weeks of course material are available to search."""
        found = set()
        for hit in rag_index.chunks:
            m = re.match(r"Week_(\d+)_", hit.source)
            if m:
                found.add(int(m.group(1)))
        return "Available weeks: " + ", ".join(str(w) for w in sorted(found))

    return [search_course_materials, list_available_weeks]
