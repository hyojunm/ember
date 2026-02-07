# ember

A progressive web app for decentralized resource distribution during
natural disaster relief.

## Build & Run

*To download the map file, you need to have Git LFS installed.*

Navigate to your desired directory, then clone the repository:

```bash
git clone https://github.com/hyojunm/ember.git
```

Set up a virtual environment and install dependencies:

```bash
python3 -m venv my_env
source my_env/bin/activate
python3 -m pip install -r requirements.txt
```

Initialize the sqlite database file (if needed):

```bash
python3 -m app.util.init_db
```

Run the app:

```bash
flask run --debug
```

## Development Plan

TartanHacks @ Carnegie Mellon University. February 6-7, 2026.

### Roles (for now)

- Keshav, *Map Guy*
- Caleb, *Auth Guy*
- Marvin, *Front End Guy*
- Jeremy, *Database Guy*

### Checkpoint 1

Complete by: **Friday, 10:00pm**

- [x] Create git repository
- [x] Set up Flask app structure
- [x] Finalize and implement database schema
- [ ] Integrate front end UI into app and ensure every button
      directs to the correct page
    - Main page (map and listings)
    - Login/register page
    - Profile settings page
    - My items page
    - Update item page
- [x] Implement register and login features, store info in
      database
- [x] Center the map based on the user's current location and
      set a max zoom out (limit view to local area)

### Checkpoint 2

Complete by: **Saturday, 10:00am**

- [ ] Implement add new item feature
    - Include all input fields necessary as outlined in database
      schema
    - Uploading (optional) pictures; figure out where/how
      to store the image
    - Convert address (given as input from the user) into
      latitude and longitude to store in database
- [ ] Implement update item feature
    - Should be very similar to add new item
    - Allow users to make items unavailable
- [ ] Implement delete item feature
- [ ] Ensure the user interface is compatible with smaller screen
      sizes
- [x] **(Priority)** Place pins on the map corresponding to listed
      items

### Checkpoint 3

Complete by: **Saturday, 4:00pm**

- [ ] **(Priority)** When the user clicks on a pin on the map, highlight
      the corresponding item "card" in the list panel
    - And vice versa
- [ ] **(Priority)** Implement offline rendering with PWA caching
    - Access site with Internet, cache all data. Then, disconnect from
      the Internet. All necessary content should still render.
- [ ] Color code pins on the map and items in the list for different
      categories
- [ ] Implement the filter and search features
    - Search is an exact match (substring)
    - Filters based on distance, category
- [ ] Implement profile settings, allow users to update data
    - Username, password (with confirmation), phone number, and phone number
      publicity should be editable by the user
- [ ] *(Extra)* Implement phone number verification with Twilio or similar
      APIs
- [ ] *(Extra)* Profile picture

### Checkpoint 4

Complete by: **Saturday, 5:00pm**

- [ ] Wrap up and polish
- [ ] Submit project for judging
- [ ] Prepare presentation for expo
