"""Instagram scraper (Phase 1: mock hook)."""
import asyncio
from .base import BaseScraper, mock_email


class InstagramScraper(BaseScraper):
    source_name = "instagram"

    async def scrape(self, params):
        await asyncio.sleep(0.2)
        location = params.get("location", "Unknown")
        domain = params.get("domain", "Business")
        leads = [
            {
                "name": "Aisha Khan", "position": "Founder",
                "company_name": f"{domain} Studio - {location}",
                "domain": domain, "location": f"{location}, India",
                "phone": None, "email": mock_email(params, "ig1"),
                "company_size": "1-10", "website_url": "https://studio.example.com",
                "has_website": True,
                "social_links": {"instagram": "https://instagram.com/studiohandle"},
                "google_rating": None, "review_count": None,
            },
        ]
        return [self.normalize(l) for l in leads]