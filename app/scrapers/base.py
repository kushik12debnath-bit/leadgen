"""Abstract base scraper + normalized Lead dict schema."""
import hashlib
from abc import ABC, abstractmethod
from typing import Any, Dict, List


NORMALIZED_LEAD_SCHEMA = {
    "name": None,
    "position": None,
    "company_name": None,
    "domain": None,
    "location": None,
    "sources": [],
    "phone": None,
    "email": None,
    "company_size": None,
    "website_url": None,
    "has_website": False,
    "social_links": {},
    "google_rating": None,
    "review_count": None,
    "digital_presence_score": 0,
}


class BaseScraper(ABC):
    source_name: str = "base"

    @abstractmethod
    async def scrape(self, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Return a list of normalized lead dicts."""
        raise NotImplementedError

    def normalize(self, raw: Dict[str, Any]) -> Dict[str, Any]:
        out = dict(NORMALIZED_LEAD_SCHEMA)
        out.update({k: v for k, v in raw.items() if k in out})
        out["sources"] = list(set((out.get("sources") or []) + [self.source_name]))
        return out


# --------------------------------------------------------------------------
# Deterministic mock identities: the SAME query always yields the SAME
# phone/email (so re-running a search dedups correctly), while a DIFFERENT
# domain/location yields different ones (so each new search = new leads).
# --------------------------------------------------------------------------
def _seed(params: Dict[str, Any], key: str = "") -> int:
    raw = "|".join([
        str(params.get("domain") or ""),
        str(params.get("location") or ""),
        str(params.get("company_name") or ""),
        key,
    ])
    return int(hashlib.md5(raw.encode("utf-8")).hexdigest(), 16)


def mock_phone(params: Dict[str, Any], key: str = "") -> str:
    n = (_seed(params, key) % 9000000000) + 1000000000
    s = str(n)
    return f"+91-{s[:5]}-{s[5:]}"


def mock_email(params: Dict[str, Any], key: str = "") -> str:
    domain = (params.get("domain") or "biz").lower().replace(" ", "")[:12]
    loc = (params.get("location") or "india").lower().replace(" ", "")[:10]
    tag = ["contact", "hello", "info", "sales"][_seed(params, key) % 4]
    return f"{tag}@{domain}{loc}.com"