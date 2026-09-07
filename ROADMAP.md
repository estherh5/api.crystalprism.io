# Roadmap

Committed doc, not scratch. Kept current by hand as work ships.
**Shipped** = live in production. **Next** = intended, not promised.
**Declined** = decided against, with the reason, so it doesn't get re-proposed.
**Open questions** = unresolved calls, with what would settle them.

## Shipped

- **2026-09** **One username rule, applied on every path that sets a username.** `create_user`
  validated usernames against `^[a-zA-Z0-9_-]+$` and `update_user` did not, so a PATCH could set
  a name the create path would have rejected. The pattern is now the `USERNAME_PATTERN` constant
  in `user/user.py`, applied on both paths, and `update_user` also rejects a blank username with
  the same message `create_user` uses. Pre-existing. All five live `cp_user` rows were checked
  against the pattern first — every one passes, so no account lost the ability to update itself.

- **2026-09** **The `drawing_id` average hash no longer depends on the PNG's encoding mode.**
  `average_hash` now lives in `canvashare/hashing.py` and both `canvashare.create_drawing` and
  `management.create_drawings` call it, so the two paths cannot drift. It normalises the image to
  RGBA before resizing: Pillow silently ignores the resampling filter for palette (mode P) images
  and then converts them to grayscale through the palette, which drifts between Pillow releases
  and flips a hash bit. RGBA input — all the canvas `toDataURL` emits — hashes byte-identically
  before and after, verified across the fixture drawing and six synthetic canvases, so every
  existing drawing id stays valid. Pinned by `TestAverageHash`, including a flat literal for the
  fixture drawing's id.

- **2026-09** **`user.login` answers 401, not 500, for a malformed password hash.** The `cp_user`
  row `ASTP001` (created 2017-11-06, `status = active`) holds a 128-character hex string where
  every other row holds a `$2b$` bcrypt hash, so `bcrypt.checkpw` raised `ValueError: Invalid
  salt` and the request became an uncaught 500. `login` in `user/user.py` now catches
  `ValueError` and treats the credential as non-matching, which is what a hash no password can
  match means. Pre-existing, not caused by the Heroku→Vercel migration — it reproduced
  identically on live Heroku. Pinned by `TestLogin.test_login_get_malformed_hash_error`.

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

_Nothing outstanding._

## Open questions

- Should `ASTP001` be reset, retired, or left as-is? Its login now answers a clean 401 rather
  than 500ing, but the row still holds an unusable hash: it has been unauthenticatable since at
  least the Heroku era and nothing depends on it logging in. Settled by deciding whether the
  account is still wanted — reset the password if so, set `status` to deleted if not.
