# Monk Play Flask Music Website

This is a playlist management website built with Flask, HTML, CSS, and JavaScript.
It now includes:

- email login and user registration
- Spotify playlist importing
- admin role management
- admin device song uploads
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

Admins can update user roles, import songs from the device, and view active logs and errors.

## Project structure

- `app.py` - Flask routes, login, playlist import, admin tools, and log capture
- `app/templates/` - Jinja HTML templates
- `app/statics/css/style.css` - app styling
- `app/statics/js/app.js` - small UI helpers
