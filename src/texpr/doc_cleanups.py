import re


def gemini_cleanups(body: str) -> str:
    """
    Extra modifications to clean up Gemini Deep Research output.
    """

    # Gemini puts "Works cited" as an h4 for some reason.
    # Convert any "Works cited" header to h2 level like other main sections.
    body = re.sub(r"#{1,6}\s+(works\s+cited)", r"## Works Cited", body, flags=re.IGNORECASE)

    return body
