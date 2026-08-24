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

- Branding strings that do NOT go through the `translate()` substitution path
  (and therefore don't auto-rebrand at runtime) were changed by hand:
  - `flutter/lib/desktop/widgets/tabbar_widget.dart`: the custom in-app
    title-bar `Text("RustDesk")` → `"BCS Beam"`.
  - `flutter/windows/runner/main.cpp`: the native window-title fallback.
  - `flutter/windows/runner/Runner.rc`: Windows file-properties metadata
    (CompanyName → Brocent, ProductName → BCS Beam, etc.; `LegalCopyright`
    keeps the RustDesk/Purslane AGPL attribution).

- Installer packaging (`res/msi/`):
  - `preprocess.py`: added a `--product-name` argument (defaults to
    `--app-name`, so upstream behavior is unchanged when omitted) that
    decouples the user-visible display name from the exe filename. Needed
    because upstream overloads `--app-name` as both the exe basename — which
    it shells out to UNQUOTED, so a space breaks it — and every display
    string. We pass `--app-name BCSBeamRemote` (space-free filename) +
    `--product-name "BCS Beam"` (spaced display).
  - `res/msi/Package/Resources/WixUIDialogBmp.bmp` + `WixUIBannerBmp.bmp`:
    BCS Beam wizard artwork (this dir is `.gitignore`d upstream, so these are
    force-added). Without them the installer wizard falls back to the stock
    art.

- Icon/logo assets under `res/` and
  `flutter/windows/runner/resources/app_icon.ico` replaced with BCS Beam
  artwork per the approved v1.3 brand system (see below).

The `APP_NAME` change alone
propagates the rebrand through the UI via RustDesk's own existing
`is_rustdesk()`/`get_app_name()` mechanism (`src/common.rs`, `src/lang.rs`):
every UI string containing the literal word "RustDesk" is automatically
substituted with our app name at translation time, **except** the
`powered_by_me` string ("Powered by RustDesk") and the
`upgrade_rustdesk_server_pro` prompt, which upstream deliberately excludes
from substitution — we did not need to touch this logic to keep the
attribution visible.

- Icon/logo assets replaced with BCS Beam artwork per the approved brand
  system (v1.3, wordmark-only — no graphic logo; the "B" monogram tile is
  used solely where the full wordmark can't physically fit):
  `res/icon.ico`, `res/icon.png`, `res/mac-icon.png`, `res/128x128.png`,
  `res/128x128@2x.png`, `res/32x32.png`, `res/64x64.png` — the steel-gradient
  "B" tile (`linear-gradient(180deg, #1a7af0, #0d3766)`, 22% corner radius,
  weight-800 system-stack font). `res/tray-icon.ico` — the line-frame "B"
  tile variant (transparent background, 2px outline) for the system tray.
  `res/logo.svg`/`res/logo-header.svg` — the "BCS Beam" wordmark (BCS in
  `#69b7ff` tint, BEAM in white, weight 800, 800 tracking) on the brand navy
  (`#081c33`); these two are only used in this repo's own README, not
  compiled into the client. `res/mac-tray-dark-x2.png`/`mac-tray-light-x2.png`
  are unchanged (macOS isn't a build target here yet).

## Not changed

Remote-control protocol, encryption/security model, permission/consent
handling, or any other functional behavior. This fork exists solely to point
the client at our own server and to reflect our own brand name in the UI —
it is not a security-relevant fork and should be kept in sync with upstream
RustDesk releases for security fixes.
