# Roadmap

Committed doc, not scratch. Kept current by hand as work ships.
**Shipped** = live in production. **Next** = intended, not promised.
**Declined** = decided against, with the reason, so it doesn't get re-proposed.
**Open questions** = unresolved calls, with what would settle them.

## Shipped

- **2026-09** **`ASTP001`'s password reset, the last legacy hash retired.** The row held a
  128-character hex string — a SHA-512 digest from before the app moved to bcrypt, never migrated,
  which is why it could not authenticate on any stack. Replaced with a bcrypt hash of a freshly
  generated password; the account belongs to a third party, so the password was handed to Esther
  rather than mailed anywhere. Verified against production: `/api/login` returns a JWT for the new
  password and 401 for both a junk password and the old hex value. The other four `cp_user` rows
  were already bcrypt (60 characters), so no legacy hashes remain.

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

## Declined

- **Re-keying the 18 `drawing_id`s that no longer reproduce from their own stored PNG.** Accepted
  as-is 2026-09-06. Settled first that this is not a bug in the code: Pillow 8.0.0 and 11.3.0
  produce byte-identical hashes for all 50 live drawings (0 differences), the hash block is
  unchanged since `5392bc5` apart from `Image.ANTIALIAS` → `Image.Resampling.LANCZOS` which is the
  same filter, Python 2 floor division of the mean reproduces fewer ids (24/50) rather than more,
  and no drawing carries a fully transparent pixel with non-zero RGB. Every drift is instead a
  knife-edge tie — the flipped pixel sits within 0.5 grey levels of the mean (median 0.26, against
  1.12 for ids that do reproduce) — and nine drawings of the same 2017-18 era are just as fragile
  and still reproduce, which rules out any global cause. The object in S3 is simply not
  byte-identical to the payload hashed when the id was minted; all 18 predate 2022 and all four
  drawings created 2024-2026 reproduce.
  **Why it is not worth fixing:** the only consequence is that re-submitting one of those 18
  drawings mints a new row instead of returning 409. The fix would be a migration across the
  `drawing` primary key, the `drawing_like` foreign key and the S3 object names, to restore
  duplicate detection for 18 drawings from 2018. The average hash stays what it is — a similarity
  score unique enough to serve as a key, not an identifier derived from the bytes it names.

## Open questions

_Nothing outstanding._
