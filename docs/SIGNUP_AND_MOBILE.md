# Email signup and mobile composer update

## Signup

New signups require `username`, `email`, and `password`; `name` remains optional.
Login is still by username/password. Existing accounts without email continue
working, and are not forced through signup again.

Email syntax is checked server-side with `email-validator`, with matching HTML
email-input validation in the signup form. Surrounding whitespace is removed,
the domain is normalized, and addresses are case-folded for this application's
case-insensitive uniqueness policy. Plus-addressing is retained. DNS checks are
not performed during signup, so registration does not depend on DNS availability.
A database unique index prevents duplicate registrations even when requests race.

**This is not inbox verification:** no verification email is sent, and an accepted
address is not proof of mailbox ownership or deliverability. Confirmation links,
expiry/resend handling and verified-account permissions require a separate email
provider integration. Do not describe current accounts as email-verified.

The password minimum is 8 characters for new users. Passwords above bcrypt's
72-byte UTF-8 limit are rejected rather than silently truncated. Legacy login
rules are preserved.

## Existing database upgrade

On startup the storage layer adds a nullable `users.email` column if missing and
creates its unique index. Existing rows retain their data and receive NULL email;
multiple legacy accounts may have NULL. The upgrade is repeatable and tested
against a database with the old schema. It does not delete/recreate the users table.

Back up the database before deployment using your verified backup process. Stop
old app instances and run the first upgraded startup with a single app instance.
The lightweight startup migration is not designed for simultaneous schema changes
by multiple replicas. Existing SQLite installations require no manual SQL change.

```bash
docker compose down
docker compose up --build -d
docker compose logs --tail=100 chatbot
```

Do not delete `data/` to upgrade. A read-only database cannot perform this migration;
start the writable app before any read-only consumers such as backups.

## Mobile chat input

The app previously used `100vh` inside a non-scrollable page. On mobile, that can
extend behind browser controls or the software keyboard. The composer also needed
explicit non-shrinking flex behavior and a zero minimum width on its textarea.

The app now uses dynamic viewport sizing, with a small `visualViewport` listener
for keyboard/visible-height changes. Only the conversation area scrolls. Safe-area
padding protects the input from phone home indicators. Pinch zoom is not disabled.
The signup form is also scrollable on short screens.

## Tests

```bash
python -m pip install -r requirements-dev.txt
JWT_SECRET=this-is-a-test-secret-that-is-32-chars-long \
NVIDIA_API_KEY=dummy python -m pytest tests/ -q
node --test tests/test_viewport.cjs tests/test_voice_frontend.cjs
```

Optional browser smoke test (requires a locally installed Chromium and Node):

```bash
npm install --prefix .cache/mobile-check --no-audit --no-fund playwright-core
NODE_PATH="$PWD/.cache/mobile-check/node_modules" \
CHROMIUM_EXECUTABLE_PATH=/path/to/chromium node tests/test_mobile_browser.cjs
```

The browser check uses real app HTML/CSS/JS with mocked API responses. It checks
email validation, signup payload/errors, login-mode behavior, and composer bounds
at 320/375/390px phone widths, landscape, reduced viewport height and desktop.
This is not a physical iOS/Android keyboard test. Manually verify typing, keyboard
opening/closing, rotation, long conversations, and returning from lesson/tool views
on target devices. The viewport unit tests cover resize, offset, pinch zoom and
older-browser fallback behavior.
