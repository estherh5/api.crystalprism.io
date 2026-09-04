# Roadmap

Committed doc, not scratch. Kept current by hand as work ships.
**Shipped** = live in production. **Next** = intended, not promised.
**Declined** = decided against, with the reason, so it doesn't get re-proposed.
**Open questions** = unresolved calls, with what would settle them.

## Shipped

- **2026-09** **Heroku decommissioned.** The `crystalprism` app and its add-ons were destroyed on
  2026-09-04 after three days of parallel running with zero real traffic. A final pre-destroy dump
  was taken and row-matched against Neon on every table before deletion. One Heroku scheduler job died with the app: `management.py backup_db`, superseded by
  `~/blob-backups` step 2b, which dumps the Neon database nightly and is restore-verified.

- **2026-09** **Off Heroku onto Vercel, with the Postgres database on Neon.** `api.crystalprism.io`
  now resolves to a Vercel deployment instead of CNAME'ing to a legacy `herokuapp` hostname that
  had no certificate covering it. The database moved to the Neon project `old-sun-58330819`
  (PostgreSQL 18) with no SQL rewritten. `crystalprism.io`'s `common.js` points at the new base
  URL, and the frontend was held back from deploying until all four API subdomains served over
  HTTPS. Nightly logical dumps now run via `~/blob-backups`
  (`backup.sh` step 2b → `pg/crystalprism.sql`), restore-verified end to end.

## Next

- **`user.user` returns a 500, not a 401, for one account whose password hash is malformed.**
  The `cp_user` row `ASTP001` (created 2017-11-06, `status = active`) holds a 128-character hex
  string where the other four rows hold a `$2b$` bcrypt hash. `user.user` calls
  `bcrypt.checkpw` with no `try`/`except`, so bcrypt raises `ValueError: invalid salt` and the
  request becomes an uncaught 500. That account cannot authenticate on any stack.
  **Pre-existing, not caused by the migration** — verified as an identical 500 on live Heroku,
  with `admin` plus a junk password returning 401 on both as the control. The fix is to catch
  `ValueError` around the `checkpw` call and answer 401, which is what a credential that cannot
  possibly match means; separately decide whether that row should be reset or retired.

- **`user.update_user` does not re-apply the username regex that `create_user` enforces.**
  `create_user` validates usernames against `^[a-zA-Z0-9_-]+$`; `update_user` does not, so a
  PATCH can set a non-ASCII username that the create path would have rejected. Pre-existing.
  Extract the pattern to one constant and apply it on both paths.

- **The `drawing_id` perceptual hash is sensitive to the Pillow version, via `convert('L')`.**
  In `canvashare.create_drawing` and `management.create_drawings`, the version-sensitive step is
  `convert('L')` — not `resize()`, which is where this was first assumed to be. It shifts mode-P
  (palette) PNGs by ±1 per pixel and flips a hash bit, so the same drawing can mint a different
  key across Pillow versions. Unreachable from the real client, because the canvas
  `toDataURL` always emits RGBA; but `create_drawing` validates only that
  `'data:image/png;base64'` appears in the payload, so a hand-crafted palette PNG reaches it.
  Either normalise the mode before converting, or tighten the payload check.

## Open questions

- Should `ASTP001` be reset, retired, or left as-is once `user.user` stops 500ing? It has been
  unauthenticatable since at least the Heroku era and nothing depends on it logging in.
