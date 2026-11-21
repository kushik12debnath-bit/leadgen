"""Enrichment & Digital Presence Scoring."""
import re
import httpx
from bs4 import BeautifulSoup
from urllib.parse import urljoin

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PHONE_RE = re.compile(r"(?:\+?\d{1,3}[\s-]?)?(?:\(?\d{2,4}\)?[\s-]?)?\d{3,4}[\s-]?\d{3,4}")
SOCIAL_DOMAINS = ["facebook.com", "instagram.com", "twitter.com", "x.com",
                  "linkedin.com", "youtube.com", "tiktok.com"]


async def check_website(url):
    if not url:
        return False, False, None
    if not url.startswith("http"):
        url = "https://" + url
    try:
        async with httpx.AsyncClient(timeout=12, follow_redirects=True, verify=False) as c:
            r = await c.get(url, headers={"User-Agent": "Mozilla/5.0"})
            if r.status_code < 400:
                final = str(r.url)
                return True, final.lower().startswith("https://"), final
    except Exception:
        pass
    return False, False, None


async def crawl_contacts(url):
    emails, phones, socials = set(), set(), set()
    if not url:
        return emails, phones, socials
    if not url.startswith("http"):
        url = "https://" + url
    for p in [url, urljoin(url, "/contact"), urljoin(url, "/contact-us")]:
        try:
            async with httpx.AsyncClient(timeout=12, follow_redirects=True, verify=False) as c:
                r = await c.get(p, headers={"User-Agent": "Mozilla/5.0"})
                if r.status_code >= 400:
                    continue
                soup = BeautifulSoup(r.text, "html.parser")
                text = soup.get_text(" ", strip=True)
                for e in EMAIL_RE.findall(text):
                    if not e.lower().endswith((".png", ".jpg", ".jpeg", ".gif", ".svg")):
                        emails.add(e.lower())
                for ph in PHONE_RE.findall(text):
                    digits = re.sub(r"\D", "", ph)
                    if 7 <= len(digits) <= 15:
                        phones.add(ph.strip())
                for a in soup.find_all("a", href=True):
                    href = a["href"]
                    for sd in SOCIAL_DOMAINS:
                        if sd in href.lower():
                            socials.add(href)
        except Exception:
            continue
    return emails, phones, socials


async def enrich(lead: dict) -> dict:
    website = lead.get("website_url")
    score = 0
    is_live, is_https, final_url = await check_website(website)
    if website:
        lead["has_website"] = bool(is_live)
    if is_live:
        score += 30
        if final_url:
            lead["website_url"] = final_url
    if is_https and is_live:
        score += 10

    emails, phones, socials = set(), set(), set()
    if is_live and lead.get("website_url"):
        emails, phones, socials = await crawl_contacts(lead["website_url"])
    if socials:
        score += 20
        sd = lead.setdefault("social_links", {})
        for s in socials:
            for d in SOCIAL_DOMAINS:
                if d in s.lower() and d.split(".")[0] not in sd:
                    sd[d.split(".")[0]] = s
    if emails or phones or lead.get("email") or lead.get("phone"):
        score += 20
        if not lead.get("email") and emails:
            lead["email"] = sorted(emails)[0]
        if not lead.get("phone") and phones:
            lead["phone"] = sorted(phones)[0]

    rating = lead.get("google_rating")
    reviews = lead.get("review_count")
    if rating is not None and rating >= 4.0:
        score += 10
    if reviews is not None and reviews >= 20:
        score += 10

    lead["digital_presence_score"] = min(100, score)
    if not website:
        lead["has_website"] = False
    return lead