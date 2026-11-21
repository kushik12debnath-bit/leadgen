"""Configuration."""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "lead_intel.db"
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DB_PATH}")

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
]

MIN_DELAY = float(os.getenv("MIN_DELAY", "1.0"))
MAX_DELAY = float(os.getenv("MAX_DELAY", "3.0"))

LOCAL_SMB_KEYWORDS = [
    "salon", "barber", "spa", "clinic", "doctor", "dentist", "gym", "fitness",
    "restaurant", "cafe", "bakery", "shop", "store", "plumber", "electrician",
    "tailor", "laundry", "pharmacy", "grocery", "supermarket", "pet",
    "veterinary", "tutor", "coaching", "tuition", "beauty", "parlour", "parlor",
    "hotel", "lodge", "resort", "travel", "agency", "real estate", "broker",
    "mechanic", "garage", "workshop", "florist", "photography", "studio",
    "boutique", "jeweller", "optician", "retail",
]

B2B_INDUSTRIAL_KEYWORDS = [
    "software", "saas", "iot", "plc", "manufacturing", "industrial",
    "enterprise", "b2b", "consulting", "technology", "tech", "automation",
    "robotics", "engineering", "construction", "infrastructure", "logistics",
    "supply chain", "wholesale", "distributor", "import", "export", "finance",
    "banking", "insurance", "healthcare", "pharma", "biotech", "energy", "oil",
    "gas", "mining", "aerospace", "defense", "telecom", "semiconductor",
    "electronics", "chemical", "textile", "automotive", "lt", "l&t",
]

COMPANY_OVERRIDES = {
    "l&t": "linkedin", "larsen & toubro": "linkedin", "tata": "linkedin",
    "reliance": "linkedin", "infosys": "linkedin", "wipro": "linkedin",
    "hcl": "linkedin", "tech mahindra": "linkedin",
}

AVAILABLE_SOURCES = ["gmaps", "linkedin", "facebook", "instagram"]