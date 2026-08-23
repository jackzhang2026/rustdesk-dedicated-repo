# Modifications from upstream RustDesk

This file lists every substantive change made in this fork, per good-practice
disclosure for a copyleft (AGPL-3.0) derivative work. Based on
[rustdesk/rustdesk](https://github.com/rustdesk/rustdesk) tag `1.3.9`
(commit `3dbe27ea57429cf2b57cbae3b894a9f9a88ff8b5`), with
[rustdesk/hbb_common](https://github.com/rustdesk/hbb_common) (commit
`81b932b7bfa2ff8bc60189625fd6538db2fa9ea1`) flattened in as regular tracked
files (it was a git submodule upstream; kept as ordinary files here so a
plain clone of this repo gets the complete corresponding source in one step,
per AGPL-3.0's source-availability requirement).

## Changes

- `libs/hbb_common/src/config.rs`:
  - `APP_NAME` default changed from `"RustDesk"` to `"BCS Beam"`.
  - `RENDEZVOUS_SERVERS` changed from RustDesk's public server
    (`rs-ny.rustdesk.com`) to our own self-hosted server
    (`beam-relay.centoffer.com`).
  - `RS_PUB_KEY` changed to our own self-hosted server's public key.

That's it — no other source files are modified. The `APP_NAME` change alone
propagates the rebrand through the UI via RustDesk's own existing
`is_rustdesk()`/`get_app_name()` mechanism (`src/common.rs`, `src/lang.rs`):
every UI string containing the literal word "RustDesk" is automatically
substituted with our app name at translation time, **except** the
`powered_by_me` string ("Powered by RustDesk") and the
`upgrade_rustdesk_server_pro` prompt, which upstream deliberately excludes
from substitution — we did not need to touch this logic to keep the
attribution visible.

Icon/logo assets (`res/icon.ico`, `res/tray-icon.ico`, `res/icon.png`,
`res/logo.svg`, `res/logo-header.svg`) are pending replacement with BCS Beam
artwork — not yet done as of this NOTICE's date.

## Not changed

Remote-control protocol, encryption/security model, permission/consent
handling, or any other functional behavior. This fork exists solely to point
the client at our own server and to reflect our own brand name in the UI —
it is not a security-relevant fork and should be kept in sync with upstream
RustDesk releases for security fixes.
