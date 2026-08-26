# BCS Beam — Branding Kit (for the macOS build)

Assembled 2026-08-26 from the Windows build machine's repo state (the one that
produced the validated Windows MSIs), for whoever is doing the macOS RustDesk
rebrand. Everything the Windows build actually ships is here, plus two newly
generated Mac tray icons (see the ⚠️ note below — the repo's own Mac tray files
were still stock RustDesk).

Companion doc: `HANDOFF_MACOS_BUILD.md` (same directory level in
`beam-remote-client/`) — the full macOS build plan, including which macOS files
still carry upstream RustDesk identifiers (`com.carriez.rustdesk` bundle id,
hardcoded "RustDesk.app" in `build.py`, etc). Read that first; this kit is the
asset half of that job.

---

## 1. Names & text strings (the exact values the Windows build uses)

| What | Value | Where it lives in code |
|---|---|---|
| Display / product name | `BCS Beam` | compiled default in `libs/hbb_common/src/config.rs` (`APP_NAME`) — cross-platform, already correct for Mac builds from this repo |
| Technical name (Windows) | `BCSBeamRemote` | exe filename, service name, registry keys. **macOS equivalent decision**: `src/platform/macos.rs` checks `/Applications/{APP_NAME}.app`, i.e. the `.app` bundle must literally be **`BCS Beam.app`** (spaced display name, NOT BCSBeamRemote) or install detection breaks — see HANDOFF_MACOS_BUILD.md §3.4 |
| Company legal name | `BROCENT CLOUD SERVICE CO., LTD (BCS TEAM)` | EULA legal-entity line, About-page copyright, License Statement page |
| Manufacturer (short) | `Brocent` | installer Publisher fields |
| Company URL | `https://www.brocent.com` | License Statement page link |
| Rendezvous/relay server | `beam-relay.centoffer.com` | compiled into `libs/hbb_common/src/config.rs` — cross-platform, nothing to do for Mac |
| Update-check endpoint | `https://update.centoffer.com` | compiled in (self-hosted update server) |
| "Powered by RustDesk" | **deliberately preserved** | repo `README.md` explains the policy — do NOT strip it on Mac either. On Windows desktop it was moved into a "License Statement" page (bottom-left sidebar link); mobile still shows it as-is |
| Sidebar wordmark subtitle | `BROCENT CLOUD SERVICE` | baked into the wordmark images |

## 2. Colors

| Color | Hex | Used for |
|---|---|---|
| Brand blue | `#1890ff` | "BCS" text in light-mode wordmark, accent underline |
| Light blue | `#69b7ff` | "BCS" text on dark/navy backgrounds (see `logo.svg`) |
| Navy | `#081c33` | "BEAM" text in light mode; dark background in `logo.svg` |
| Near-white | `#f0f5fa` | "BEAM" text in dark mode (`logo-dark-mode.png`) |
| App-icon gradient | `#1976e8` → `#0d3b6e` (top→bottom, vertical) | the blue "B" badge icon background |

Fonts: wordmark PNGs were rendered with **Segoe UI Bold** (a Windows font).
The SVG sources declare a stack (`Liberation Sans, -apple-system, 'Segoe UI',
Arial`). If you regenerate on macOS, Helvetica Neue Bold / SF Pro Bold are the
natural substitutes — or just use the shipped PNGs/SVGs as-is (preferred; don't
introduce a subtly different wordmark). The generator scripts are in
`wordmark/generators/` so the exact layout math is reproducible.

## 3. Asset inventory & what each maps to on macOS

### icons/
| File | Size | Windows role | macOS role |
|---|---|---|---|
| `mac-icon-1024.png` | 1024² | — | **source for the `.icns`** (`iconutil`/`makeicns` from this) and `Assets.xcassets/AppIcon.appiconset`. Was already rebranded in-repo (`res/mac-icon.png`) |
| `icon-1024.png` | 1024² | master icon | same design, identical to mac-icon |
| `icon-multi-size-windows.ico` | 16-128 multi | window/taskbar icon | reference only |
| `icon-32/64/128/256.png` | as named | Linux/misc sizes | handy pre-scaled sizes for the iconset |
| `titlebar-icon-128.png` | 128² | in-app titlebar glyph (`flutter/assets/icon.png`) | same file works — it's a Flutter asset, cross-platform. Already in the repo |
| `tray-icon-windows.ico` | 32² | Windows system tray | design reference for the Mac tray glyphs |
| `mac-tray-dark-x2.png` | 60² | — | **menu-bar icon, black glyph** (for light menu bar). ⚠️ NEWLY GENERATED — see note below |
| `mac-tray-light-x2.png` | 48² | — | **menu-bar icon, white glyph** (for dark menu bar). ⚠️ NEWLY GENERATED |

**⚠️ Mac tray icons**: the repo's own `res/mac-tray-dark-x2.png` /
`res/mac-tray-light-x2.png` are **still the stock RustDesk swirl** — the earlier
branding phase missed them (verified visually 2026-08-26). The two files in this
kit are drop-in replacements at the exact same pixel sizes, matching the approved
Windows tray design (bold "B" in a rounded-square outline, monochrome). **They
have NOT been committed to the repo yet** — copy them over `res/mac-tray-*.png`
in your working tree as part of the Mac branding pass, and commit them there.

### wordmark/
| File | What |
|---|---|
| `logo.svg`, `logo-header.svg` | source-of-truth wordmark design (dark-navy background variant, used in repo README) |
| `logo-light-mode.png` | 480×132, transparent bg, for light UI (`flutter/assets/logo.png` — sidebar) |
| `logo-dark-mode.png` | 480×132, transparent bg, "BEAM" near-white for dark UI (`flutter/assets/logo_dark.png`) |
| `generators/*.py` | Pillow scripts that produced the PNGs + the Mac tray glyphs (need a Windows font path as written — adjust if rerunning on macOS) |

Both wordmark PNGs are already wired into the shared Flutter code
(`loadLogo()` in `flutter/lib/common.dart`, theme-aware) — a Mac build from
current source gets the sidebar wordmark for free; nothing to re-plumb.

### installer-art/
`WixUIBannerBmp.bmp` (493×58) and `WixUIDialogBmp.bmp` (493×312) — the Windows
MSI wizard artwork. macOS has no direct equivalent, but if you style the DMG
background image, these are the approved look to match.

## 4. What's already cross-platform (do NOT redo for Mac)

Because these live in shared Rust/Flutter code, a Mac build from this repo
already gets them: display name "BCS Beam" everywhere in-app, the rendezvous
server, sidebar wordmark (light+dark), titlebar icon, License Statement page +
bottom-left link, About-page copyright with the full legal name, EULA-equivalent
in-app text. The Mac-specific work is only: `.icns` + `AppIcon.appiconset`, the
two tray PNGs above, bundle name/identifier (`BCS Beam.app`, pick a
`com.brocent.*` bundle id), `build.py`'s hardcoded "RustDesk.app"/"RustDesk
Installer" strings, and DMG packaging cosmetics. Full list with file paths:
`HANDOFF_MACOS_BUILD.md`.
