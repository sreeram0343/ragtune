"""
RAGTUNE Output Security & Response Governance Engine - Response Formatter
Formats narrative content into clean Markdown, JSON, or Plain Text structures.
"""



class ResponseFormatter:
    def format_markdown(self, content: str, citations: list[str] = None) -> str:
        """Formats content into clean enterprise Markdown layout."""
        if not content:
            return ""

        formatted = content.strip()
        if citations:
            formatted += "\n\n### Source Evidence & Citations\n"
            for c in citations:
                formatted += f"- {c}\n"

        return formatted

    def format_plain_text(self, content: str) -> str:
        """Strips markdown headers and returns plain text narrative."""
        if not content:
            return ""
        return content.replace("#", "").strip()
