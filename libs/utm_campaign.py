"""Generate attributable, non-duplicated campaign URLs without network access."""

import re
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

ALLOWED_SOURCES = frozenset({
    "instagram", "bluesky", "facebook", "threads", "line", "note", "youtube"
})
CAMPAIGN_RE = re.compile(r"^[a-z0-9_-]{3,80}$")


def build_campaign_url(base_url: str, *, source: str, campaign: str,
                       content: str, medium: str = "organic_social") -> str:
    """Preserve unrelated query params; replace existing UTM values.

    This only generates a URL. It does not post, track users, or imply sales.
    """
    parts = urlsplit(base_url)
    if parts.scheme != "https" or not parts.hostname or parts.username or parts.password:
        raise ValueError("A public HTTPS URL without embedded credentials is required")
    if source not in ALLOWED_SOURCES:
        raise ValueError("Unrecognized traffic source")
    for name, value in (("campaign", campaign), ("content", content), ("medium", medium)):
        if not CAMPAIGN_RE.fullmatch(value):
            raise ValueError(f"Invalid {name} slug")
    existing = [(k, v) for k, v in parse_qsl(parts.query, keep_blank_values=True)
                if not k.lower().startswith("utm_")]
    existing.extend([
        ("utm_source", source),
        ("utm_medium", medium),
        ("utm_campaign", campaign),
        ("utm_content", content),
    ])
    return urlunsplit((parts.scheme, parts.netloc, parts.path,
                       urlencode(existing), parts.fragment))
