"""Google Maps scraper (Phase 1: mock hook, Phase 2: Playwright)."""
import asyncio
from .base import BaseScraper, mock_phone, mock_email


class GMapsScraper(BaseScraper):
    source_name = "gmaps"

    async def scrape(self, params):
        await asyncio.sleep(0.2)  # simulate network
        location = params.get("location", "Unknown")
        domain = params.get("domain", "Local Business")
        leads = [
            {
                "name": "Ramesh Gupta", "position": "Owner",
                "company_name": f"{domain} Hub - {location}",
                "domain": domain, "location": f"{location}, India",
                "phone": mock_phone(params, "gmaps1"), "email": None,
                "company_size": "1-10", "website_url": None, "has_website": False,
                "social_links": {}, "google_rating": 4.6, "review_count": 128,
            },
            {
                "name": "Priya Sharma", "position": "Manager",
                "company_name": f"Prime {domain} - {location}",
                "domain": domain, "location": f"{location}, India",
                "phone": mock_phone(params, "gmaps2"), "email": mock_email(params, "gmaps2"),
                "company_size": "11-50", "website_url": f"https://prime{domain.lower().replace(' ', '')}.com",
                "has_website": True, "social_links": {"facebook": "https://facebook.com/primeexample"},
                "google_rating": 4.2, "review_count": 54,
            },
        ]
        return [self.normalize(l) for l in leads]