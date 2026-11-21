"""Facebook scraper (Phase 1: mock hook)."""
import asyncio
from .base import BaseScraper, mock_phone


class FacebookScraper(BaseScraper):
    source_name = "facebook"

    async def scrape(self, params):
        await asyncio.sleep(0.2)
        location = params.get("location", "Unknown")
        domain = params.get("domain", "Business")
        leads = [
            {
                "name": "Vikram Singh", "position": "Owner",
                "company_name": f"{domain} Corner - {location}",
                "domain": domain, "location": f"{location}, India",
                "phone": mock_phone(params, "fb1"), "email": None,
                "company_size": "1-10", "website_url": None, "has_website": False,
                "social_links": {"facebook": "https://facebook.com/bizcorner"},
                "google_rating": None, "review_count": None,
            },
        ]
        return [self.normalize(l) for l in leads]