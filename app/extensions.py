import os
from dotenv import load_dotenv
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy

# Load .env at import time so DEDALUS_API_KEY is always available
load_dotenv()


# Initialize the database instance here to avoid circular imports
db = SQLAlchemy()
login_manager = LoginManager()

# --- Dedalus Labs SDK ---
# Lazily initialized; None when the API key is not set (offline / local dev)
_dedalus_client = None


def get_dedalus_client():
    """Return a Dedalus client singleton, or None if the key isn't configured."""
    global _dedalus_client
    if _dedalus_client is not None:
        return _dedalus_client

    api_key = os.environ.get("DEDALUS_API_KEY")
    if not api_key or api_key == "your-api-key-here":
        return None


    try:
        from dedalus_labs import Dedalus
        _dedalus_client = Dedalus(api_key=api_key)
        print("here")
        return _dedalus_client
    except Exception:
        return None
