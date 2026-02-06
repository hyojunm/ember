from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy


# Initialize the database instance here to avoid circular imports
db = SQLAlchemy()
login_manager = LoginManager()
