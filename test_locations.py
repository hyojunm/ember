from app import app, db
from app.models import User, SavedLocation

with app.app_context():
    # Get first user
    user = User.query.first()
    if not user:
        print("❌ No users found! Create a user first.")
        exit()
    
    print(f"✅ Found user: {user.username}")
    
    # Check saved locations
    locations = SavedLocation.query.filter_by(user_id=user.id).all()
    print(f"✅ User has {len(locations)} saved locations:")
    
    for loc in locations:
        print(f"   - {loc.name}: {loc.address} ({loc.latitude}, {loc.longitude})")
    
    if len(locations) == 0:
        print("ℹ️  Adding a test location...")
        test_loc = SavedLocation(
            user_id=user.id,
            name="Test Location",
            address="Purdue University, West Lafayette, IN",
            latitude=40.4237,
            longitude=-86.9212
        )
        db.session.add(test_loc)
        db.session.commit()
        print("✅ Test location added!")
    
    # Test the user method
    locations_dict = user.get_saved_locations()
    print(f"\n✅ get_saved_locations() returns: {locations_dict}")