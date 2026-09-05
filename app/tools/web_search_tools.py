"""Web search tool. The agent decides WHEN this is necessary."""

from strands import tool


@tool
def search_web(query: str, max_results: int = 5) -> str:
    """Search the web for CURRENT external information (transport schedules,
    delays, opening hours, airport info, local activities). Use only when the
    trip state alone cannot answer the question."""
    try:
        from ddgs import DDGS

        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
    except Exception as exc:  # pragma: no cover - network dependent
        return f"Web search unavailable ({exc}). Reason from what you know."

    if not results:
        return "No results found."

    lines = [
        f"- {item.get('title', '')}: {item.get('body', '')} ({item.get('href', '')})"
        for item in results
    ]
    return "\n".join(lines)
