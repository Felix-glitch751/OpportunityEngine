import hashlib
import re
import unicodedata
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


TRACKING_PARAMS = {
    "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
    "fbclid", "gclid", "mc_cid", "mc_eid", "ref", "referrer",
}


def canonicalize_url(value: str) -> str:
    """Normaliza URLs para evitar duplicados por tracking, fragmentos y barras."""
    value = (value or "").strip()
    if not value:
        return value

    parts = urlsplit(value)
    scheme = parts.scheme.lower() or "https"
    netloc = parts.netloc.lower()
    if netloc.startswith("www."):
        netloc = netloc[4:]

    path = re.sub(r"/{2,}", "/", parts.path or "/")
    if path != "/":
        path = path.rstrip("/")

    query = []
    for key, val in parse_qsl(parts.query, keep_blank_values=True):
        lowered = key.lower()
        if lowered in TRACKING_PARAMS or lowered.startswith("utm_"):
            continue
        query.append((key, val))
    query.sort()

    return urlunsplit((scheme, netloc, path, urlencode(query), ""))


def normalize_text(value: str) -> str:
    text = unicodedata.normalize("NFKD", value or "")
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.lower()
    text = re.sub(r"https?://\S+", " ", text)
    text = re.sub(r"[^a-z0-9%$]+", " ", text)
    return " ".join(text.split())


def material_fingerprint(opportunity) -> str:
    """Huella estable de los datos económicos importantes de una oportunidad."""
    raw = opportunity.raw_data or {}
    discount = float(raw.get("discount_percent", 0) or 0)
    opportunity_type = str(raw.get("opportunity_type", opportunity.category or ""))
    payload = "|".join([
        opportunity.source_id,
        normalize_text(opportunity.title),
        opportunity_type,
        f"{float(opportunity.reward_amount or 0):.2f}",
        f"{float(opportunity.required_cost or 0):.2f}",
        f"{discount:.2f}",
        str(opportunity.expires_at or ""),
    ])
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
