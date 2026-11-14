# NEU Career – Admin/Moderator UI

The staff interface uses the Vue Notus dashboard as a visual reference, adapted to the project's existing Flask + Jinja2 + CSS + JavaScript stack. No Vue build step or new Python dependency is required.

## Run

1. Run `run.cmd` from the project root. It creates the virtual environment if needed,
   installs dependencies when Flask is missing, initializes the database, and starts the server.
2. Open `http://127.0.0.1:5000/admin/login` and sign in with an Admin or Moderator account.

## Staff pages

- `/admin/` – Dashboard
- `/admin/companies` – pending company review
- `/admin/jobs` – pending job review
- `/admin/history` – review history
- `/admin/categories` – category list; create/edit/delete are Admin-only
- `/admin/contents` – career content management
- `/admin/users` – account management (Admin-only)

The pages call the existing `/api/admin/*` endpoints. Backend authorization remains authoritative; hiding a menu item in the browser is not used as a security control.

## Files added/changed

- Added `backend/app/admin/pages.py` for HTML page routes, separate from the JSON API blueprint.
- Updated `backend/app/__init__.py` to register the page blueprint at `/admin`.
- Added templates under `frontend/templates/admin/`.
- Added `frontend/static/css/admin.css` and `frontend/static/js/admin.js`.

The existing Admin API routes and other team modules were not intentionally changed.


## Dashboard overview API

- `GET /api/admin/dashboard/summary` – Admin/Moderator only.
- Returns aggregate counts from SQLite and the latest 8 moderation decisions.
- The dashboard uses this endpoint for metrics and recent activity; it does not use hard-coded sample counts.
- The active-job count excludes expired jobs and jobs whose company or business account is not approved/active.
