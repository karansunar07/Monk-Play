# Dashboard Notes

The dashboard is built from `get_dashboard_data()` in `app.py` and rendered by `app/templates/dashboard.html`.

It is designed to show a quick picture of the account:

- imported playlist count
- saved track count
- uploaded local file count
- manually added track count
- recent playlists
- recent songs
- admin user totals
- recent application log health

Dashboard-only styling lives at the end of `app/statics/css/style.css` under the dashboard command center section. Keep new dashboard classes prefixed with `dash-` when possible so future UI changes stay scoped to the dashboard page.
