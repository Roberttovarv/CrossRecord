# CrossRecord backend

Flask API for records, friendships, challenges and feeds. The API is versioned at `/api/v1`. This version starts with a new MongoDB database; it does not import or modify the old SQLite database.

## Project structure

- `src/app.py` creates the Flask application and configures MongoDB.
- `src/api.py` assembles feature blueprints and API error handlers.
- `src/db/routes/` contains separate route modules for authentication, users, follows, exercises, variations, records, statistics, challenges and feeds.
- `src/db/services/` contains shared user/privacy, record and challenge rules; `src/db/common.py` and `src/db/connection.py` provide validation, serialization and MongoDB setup.

The three exercise categories use the same record and challenge endpoints, with category-specific rules in the services. No SQLAlchemy models are used.

## Run locally

Install Python 3.12, Pipenv, MongoDB and `mongosh`. MongoDB must run as a replica set, even locally: completing a challenge uses a multi-document transaction. For example, start `mongod` with `--replSet rs0` and an existing data directory, then run `rs.initiate()` in `mongosh`. Wait for the primary to become available.

```powershell
pipenv install --dev
$env:MONGO_URI = 'mongodb://localhost:27017/?replicaSet=rs0'
$env:MONGO_DATABASE = 'crossrecord'
$env:JWT_SECRET_KEY = '<a long random secret>'
pipenv run python run_server.py
```

Use a managed replica set and credentials in production. Configure `JWT_SECRET_KEY` through a secret manager; the application refuses to start without it. Indexes are created at startup. The application does not create initial administrators or premium accounts from client input: provision `is_admin` and `premium` through a trusted database administration process. Payment verification and advertising SDKs are not included. Existing accounts default to free and non-admin.

## API conventions

Requests and responses are JSON. Authenticated endpoints require `Authorization: Bearer <access_token>`. IDs are MongoDB ObjectId strings. Dates are ISO 8601 with timezone; the server stores UTC. Errors return `{"error": "..."}` and an appropriate HTTP status. Pagination uses `limit` (1–50) and `offset`; responses with `next_offset` set to null have no further page. New records default to private. Values are positive: repetitions are integers, weighted values are kilograms with up to two decimal places, and cardio values are integer seconds at a specified `distance_m` (metres, up to two decimals). Cardio comparisons always use the same variation and distance.

| Method and path | Purpose |
| --- | --- |
| `POST /auth/register` | `email`, `password` (at least 8 characters), `username`, `name`, `last_name`; optional `weight`, `profile_private`. Returns user and access token. |
| `POST /auth/login` | `email`, `password`; returns user and access token. |
| `GET/PATCH /me` | Own account; PATCH accepts `name`, `last_name`, `username`, `weight`, `profile_picture`, `profile_private`. Returns `premium` and `show_ads`. |
| `GET /users?q=...` and `GET /users/{id}` | Search username prefixes and inspect public profile and visible best records. |
| `POST/DELETE /users/{id}/follow` | Follow/unfollow. Mutual following constitutes friendship. |
| `GET /me/following`, `/me/followers`, `/me/friends` | List relationships. |
| `GET /exercises?kind=...`, `GET /exercises/{id}/variations` | Browse the catalog. Kinds: `calisthenic`, `weighted`, `cardio`. |
| `POST /exercises`, `POST /exercises/{id}/variations` | Administrator-only catalog creation; exercise takes `name`, `kind`; variation takes `name`. |
| `POST /records` | `variation_id`, `value`, optional `performed_at` and `is_private`; cardio requires `distance_m`. |
| `PATCH /records/{id}/visibility` | Owner changes `is_private`. |
| `GET /me/records` | Free: newest three across all exercises and `has_more_locked`; premium: full paginated history. |
| `GET /me/statistics?variation_id=...` | Premium-only series and best; cardio also requires `distance_m`. |
| `GET /challenges/options?user_id=...&variation_id=...` | Returns baseline and allowed `min`, `max`, `step`; cardio requires `distance_m`. |
| `POST /challenges` | `user_id` (recipient), `variation_id`, `target`, optional `message`; cardio requires `distance_m`. |
| `GET /challenges` | Paginated sent and received challenges. |
| `POST /challenges/{id}/accept`, `/reject`, `/cancel` | Recipient accepts/rejects; sender cancels. Active challenges expire after seven days. |
| `POST /challenges/{id}/complete` | Recipient submits actual `value`, optional `performed_at`, `is_private`; cardio requires matching `distance_m`. The record and completion commit atomically. |
| `GET /feed/following`, `/feed/global` | Paginated shared personal-best activity. Global uses recent batches diversified by user and exercise. |

Records on a public profile can be seen by authenticated users when shared; on a private profile, shared records are visible to mutual friends. Individually private records remain visible only to the owner. The global feed contains public-profile records only; following feed checks friendship at read time. Profiles show current best records; when viewing their own profile, free users only receive best records that are among their three most recent entries, so the profile cannot bypass the history limit. Challenges require a visible overall best and mutual following at creation; only one active challenge per recipient, variation and distance is allowed. The API reports a bounded target range rather than producing an unbounded array of options. Weighted targets use 0.01 kg steps; cardio uses seconds. Calisthenics rounds the maximum increase up only if its fractional part is at least 0.65.

Feed pagination uses offsets and may shift when new activity arrives. Ranking is intentionally simple and not a personalized recommendation system. Profile photos are external references; uploading media is outside this backend.

## Tests

```powershell
pipenv run python -m pytest
$env:TEST_MONGO_URI = 'mongodb://localhost:27017/?replicaSet=rs0'
pipenv run python -m pytest
```

Without `TEST_MONGO_URI`, tests use an in-memory MongoDB substitute and skip transactional completion. With it, tests create a uniquely named temporary database on the specified MongoDB server and drop that test database afterward; use a dedicated test server. The second run exercises actual transactions and indexes. Never point tests at a production server.
