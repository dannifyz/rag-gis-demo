import os
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[2]

load_dotenv(PROJECT_ROOT / ".env")

api_key = os.getenv("GOOGLE_API_KEY")

if not api_key:
    raise RuntimeError(f"GOOGLE_API_KEY not set. Add it to {PROJECT_ROOT / '.env'}")
