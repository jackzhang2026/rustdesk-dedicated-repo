# BCS Beam (RustDesk fork) — macOS Build Handoff

## UPDATE 2026-08-27 — re: the "About page still says Purslane Ltd." finding

Your finding was correct **against the repo state you could see at the time** — and is
now resolved by a push, not a new fix. What happened:

- The About-page copyright (and a full License Statement page with the complete legal
  name, plus a dark-mode-aware sidebar wordmark, the titlebar icon, and several
  Windows-validated MSI/installer fixes) were fixed on the Windows build machine on
  2026-08-25 — but sat in **local-only commits** under the push-at-deploy-only policy.
  `origin/main` (`a4be460` at the time you searched) genuinely did not contain them.
- Jack approved a push on 2026-08-27: **`origin/main` is now `c6c0a3b`** and contains
  everything. **`git pull` before doing any branding work** — do not patch the About
  page yourself, it's done (`desktop_setting_page.dart` now has zero "Purslane").
- Your inference that already-shipped Windows MSIs carry the old text is **not the
  case**: the fix landed in the second-ever local build (2026-08-25 morning); every MSI
  since — including everything in `dist/` and everything Jack validated — has the full
  legal name. Nothing has shipped to customers at all yet (all builds unsigned,
  internal-testing only). No remediation needed.
- A full-repo sweep found two further "Purslane Ltd" stragglers: `src/main.rs`'s CLI
  `--help` author metadata (fixed in `c6c0a3b`) and `src/ui/index.tis:388` (legacy
  Sciter UI — **dead code for Flutter builds on every platform including macOS**, never
  compiled in; leave it).

---

**Status: NOT STARTED.** Nothing in this document has been attempted or verified — no
macOS machine has been touched in this project yet. This is a from-scratch plan derived
by reading this repo's own build scripts and CI recipe (`.github/workflows/flutter-build.yml`,
the `build-for-macOS` job — this file is the **unmodified upstream RustDesk workflow**,
still pinned to the original `rustdesk/rustdesk` project's own settings; unlike
`build-bcsbeam.yml` for Windows, nobody has trimmed/adapted it for Brocent yet) plus
inspection of `build.py` and `flutter/macos/`. Treat every command below as "should work
per the source, not yet proven" — expect to hit undocumented problems, the same way the
Windows effort did (see `HANDOFF_LOCAL_BUILD.md` in the repo root for how many
undocumented issues turned up there despite having a similar CI recipe to start from).

This document is the macOS sibling of `HANDOFF_LOCAL_BUILD.md` (repo root) — **read that
file too**, several of its landmines are Dart/Flutter/build-tooling issues that are not
Windows-specific and will likely recur here (flagged inline below where relevant).

---

## 0. The one thing to understand before starting: macOS branding has NOT been done

The Windows side went through two phases before this document existed: (1) an earlier
"branding phase" session that renamed the app, swapped icons, and pointed it at Brocent's
own rendezvous server across the whole codebase, and (2) the local-build phase (this
project) that got a working Windows installer out of it. **Only phase 1's *cross-platform*
parts (the shared Rust/Flutter source — `libs/hbb_common/src/config.rs`'s `APP_NAME`
default, the shared Flutter UI, the rendezvous server config) apply to macOS today.
Phase 1's Windows-*specific* branding work does not, and macOS's own equivalent has never
been done:**

