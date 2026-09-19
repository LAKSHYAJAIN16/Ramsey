import os
from pathlib import Path

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
CACHE_DIR = BASE_DIR / "backend" / "data" / "cache"
DEMO_RECIPE_PATH = DATA_DIR / "demo_recipe.json"

BROWSERBASE_API_KEY = os.environ.get("BROWSERBASE_API_KEY", "")
BROWSERBASE_PROJECT_ID = os.environ.get("BROWSERBASE_PROJECT_ID", "")
BACKBOARD_API_KEY = os.environ.get("BACKBOARD_API_KEY", "")
BACKBOARD_MODEL = os.environ.get("BACKBOARD_MODEL", "")
ELEVENLABS_API_KEY = os.environ.get("ELEVENLABS_API_KEY", "")
RAMSEY_PORT = int(os.environ.get("RAMSEY_PORT", "8000"))
SESSION_SECRET = os.environ.get("SESSION_SECRET", "ramsey-local-development-secret")
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", "")
GOOGLE_REDIRECT_URI = os.environ.get("GOOGLE_REDIRECT_URI", "http://localhost:8000/api/auth/google/callback")

MIN_INGREDIENTS = 3
MIN_STEPS = 2
