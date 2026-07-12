# Monk Play Flask Music Website

This is a playlist management website built with Flask, HTML, CSS, and JavaScript.
It now includes:

- email login, user registration, and forgot password reset
- CSRF protection for form submissions
- cookie manipulation for saving, reading, and clearing browser preferences
- Spotify playlist importing
- admin user editing, role management, and user deletion
- manual music uploads with title, description, artist, album, link, and duration fields
- saved-track listing on the home page from the local database
- a fixed music player bar with play, pause, skip, seek, shuffle, repeat, mute, and volume controls
- an admin dashboard log console for active logs and errors

## Run locally

1. Create and activate a virtual environment:

```powershell
python -m venv venv
venv\Scripts\activate
```

2. Install dependencies:

```powershell
pip install -r requirements.txt
```

3. Configure MySQL in `config.py`:

```python
MYSQL_HOST = "localhost"
MYSQL_USER = "root"
MYSQL_PASSWORD = "root"
MYSQL_DATABASE = "flask_crud"
```

The app creates the configured MySQL database and tables automatically on startup.
If you want to create them manually, run:

```powershell
mysql -u root -p < schema.sql
```

4. Start the Flask app:

```powershell
python app.py
```

5. Open this URL in your browser:

```text
http://127.0.0.1:5000
```

## Dashboard

Open the dashboard after logging in:

```text
http://127.0.0.1:5000/dashboard
```

Admins can edit user details, update roles, delete users, add manual music uploads, and view active logs and errors.

## Admin tools

Admin accounts can manage users directly from the dashboard. The user table supports editing name, email, and role, plus deleting users when allowed.

Manual music can be added from the home page admin tools section. The form accepts a music file and stores title, description, artist, album, optional music link, and duration. Manual music is saved into an internal `Manual Music` collection automatically, so admins do not need to choose a playlist.

## Spotify import

Set the Spotify app credentials in `config.py` and make sure the redirect URI in the Spotify developer dashboard exactly matches:

```text
http://127.0.0.1:5000/spotify/callback
```

After connecting Spotify, the import page lists all readable playlists from the connected account. You can also paste a Spotify playlist URL or playlist ID directly into the import form.

Imported playlists and their saved tracks are visible on the home page for all users. Spotify does not provide full song files through this API, so the site plays Spotify preview audio when Spotify includes a preview URL. Tracks without preview audio can open an embedded Spotify player directly on the site.

## Saved tracks and player

The home page now reads saved tracks from the `imported_playlist_tracks` table instead of showing example rows. Tracks with an uploaded local file or Spotify preview URL include a Play button and can be controlled from the fixed bottom player. Imported Spotify tracks without preview audio show an in-page Spotify embed.

The bottom player shows the current track title and artist, supports previous and next navigation, shuffle, repeat, progress seeking, mute, and volume control. It only appears when at least one saved track has a playable uploaded file.

## Security

All POST forms include a CSRF token. The app validates the token before processing login, registration, password reset, admin actions, Spotify import, and manual music upload requests.

## Cookie tools

Admin users can open the cookie tools page directly by URL to save a listener name and music preference in browser cookies, read the current cookie values, or clear the saved cookies:

```text
http://127.0.0.1:5000/cookies
```

## Project structure

- `app.py` - Flask routes, login, password reset, playlist import, admin tools, CSRF checks, and log capture
- `schema.sql` - MySQL database and table setup for all saved records
- `app/templates/` - Jinja HTML templates
- `app/statics/css/style.css` - app styling
- `app/statics/js/app.js` - small UI helpers
