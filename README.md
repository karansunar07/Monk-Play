# Monk Play Flask Music Website

This is a playlist management website built with Flask, HTML, CSS, and JavaScript.
It now includes:

- email login, user registration, and forgot password reset
- CSRF protection for form submissions
- Spotify playlist importing
- admin user editing, role management, and user deletion
- manual music uploads with title, description, artist, album, link, and duration fields
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

3. Start the Flask app:

```powershell
python app.py
```

4. Open this URL in your browser:

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

## Security

All POST forms include a CSRF token. The app validates the token before processing login, registration, password reset, admin actions, Spotify import, and manual music upload requests.

## Project structure

- `app.py` - Flask routes, login, password reset, playlist import, admin tools, CSRF checks, and log capture
- `app/templates/` - Jinja HTML templates
- `app/statics/css/style.css` - app styling
- `app/statics/js/app.js` - small UI helpers