- `flutter/macos/Runner.xcodeproj/project.pbxproj` still has
  `PRODUCT_BUNDLE_IDENTIFIER = com.carriez.rustdesk` — the **original upstream RustDesk**
  bundle identifier (`carriez` is upstream's author). Not Brocent's, not even genericized.
- `flutter/macos/Runner/Info.plist` — has not been checked/edited for `CFBundleName` /
  `CFBundleDisplayName` (need to verify current values and change to "BCS Beam").
- `build.py`'s macOS packaging code path (`~line 413-417`) **hardcodes `RustDesk.app`
  and `"RustDesk Installer"` literally** — it does not read any `--app-name`/`--product-name`
  flag at all (unlike the Windows path, which at least partially does). Building today, as-is,
  produces an app bundle and DMG both still named/labeled "RustDesk", regardless of what
  `APP_NAME` says at the Rust level.
- No `.icns` app icon file exists anywhere in the repo (`find . -iname "*.icns"` returns
  nothing) — macOS needs its own icon format, distinct from Windows' `.ico`
  (`res/icon.ico`, already Brocent-branded) and Linux's `.png`. Someone needs to generate
  one from the same source design (see `res/logo.svg`/`res/icon.ico` for the approved mark)
  and wire it into `flutter/macos/Runner/Assets.xcassets`.
- The custom rendezvous server (`beam-relay.centoffer.com`, baked into
  `libs/hbb_common/src/config.rs`'s `RENDEZVOUS_SERVERS` const) **is** shared/cross-platform
  code, so that part *should* just work on macOS without extra effort — but has never been
  tested there.

**Do not assume "port the Windows fixes" is the task.** The actual task is closer to
redoing the Windows project's *both* phases, for macOS, from a colder start.

---

## 1. Toolchain (per CI's `build-for-macOS` job — NOT locally verified)

| Component | Version | Notes |
|---|---|---|
| macOS | Ventura 13+ recommended (matches `macos-13`/`macos-latest` CI runners) | Apple Silicon (arm64) and Intel (x86_64) are both supported targets; pick based on target hardware, or build both |
| Xcode | latest matching the macOS version, + Command Line Tools | needed for `flutter build macos`, CocoaPods, codesigning |
| Rust | **1.81** (`MAC_RUST_VERSION` in `flutter-build.yml`) | **Different from Windows' 1.75.0** — macOS needs the newer version because a transitive dependency (`cidre`, via the [yury/cidre](https://github.com/yury/cidre) crate) requires it. Do not reuse the Windows Rust pin. |
| Rust target | `x86_64-apple-darwin` (Intel) or `aarch64-apple-darwin` (Apple Silicon) | `rustup target add <target>` |
| Flutter | 3.24.5 | same pin as Windows |
| LLVM/Clang | 15.0.6 | same pin as Windows; install via `brew install llvm` |
| vcpkg | commit `6f29f12e82a8293156836ad81cc9bf5af41fe836`, triplet `x64-osx` (Intel) or `arm64-osx` (Apple Silicon) | ⚠️ **this is the OLD/stale vcpkg commit that Windows's `build-bcsbeam.yml` had to override** (to `120deac3062162151622ca4860575a33844ba10b`) because of a dead msys2-runtime mirror — see `HANDOFF_LOCAL_BUILD.md` §6 landmine. That failure was in an msys2 Windows-only package, so it may not reproduce on macOS's vcpkg triplets, but **budget time to hit the same class of "vcpkg port fetch 404" problem and know the fix (bump to the newer commit) if it happens.** |
| Homebrew packages | `llvm create-dmg nasm cmake gcc wget ninja pkg-config` | `brew install` all of these |
| CocoaPods | via `flutter build macos` (auto-invoked) | `flutter/macos/Podfile` already present, `platform :osx, '10.14'` minimum |
| create-dmg | via brew, see table above | used to package the final `.dmg` installer |
| Apple Developer account + codesigning cert + notarization credentials | **only needed for the signed/distributable build** — see §5 | not needed to get an unsigned local build running |

---

## 2. Build recipe (translated from `.github/workflows/flutter-build.yml`'s `build-for-macOS` job — read that job in full before starting, this is a condensed version)

```bash
# 0. Prerequisites: Xcode + CLI tools installed, Homebrew installed.

# 1. Install build runtime
brew install llvm create-dmg nasm cmake gcc wget ninja pkg-config

# 2. Install Flutter 3.24.5 (subosito/flutter-action equivalent: download SDK,
#    add to PATH) — same as Windows §4/§5, see HANDOFF_LOCAL_BUILD.md

# 3. Flutter patches (CI applies these — check if still needed for 3.24.5,
#    they may be Windows/Linux-only fixes, verify before skipping):
cd "$(dirname "$(which flutter)")/.."
git apply <repo>/.github/patches/flutter_3.24.4_dropdown_menu_enableFilter.diff
# separately, CI also does a sed patch to flutter's own scheduler binding.dart
# for https://github.com/flutter/flutter/issues/133533 — see workflow lines
# ~763-769 for the exact sed command.

# 4. Install Rust 1.81 + target
rustup toolchain install 1.81
rustup target add aarch64-apple-darwin   # or x86_64-apple-darwin for Intel
rustup default 1.81

# 5. Get the flutter_rust_bridge-generated files
#    IMPORTANT: bridge codegen output is NOT platform-specific — it's derived
#    purely from the Rust FFI interface definitions, identical on every OS.
#    Once the Windows-side fixes in this repo are committed (they include a
#    working generated_bridge.dart/.freezed.dart, see HANDOFF_LOCAL_BUILD.md),
#    a Mac build should be able to REUSE those files directly instead of
#    re-running flutter_rust_bridge_codegen + build_runner from scratch. Only
#    regenerate if the Rust FFI surface (src/flutter_ffi.rs) has changed since.

# 6. vcpkg
git clone https://github.com/microsoft/vcpkg
cd vcpkg && git checkout 6f29f12e82a8293156836ad81cc9bf5af41fe836   # or the
  # newer 120deac3062162151622ca4860575a33844ba10b if you hit the same dead-
  # mirror problem Windows did, see table above
./bootstrap-vcpkg.sh
export VCPKG_ROOT=$(pwd)
$VCPKG_ROOT/vcpkg install --x-install-root="$VCPKG_ROOT/installed"
# triplet is picked up from vcpkg.json / VCPKG_DEFAULT_TRIPLET — CI doesn't
# pass --triplet explicitly here (unlike Windows), check vcpkg.json's default

# 7. Build
cd <repo root>
# only if targeting Apple Silicon — patches minimum macOS version to 12.3:
#   sed -i '' -e "s/MACOSX_DEPLOYMENT_TARGET=[0-9]*.[0-9]*/MACOSX_DEPLOYMENT_TARGET=12.3/" build.py
#   sed -i '' -e "s/platform :osx, '.*'/platform :osx, '12.3'/" flutter/macos/Podfile
#   sed -i '' -e "s/osx_minimum_system_version = \"[0-9]*.[0-9]*\"/osx_minimum_system_version = \"12.3\"/" Cargo.toml
#   sed -i '' -e "s/MACOSX_DEPLOYMENT_TARGET = [0-9]*.[0-9]*;/MACOSX_DEPLOYMENT_TARGET = 12.3;/" flutter/macos/Runner.xcodeproj/project.pbxproj
./build.py --flutter --hwcodec --unix-file-copy-paste --screencapturekit
# --screencapturekit is arm64-only per CI matrix (x86_64 job passes no extra
# flag) — drop it if building for Intel.

# 8. Package as unsigned DMG
CREATE_DMG="$(readlink -f "$(command -v create-dmg)")"
sed -i '' -e 's/MAXIMUM_UNMOUNTING_ATTEMPTS=3/MAXIMUM_UNMOUNTING_ATTEMPTS=7/' "$CREATE_DMG"
create-dmg --icon "RustDesk.app" 200 190 --hide-extension "RustDesk.app" \
  --window-size 800 400 --app-drop-link 600 185 \
  rustdesk-<version>-<arch>.dmg ./flutter/build/macos/Build/Products/Release/RustDesk.app
# ^ NOTE: every "RustDesk"/"rustdesk" literal above is exactly what needs to
#   become "BCS Beam"/"BCSBeamRemote" per §0 — this command as-is (copied
#   straight from CI) packages an app still named/labeled RustDesk.
```

---

## 3. Known risk carry-overs from the Windows effort (untested here, but worth checking first)

These bit the Windows build despite starting from a similar CI recipe — no reason to
assume macOS is immune, since several are Dart/Flutter-toolchain issues, not
Windows-specific:

1. **`frontend_server_client`/Dart SDK snapshot mismatch** (`HANDOFF_LOCAL_BUILD.md`
   landmine #6): Dart SDK 3.5.4 (bundled with Flutter 3.24.5, same version on macOS)
   doesn't ship the legacy `frontend_server.dart.snapshot` that `build_runner 2.4.8`'s
   pinned `frontend_server_client ^3.0.0` hardcodes. The fix already applied to
   `flutter/pubspec.yaml` (`dependency_overrides: frontend_server_client: ^4.0.0`) is
   cross-platform Dart config — should already be fixed once you're on the same
   `flutter/pubspec.yaml` as the Windows work, but verify `dart run build_runner build`
   actually succeeds.
2. **`flutter_rust_bridge_codegen` must NOT be run with `--no-build-runner`** (landmine
   #4) if you do end up regenerating the bridge — same reasoning as Windows.
3. **EULA/license text company name** — irrelevant to macOS packaging (that's
   Windows-MSI-specific, `res/msi/`), but if a macOS installer/DMG background or "About"
   text needs similar text, check `flutter/lib/desktop/pages/desktop_setting_page.dart`'s
   `_About`/`_LicenseStatement` widgets (shared Flutter code, should already show the
   correct "BROCENT CLOUD SERVICE CO., LTD (BCS TEAM)" text once built from the same
   source as the Windows work).
4. **`is_installed()`-style logic**: Windows had a real bug where the "install
   detection" code used a *different* app name than what was actually on disk/registry
   (`HANDOFF_LOCAL_BUILD.md` landmine #12, in `src/platform/windows.rs`). The macOS
   equivalent (`src/platform/macos.rs`) does the install check by testing
   `/Applications/{get_app_name()}.app` directly — i.e. it uses the *same* app name
   value for both the check and (implicitly) the expected bundle name, so **this
   particular bug class shouldn't recur on macOS as long as whoever does the macOS
   branding work makes the actual `.app` bundle name (`CFBundleName`/`PRODUCT_NAME` in
   Xcode) literally match `get_app_name()`'s compiled value ("BCS Beam") exactly** — call
   this out explicitly to whoever does that work, it's the one thing to get right to avoid
   repeating the Windows mistake.
5. **vcpkg commit staleness** — see §1 table.

---

## 4. What's genuinely new for macOS (no Windows equivalent)

- **Code signing & notarization**: unsigned macOS apps show Gatekeeper warnings and, since
  recent macOS versions, may be very difficult for end users to run at all without
  right-click-Open workarounds. CI's signing step (`flutter-build.yml` lines ~846-862)
  needs an Apple Developer ID certificate + notarization API key — **this requires an
  actual paid Apple Developer Program membership and its credentials**, a new
  organizational dependency, not just a technical one. Get this from whoever manages
  Brocent's Apple Developer account before attempting a distributable build; an unsigned
  local build (§2 above) doesn't need it.
- **Universal/architecture split**: macOS ships two separate CPU architectures
  (`x86_64-apple-darwin` Intel, `aarch64-apple-darwin` Apple Silicon/M-series) as
  *separate builds* (CI builds both, produces two DMGs) — decide whether Brocent needs
  both or just Apple Silicon (most new Macs since 2020) for a first pass.
- **Entitlements**: `flutter/macos/Runner/Release.entitlements` /
  `DebugProfile.entitlements` already exist and are presumably upstream-correct (grant
  microphone access etc. for remote-support features) — should not need changes, but
  worth a read given RustDesk's screen-recording/accessibility permission prompts are a
  common source of confused end users on macOS specifically.
- **App icon**: needs a `.icns` file generated from the approved BCS Beam mark (see
  `res/icon.ico`'s design — blue rounded-square badge with white "B") and wired into
  `flutter/macos/Runner/Assets.xcassets/AppIcon.appiconset`.

---

## 5. Suggested order of work

1. Get an **unsigned** build running end-to-end (§2), accepting it'll still say
   "RustDesk" everywhere — this validates the toolchain before spending time on branding.
2. Do the macOS branding pass (§0's checklist: bundle identifier, Info.plist, `.icns`
   icon, `build.py`'s hardcoded "RustDesk"/"RustDesk Installer" strings, the `create-dmg`
   call's literals) — mirroring what the Windows branding phase did, documented (for
   reference/pattern, not literal reuse — the actual Windows changes are Windows-file-
   specific) in whatever memory/handoff covers that earlier phase.
3. Rebuild with the branding changes, validate hands-on (does it say "BCS Beam"
   everywhere, does the custom rendezvous server connect, does the About/License page
   show correctly).
4. Only then pursue code signing/notarization (§4) once Apple Developer credentials are
   available — this is a separate, later milestone, same as Windows deferred MSI signing
   until after functional validation passed.

---

## 6. Open questions for whoever picks this up

- Does Brocent already have an Apple Developer Program account/certificate? (blocks §4,
  not §1-3)
- Target both Intel and Apple Silicon, or just one?
- Is there an existing macOS-capable build machine, or does this also start from a bare
  machine like the Windows effort did (in which case, budget similar multi-day toolchain
  bring-up time, not just the build itself)?
