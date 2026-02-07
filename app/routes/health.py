from flask import Blueprint

bp = Blueprint('health', __name__)

# Note: Main route and PWA routes remain in app/__init__.py for now
# to maintain root-level access. Can be moved here if needed.
