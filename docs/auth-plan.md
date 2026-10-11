# Auth Plan

The step-by-step plan for adding login: one user signs in and manages several accounts, and the app looks as it does today. Why it is built this way: [[05-decisions]] #69. Moves to `docs/archive/` when the work is done.

## 1. Target

- Before login: a login screen, nothing else.
- After login: the app as today. The sidebar lists the signed-in user's accounts and their projects; switching between accounts works as now.
- A user owns accounts; projects and saved trees already belong to an account (`account_id`), so they follow it.
- Every `/api/*` request except login needs a valid session and may only touch the signed-in user's accounts, projects, and saved trees.

## 2. What exists today

- Accounts (`data/accounts.json`) and projects (`current.json`) already carry a stub `user_id`, always `DEFAULT_USER_ID = 1` (`backend/storage/paths.py`). Nothing reads it.
- No login: anyone who can reach `localhost:8000` can read and change everything.
- All routes go through `Handler` in `backend/api/requests_from_browser.py` (`do_GET()`, `_POST_ROUTES`).
- The browser remembers the active account in `localStorage` (`activeAccountId`).

## 3. Steps

One step per commit; each is read and approved before the next starts.

1. **Users store** — `backend/auth/users.py` and storage in `backend/storage/users_persistence.py`: `data/users.json` with `id`, `username`, `password_hash`, `created_at`. Passwords are hashed with `hashlib.scrypt` and a random salt; plain text is never stored. A command-line script creates a user (`python -m backend.auth.create_user`). The first user gets id `1`, so every existing account and project already belongs to them. Tests.
2. **Sessions** — `backend/auth/sessions.py`: create, look up, and end a session. A session is a random token (`secrets`) mapped to a user id and an expiry, stored in `data/sessions.json`. Tests.
3. **Login routes** — `POST /api/login`, `POST /api/logout`, `GET /api/me`. Login sets the token as a cookie (`HttpOnly`, `SameSite=Strict`, `Path=/`). Thin wiring in `requests_from_browser.py`; the logic stays in `backend/auth/`.
4. **Guard** — one check in `Handler` before every `/api/*` route except login: no valid session gives `401`. The page files stay public, so the login screen can load.
5. **Ownership** — the API passes the signed-in user's id down. Accounts are listed and created per user; each project, account, and saved-tree route checks that it belongs to the user, else `404`. `DEFAULT_USER_ID` stops being the source of the owner.
6. **Login screen in the UI** — `app/ui/src/auth/`: a login form, a Log out item, and a redirect to login on any `401`. `activeAccountId` is cleared on logout.
7. **Docs** — update `04-current-state.md` and `03-architecture.md` (an auth step in front of the API), close the TODO item, move this file to `docs/archive/`.

## 4. Open questions

- **Registration** — only the command-line script at first, or a sign-up screen?
- **Session length** — how long a login lasts, and whether "remember me" is needed.
- **Password rules** — minimum length only, or more?
- **First login with no accounts** — show the empty sidebar as today, or create a first account automatically?

## 5. Out of scope

- Running the app over a network (HTTPS, other people's machines). That changes the privacy trade-off in [[05-decisions]] #5 and #15 and needs its own decision.
- Encrypting data at rest.
- Password reset, email, or third-party login.
