# CrossRecord backend

Flask API for records, friendships, challenges and feeds. The API is versioned at `/api/v1`. This version starts with a new MongoDB database; it does not import or modify the old SQLite database.

## Project structure

- `src/app.py` creates the Flask application and configures MongoDB.
- `src/api.py` assembles feature blueprints and API error handlers.
- `src/db/routes/` contains separate route modules for authentication, users, follows, exercises, variations, records, statistics, challenges and feeds.
- `src/db/services/` contains shared user/privacy, record and challenge rules; `src/db/common.py` and `src/db/connection.py` provide validation, serialization and MongoDB setup.

The three exercise categories use the same record and challenge endpoints, with category-specific rules in the services. No SQLAlchemy models are used.

## Run locally

Install Python 3.12, Pipenv, MongoDB Community Server and `mongosh`. MongoDB must run as a replica set, even locally: completing a challenge uses a multi-document transaction.

### Local database and seed data

The repository includes Windows/PowerShell commands for a separate local database. It listens only on `127.0.0.1`, uses the replica set `rs0`, and stores its files in `%LOCALAPPDATA%\CrossRecord\mongodb`; it never uses or changes Atlas.

Install GNU Make if you want to use `make` targets. Then:

```powershell
make mongo-up
make mongo-status
make seed-catalog
$env:CROSSRECORD_LOCAL_ROBERT_PASSWORD = '<choose a local password>'
make seed
```

`make seed` creates/promotes the local `robert` premium account and adds the CrossFit catalog plus the repeatable demo dataset. It uses the database `crossrecord_local` and is safe to run again. `make mongo-down` stops only the MongoDB process started by this repository. Without GNU Make, invoke the same PowerShell scripts directly:

```powershell
.\scripts\local_mongo.ps1 -Action up
$env:CROSSRECORD_LOCAL_ROBERT_PASSWORD = '<choose a local password>'
.\scripts\seed_local.ps1 -Action all
```

```powershell
pipenv install --dev
pipenv run python run_server.py
```

`run_server.py` loads the ignored `.env.local` file automatically. It is already configured for the local MongoDB URI and `crossrecord_local`; do not point it at Atlas. It listens on port 5000 over the local network so an Expo app on a physical phone can reach it. To test real email locally, add a separate development Resend key and a verified sender to that file. Vercel uses its own environment variables and never reads `.env.local`.

For MongoDB Compass, use `mongodb://127.0.0.1:27017/?replicaSet=rs0` and select the `crossrecord_local` database. Compass connects to MongoDB; the mobile app connects to the Flask API instead. A physical device must use `http://<your-PC-LAN-IP>:5000/api/v1` as its development API URL (not `localhost`). Android Emulator uses `http://10.0.2.2:5000/api/v1`; iOS Simulator may use `http://127.0.0.1:5000/api/v1`.

Use a managed replica set and credentials in production. Configure `JWT_SECRET_KEY` through a secret manager; the application refuses to start without it. Indexes are created at startup. The application does not create initial administrators or premium accounts from client input: provision `is_admin` and `premium` through a trusted database administration process. Payment verification and advertising SDKs are not included. Existing accounts default to free and non-admin.

Set `RESEND_API_KEY` as a Vercel Secret, never in a committed file. `MAIL_FROM` must use a verified Resend domain. One-time account tokens are stored only as hashes and expire after one hour.

## API conventions

Requests and responses are JSON. Authenticated endpoints require `Authorization: Bearer <access_token>`. IDs are MongoDB ObjectId strings. Dates are ISO 8601 with timezone; the server stores UTC. Errors return `{"error": "..."}` and an appropriate HTTP status. Pagination uses `limit` (1–50) and `offset`; responses with `next_offset` set to null have no further page. New records default to private. Values are positive: repetitions are integers, weighted values are kilograms with up to two decimal places, and cardio values are integer seconds at a specified `distance_m` (metres, up to two decimals). Cardio comparisons always use the same variation and distance.

