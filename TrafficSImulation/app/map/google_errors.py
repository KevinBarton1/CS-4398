import httpx


def format_google_api_error(response: httpx.Response, *, max_length: int = 800) -> str:
    """Extract a readable Google API error message, including fieldViolations."""
    try:
        body = response.json()
    except ValueError:
        return response.text.strip().replace("\n", " ")[:max_length]

    error = body.get("error") or {}
    parts: list[str] = []

    message = error.get("message")
    if message:
        parts.append(str(message))

    for detail in error.get("details") or []:
        if "BadRequest" not in str(detail.get("@type", "")):
            continue
        for violation in detail.get("fieldViolations") or []:
            field = violation.get("field") or "unknown field"
            description = violation.get("description") or "invalid value"
            parts.append(f"{field}: {description}")

    if parts:
        text = "; ".join(parts)
    else:
        text = response.text.strip().replace("\n", " ")

    return text[:max_length]
