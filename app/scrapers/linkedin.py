"""LinkedIn scraper (Phase 1: mock hook)."""
import asyncio
from .base import BaseScraper, mock_phone, mock_email


class LinkedInScraper(BaseScraper):
    source_name = "linkedin"

    async def scrape(self, params):
        await asyncio.sleep(0.2)
        location = params.get("location", "Unknown")
        domain = params.get("domain", "B2B")
        company = params.get("company_name") or f"{domain} Solutions"
        position = params.get("position") or "Decision Maker"
        leads = [
            {
                "name": "Ankit Verma", "position": position,
                "company_name": company, "domain": domain,
                "location": f"{location}, India",
                "phone": None, "email": mock_email(params, "li1"),
                "company_size": "201-500", "website_url": f"https://{company.lower().replace(' ', '')}.com",
                "has_website": True,
                "social_links": {"linkedin": "https://linkedin.com/in/ankitverma"},
                "google_rating": None, "review_count": None,
            },
            {
                "name": "Neha Kapoor", "position": "Head of Operations",
                "company_name": f"{company} - {location}", "domain": domain,
                "location": f"{location}, India",
                "phone": mock_phone(params, "li2"), "email": None,
                "company_size": "51-200", "website_url": None, "has_website": False,
                "social_links": {"linkedin": "https://linkedin.com/in/nehakapoor"},
                "google_rating": None, "review_count": None,
            },
        ]
        return [self.normalize(l) for l in leads]