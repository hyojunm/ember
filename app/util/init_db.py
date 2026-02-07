from app import app
from ..extensions import db
from ..models import User, Item, Location, Category


def create_db():
    with app.app_context():
        # This deletes the old database so you can apply your 
        # nullable=False and field length changes!
        db.drop_all() 
        db.create_all()
        print('database initialized in site.db')


def seed_all():
    with app.app_context():
        # 1. seed admin user
        if not User.query.filter_by(username='pete').first():
            admin = User(username='pete', phone_number='800-123-4567')
            admin.set_password('boilerup')

            db.session.add(admin)
            db.session.commit()

        # 2. seed categories
        categories = ['Water', 'Food', 'Power', 'Tools', 'Medical']
        cat_objs = {}

        for name in categories:
            if not Category.query.filter_by(name=name).first():
                cat = Category(name=name)
                db.session.add(cat)

            cat_objs[name] = cat

        db.session.commit()

        # 3. seed locations (Location A will have 3+ items - Community Hub)
        loc_data = [
            {'name': 'Lawrenceville Community Center', 'address': '4600 Butler St', 'lat': 40.4707, 'lon': -79.9602},
            {'name': 'Squirrel Hill Library', 'address': '5801 Forbes Ave', 'lat': 40.4380, 'lon': -79.9229},
            {'name': 'South Side Market House', 'address': '12th and Bingham St', 'lat': 40.4287, 'lon': -79.9783},
            {'name': 'East Liberty Station', 'address': '5800 Penn Ave', 'lat': 40.4601, 'lon': -79.9248}
        ]
        
        loc_objs = []

        for loc in loc_data:
            if not Location.query.filter_by(address=loc['address']).first():
                location = Location(name=loc['name'], address=loc['address'], latitude=loc['lat'], longitude=loc['lon'])
                db.session.add(location)

            loc_objs.append(location)

        db.session.commit()

        # 4. seed 10 Items
        item_list = [
            # 3+ items at Lawrenceville Hub
            ('Case of Bottled Water', 'Water', loc_objs[0], 5),
            ('First Aid Trauma Kit', 'Medical', loc_objs[0], 1),
            ('Non-perishable Canned Goods', 'Food', loc_objs[0], 10),
            
            # Other distributed items
            ('Heavy Duty Snow Shovel', 'Tools', loc_objs[1], 2),
            ('Portable Generator', 'Power', loc_objs[1], 1),
            ('Rechargeable Lantern', 'Power', loc_objs[2], 3),
            ('Crowbar & Bolt Cutters', 'Tools', loc_objs[3], 1),
            ('Solar Phone Charger', 'Power', loc_objs[3], 2),
            ('Thermal Blankets', 'Medical', loc_objs[3], 5)
        ]

        for name, cat_name, loc_obj, qty in item_list:
            item = Item(
                item_name=name,
                item_desc=f'Essential {cat_name} gear for neighbors.',
                quantity=qty,
                user_id=admin.id,
                category_id=cat_objs[cat_name].id,
                location_id=loc_obj.id,
                pickup_instructions='Available on the front porch. Text via app before arriving.'
            )
            db.session.add(item)
        
        db.session.commit()
        print('database seeded with default values')


if __name__ == '__main__':
    create_db()
    seed_all()