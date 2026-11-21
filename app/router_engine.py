"""Smart Router & Custom Dispatcher."""
from .config import LOCAL_SMB_KEYWORDS, B2B_INDUSTRIAL_KEYWORDS, COMPANY_OVERRIDES, AVAILABLE_SOURCES


def _classify_auto(domain: str, company_name: str = None) -> list:
    text = (domain or "").strip().lower()
    if company_name:
        cn = company_name.strip().lower()
        for key, src in COMPANY_OVERRIDES.items():
            if key in cn:
                return ["linkedin"] if src == "linkedin" else ["gmaps"]
    for kw in LOCAL_SMB_KEYWORDS:
        if kw in text:
            return ["gmaps"]
    for kw in B2B_INDUSTRIAL_KEYWORDS:
        if kw in text:
            return ["linkedin"]
    if company_name and company_name.strip():
        return ["linkedin"]
    return ["gmaps"]


def resolve_sources(mode: str, domain: str = None, company_name: str = None,
                    selected_sources: list = None) -> list:
    """Return the list of source names to dispatch."""
    if mode == "auto":
        return _classify_auto(domain or "", company_name)
    # custom
    if not selected_sources:
        raise ValueError("selected_sources required for custom mode")
    out = []
    for s in selected_sources:
        s = s.strip().lower()
        if s not in AVAILABLE_SOURCES:
            raise ValueError(f"Unknown source: {s}")
        if s not in out:
            out.append(s)
    if not out:
        raise ValueError("No valid sources selected")
    return out