| Method and path | Purpose |
| --- | --- |
| `POST /auth/register` | `email`, `password` (at least 8 characters), `username`, `name`, `last_name`; optional `weight`, `profile_private`. Returns user and access token. |
| `POST /auth/login` | `email`, `password`; returns user and access token. |
| `POST /auth/verify-email/request`, `/confirm` | Send a one-hour verification link and consume its one-time token. Unverified users may log in and inspect `/me`, but cannot use application features. |
| `POST /auth/password-reset/request`, `/confirm` | Request a one-hour reset link and consume it with a new password. The request response does not reveal whether an email exists. |
| `GET/PATCH /me` | Own account; PATCH accepts `name`, `last_name`, `username`, `weight`, `profile_picture`, `profile_private`. Returns `premium` and `show_ads`. |
| `GET /users?q=...` and `GET /users/{id}` | Search username prefixes and inspect public profile and visible best records. |
| `POST/DELETE /users/{id}/follow` | Follow/unfollow. Mutual following constitutes friendship. |
| `GET /me/following`, `/me/followers`, `/me/friends` | List relationships. |
| `GET /exercises?kind=...`, `GET /exercises/{id}/variations` | Browse the catalog. Kinds: `calisthenic`, `weighted`, `cardio`. |
| `POST /exercises`, `POST /exercises/{id}/variations` | Administrator-only catalog creation; exercise takes `name`, `kind`; variation takes `name`. |
| `POST /records` | `variation_id`, `value`, optional `performed_at` and `is_private`; cardio requires `distance_m`. When a result reaches an active challenge, submit `challenge_id`, the `challenge_target` observed in the preview, and `challenge_decision` (`complete` or `cancel`). |
| `POST /records/preview` / `POST /records/{id}/preview` | Preview a new or edited value and return an eligible active challenge, if any. The server revalidates the challenge and target on save. |
| `PATCH /records/{id}/visibility` | Owner changes `is_private`. |
| `PATCH /records/{id}` / `DELETE /records/{id}` | Correct `value`, `performed_at` or `is_private`, or delete a record. Free accounts can change only their three most recent records in the variation and distance. A correction reaching an active challenge requires the same decision fields as creation. Requires MongoDB transactions. |
| `GET /me/records` | Free: requires `variation_id` and returns the newest three for that variation and `has_more_locked`; cardio also requires `distance_m`. Premium: full paginated history, optionally filtered by variation and distance. |
| `GET /me/statistics?variation_id=...` | Premium-only series, best, first and last values, and absolute and percentage improvement; cardio also requires `distance_m`, and a decrease in time is a positive improvement. |
| `GET /challenges/options?user_id=...&variation_id=...` | Returns baseline and allowed `min`, `max`, `step`; cardio requires `distance_m`. |
| `POST /challenges` | `user_id` (recipient), `variation_id`, `target`, optional `message`; cardio requires `distance_m`. |
| `GET /challenges` | Paginated sent and received challenges. |
| `POST /challenges/{id}/accept`, `/reject`, `/cancel` | Recipient accepts/rejects; sender cancels. Active challenges expire after seven days. |
| `POST /challenges/{id}/complete` | Recipient submits actual `value`, optional `performed_at`, `is_private`; cardio requires matching `distance_m`. The record and completion commit atomically. |
| `GET /me/notifications` / `POST /me/notifications/{id}/read` | List internal notifications and mark one as read. |
| `DELETE /me` | Temporarily deactivate the account; signing in reactivates it and old access tokens remain invalid. |
| `GET /feed/following`, `/feed/global` | Paginated shared personal-best activity, ordered by original creation time. Free accounts see their own three latest published personal bests per variation and cardio distance; other users' visible posts are not limited by this rule. |

Records on a public profile can be seen by authenticated users when shared; on a private profile, shared records are visible to mutual friends. Individually private records remain visible only to the owner. The global feed contains public-profile records only; following feed checks friendship at read time. Profiles show current best records, including older best records for free users. New records cannot be dated earlier than the latest record in the same variation and cardio distance. Challenges require a visible overall best and mutual following at creation; only one active challenge per recipient, variation and distance is allowed. The API reports a bounded target range rather than producing an unbounded array of options. Weighted targets use 0.01 kg steps; cardio uses seconds. Calisthenics rounds the maximum increase up only if its fractional part is at least 0.65.

Feed pagination uses offsets and may shift when new activity arrives. Feed items are ordered by their original creation time; this is not a personalized recommendation system. Profile photos are external references; uploading media is outside this backend.

## Tests

```powershell
pipenv run python -m pytest
$env:TEST_MONGO_URI = 'mongodb://localhost:27017/?replicaSet=rs0'
pipenv run python -m pytest
```

Without `TEST_MONGO_URI`, integration tests are skipped because record and challenge writes require transactions. With it, tests create a uniquely named temporary database on the specified MongoDB server and drop that test database afterward; use a dedicated test server. Never point tests at a production server.
