# Monk Play Flask Music Website

This is a Spotify-inspired music website built with Flask, HTML, CSS, and JavaScript.
It now includes:

- a Gmail login page wired for Google OAuth
- a Spotify playlist helper that cleans copied song lists
- a one-click copy flow for pasted tracks

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

3. Start the Flask app:

```powershell
python app.py
```

4. Open this URL in your browser:

```text
http://127.0.0.1:5000
```

## Gmail login setup

1. Create Google OAuth credentials in Google Cloud Console.
2. Add this redirect URI:

```text
http://127.0.0.1:5000/auth/google
```

3. Set these environment variables before starting Flask:

```powershell
$env:SECRET_KEY="replace-this"
$env:GOOGLE_CLIENT_ID="your-google-client-id"
$env:GOOGLE_CLIENT_SECRET="your-google-client-secret"
```

4. Start the app and open:

```text
http://127.0.0.1:5000/login
```

## Spotify playlist helper

Open:

```text
http://127.0.0.1:5000/playlist-helper
```

Best workflow:

1. Copy the visible track list from Spotify.
2. Paste it into the helper.
3. Click `Copy all songs` to get a clean track list.

## Project structure

- `app.py` - Flask routes, Google login flow, and playlist helper logic
- `templates/` - Jinja HTML templates
- `static/css/style.css` - Spotify-inspired styling
- `static/js/main.js` - Player interactions and clipboard helpers
