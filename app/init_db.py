from app import app
from .extensions import db
from .models import User, Item, Location, Category


def create_db():
    with app.app_context():
        # This deletes the old database so you can apply your 
        # nullable=False and field length changes!
        db.drop_all() 
        db.create_all()
        print('database initialized in site.db')


# input default categories into db
# input shared community locations into db


if __name__ == '__main__':
    create_db()