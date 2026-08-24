# BCS Beam (RustDesk fork) — Local Windows Build Handoff

**For: Claude Desktop on Jack's Windows machine, continuing the build locally.**
**Date: 2026-08-24. Self-contained — do not assume access to any other machine.**

You are picking up a rebranded RustDesk fork. Everything below is what you need to
build it on this Windows PC, finish the last task, and validate on real hardware —
without GitHub Actions (its quota is exhausted; Windows runners bill at 2× minutes).

---

## 0. TL;DR — what to do

1. Set up the toolchain (§4) — heavy first time (~15–25 GB, half a day).
2. Build (§5). The authoritative recipe is the three workflow files in
   `.github/workflows/` — they are a **known-good** build that succeeded on CI
   (run `32708350027`). Translate them to local PowerShell.
3. Finish the ONE open task: multi-language installer wiring (§3, decision pending
   from Jack — default to the safe path in §3).
4. Validate on this machine (§7 checklist): icons, window title, installer wizard,
   UAC-via-MSI, language.
5. Signing is a later step (§8) — build UNSIGNED first and validate branding.

---

## 1. What this project is

- **BCS Beam Remote** = Brocent's rebranded fork of [RustDesk](https://github.com/rustdesk/rustdesk),
  the **backup** remote-support channel (primary is MeshCentral). Self-compiled from
  source (Jack decided against paying for RustDesk Server Pro's custom-client generator).
- Repo: `github.com/jackzhang2026/rustdesk-dedicated-repo` (this repo). Based on
  RustDesk **1.3.9** + `hbb_common` flattened in (no submodule).
- **License: AGPL-3.0-only** (NOT GPL-3.0 — RustDesk's client is AGPL). Keep
  `NOTICE.md` accurate; the "Powered by RustDesk" attribution in the UI is
  **deliberately kept** (Jack's instruction — respect upstream).
- Our self-hosted server is baked into `libs/hbb_common/src/config.rs`:
  `RENDEZVOUS_SERVERS = ["beam-relay.centoffer.com"]`,
  `RS_PUB_KEY = "7Xy61LSDKygY5dUPtAfgUPR3i+NKLZPhpecfVesFco4="`,
  `APP_NAME = "BCS Beam"`.

## 2. Current repo state (all pushed to GitHub `main` as of this handoff)

Recent commits (newest first):
- `i18n(msi): add Simplified-Chinese installer strings (zh-cn)` — `Package.zh-cn.wxl` + `WixExt_zh-cn.wxl`
- `brand: approved installer wizard artwork + display-name decoupling` — wizard bmps + `preprocess.py --product-name`
- `fix(ci): real root cause of the MSI build failure — unquoted space in app-name`
- `fix: real branding regression — Flutter UI has its OWN hardcoded strings/icon`
- `fix: restore 118 files silently dropped by .gitignore's '*png' rule`
- `brand: replace stock RustDesk icons/logo with BCS Beam v1.3 assets`
- (+ the config.rs rebrand and CI-fix commits before those)

**Branding already done and verified (mostly on CI build `32708350027`, and locally):**
- `config.rs`: APP_NAME / server / key ✓
- App window title-bar text (`flutter/lib/desktop/widgets/tabbar_widget.dart`: `Text("BCS Beam")`) ✓
- Native window title fallback (`flutter/windows/runner/main.cpp`) ✓
- Windows file-properties (`flutter/windows/runner/Runner.rc`: CompanyName=Brocent, ProductName=BCS Beam; LegalCopyright keeps RustDesk/Purslane AGPL attribution) ✓
- Window/taskbar icon (`flutter/windows/runner/resources/app_icon.ico`) ✓ — this is a SEPARATE file from `res/icon.ico`; both are the BCS Beam "B" now.
- Tray icon (`res/tray-icon.ico`, compiled in via `src/tray.rs` include_bytes!) ✓
- All `res/` icons + wordmark SVGs ✓
- Installer (MSI): `preprocess.py --app-name BCSBeamRemote --product-name "BCS Beam"` →
  display name "BCS Beam" (spaced) everywhere the user reads it, exe filename stays
  space-free `BCSBeamRemote.exe`. Wizard bitmaps `res/msi/Package/Resources/WixUIDialogBmp.bmp`
  (493×312) + `WixUIBannerBmp.bmp` (493×58), force-added past `res/msi/.gitignore`.
  EULA (`License.rtf`) auto-rebrands (Purslane/rustdesk.com removed). **All verified by
  running preprocess.py locally on Linux; NOT yet compiled into an MSI on Windows.**

**KEY:** most user-visible RustDesk strings auto-rebrand at runtime because Flutter's
`translate()` routes through Rust `lang.rs::translate_locale`, which replaces
"RustDesk"→APP_NAME for every string EXCEPT `powered_by_me` ("Powered by RustDesk",
kept on purpose). Only LITERAL non-translated strings/assets needed hand-editing — those
are all done (listed above). Do NOT re-hunt `translate('...RustDesk...')` strings; they
self-rebrand.

## 3. The ONE open task — multi-language installer (Jack chose "auto-switch by OS language")

Chinese translations are DONE (`Package.zh-cn.wxl`, `WixExt_zh-cn.wxl`; `ProductLanguage=2052`).
What's NOT wired yet: making the MSI actually build/ship both languages.

**Two-installer reality:** customers run the **unified BCS Beam installer** (an Inno Setup
wrapper, in a separate FINOS build pipeline — NOT this repo) which silent-installs this
RustDesk MSI via `--silent-install`. So the MSI wizard is normally NOT shown to customers;
it's shown only when someone runs the standalone MSI (testing).

**Recommended safe path (proposed to Jack, confirm with him):** do OS-language auto-switch
at the **Inno wrapper** layer (Inno has robust built-in multi-language) and just make this
MSI **bilingual-buildable** (build both en-us and zh-cn cultures → two MSIs). Set
`<Cultures>en-US;zh-CN</Cultures>` in `res/msi/Package/Package.wixproj`. WiX's UI extension
ships built-in zh-CN for the standard chrome; our `*.zh-cn.wxl` covers the custom strings.

**Risky stretch (only if Jack insists on a single auto-switching standalone MSI):** build
both cultures, then embed the zh-CN transform into the en-us MSI (`wix msi transform` +
`msidb`/`WiSubStg.vbs` to add substorage + set the Summary Template to `1033,2052`). This
is the one step nobody could verify on Linux — do it LAST, after the base build works, and
keep the two single-language MSIs as the fallback if the embed misbehaves.

## 4. Toolchain setup (Windows) — match upstream CI pins EXACTLY (version drift breaks builds)

| Tool | Version | Notes |
|---|---|---|
| Visual Studio 2022 | Build Tools or Community | **"Desktop development with C++"** workload (MSVC + Windows SDK) |
| Rust | **1.75.0** | `rustup toolchain install 1.75.0-x86_64-pc-windows-msvc; rustup default 1.75.0` |
| Flutter | **3.24.5** (stable) | plus a custom engine + a patch, see §5 |
| LLVM/Clang | **15.0.6** | for `flutter_rust_bridge` / bindgen |
| vcpkg | commit **`120deac3062162151622ca4860575a33844ba10b`** | triplet `x64-windows-static` (builds libvpx/libyuv/opus/aom from source — slow, aom ~30 min) |
| Python | 3.x | build scripts |
| WiX | v4.0.5 | restored automatically by `msbuild`/`nuget` on `res/msi/msi.sln` |
| Git, 7-Zip/Expand-Archive | — | — |

Quick installs via winget (adapt as needed):
```powershell
winget install --id Git.Git -e
winget install --id Python.Python.3.12 -e
winget install --id LLVM.LLVM -v 15.0.6 -e          # or download the 15.0.6 installer explicitly
winget install --id Microsoft.VisualStudio.2022.BuildTools -e --override "--add Microsoft.VisualStudio.Workload.VCTools --includeRecommended"
# Rust:
Invoke-WebRequest https://win.rustup.rs -OutFile rustup-init.exe; .\rustup-init.exe -y --default-toolchain 1.75.0
# Flutter 3.24.5: download the stable 3.24.5 zip from flutter.dev and add flutter\bin to PATH.
# vcpkg:
git clone https://github.com/microsoft/vcpkg C:\vcpkg
cd C:\vcpkg; git checkout 120deac3062162151622ca4860575a33844ba10b; .\bootstrap-vcpkg.bat
```

## 5. Build recipe — the workflow files are AUTHORITATIVE

The exact, known-good build is encoded in three files in this repo — read them and run the
equivalent locally (they target a `windows-2022` runner; you're on Windows so most maps 1:1):
- `.github/workflows/build-bcsbeam.yml` — the main Windows build + portable-exe pack + MSI.
- `.github/workflows/bridge.yml` — `flutter_rust_bridge_codegen` step (generates
  `src/bridge_generated*.rs` + `flutter/lib/generated_bridge.dart`). Run this FIRST.
- `.github/workflows/third-party-RustDeskTempTopMostWindow.yml` — a tiny C++ helper subproject.

Core sequence (see the yml for exact flags/paths):
1. `flutter_rust_bridge_codegen` (per bridge.yml) to generate bridge files.
2. Install LLVM 15.0.6, Flutter 3.24.5, Rust 1.75, vcpkg deps (triplet `x64-windows-static`).
3. **Custom flutter engine + patch** (build-bcsbeam.yml "Replace engine" + "Patch flutter" steps):
   download `https://github.com/rustdesk/engine/releases/download/main/windows-x64-release.zip`
   into the flutter engine cache, and `git apply .github/patches/flutter_3.24.4_dropdown_menu_enableFilter.diff`.
4. Build: `python .\build.py --portable --hwcodec --flutter --vram --skip-portable-pack`
   → output in `flutter\build\windows\x64\runner\Release`. Also fetch usbmmidd_v2 + printer
   driver as the yml does.
5. Rename the exe to a space-free name for the MSI step:
   `Move-Item .\bcsbeam-remote\rustdesk.exe .\bcsbeam-remote\BCSBeamRemote.exe`
6. Portable self-extractor: `libs/portable/generate.py -f <dist> -o . -e <dist>\rustdesk.exe`
   → produces `BCSBeamRemote-<ver>-x86_64.exe` (portable; see §7 note about UAC).
7. MSI: `cd res\msi; python preprocess.py --arp -d <dist> --app-name "BCSBeamRemote" --product-name "BCS Beam" --manufacturer "Brocent"` ;
   `nuget restore msi.sln; msbuild msi.sln -p:Configuration=Release -p:Platform=x64 /p:TargetVersion=Windows10`
   → `res\msi\Package\bin\x64\Release\<culture>\Package.msi` → rename to `BCSBeamRemote-<ver>-x86_64.msi`.
   (For bilingual, add `<Cultures>en-US;zh-CN</Cultures>` to `Package.wixproj` — §3.)

Upstream official build docs (fallback reference):
https://rustdesk.com/docs/en/dev/build/windows/

## 6. Landmines already hit & fixed on CI (so you understand the repo's quirks)

1. **`.gitignore` silently drops assets.** The root `.gitignore` has `*png` and `res/msi/.gitignore`
   has `Package/Resources` — both hide REQUIRED tracked files. 118 files (incl. `libs/portable/src/res/label.png`
   needed at Rust compile time via `include_bytes!`, and all `flutter/assets/*.svg`) were force-added; the two
   wizard bmps too. If a build fails on a missing asset, check whether `.gitignore` ate it (`git check-ignore <path>`),
   and `git add -f`.
2. **`preprocess.py` shells out to `<app_name>.exe` UNQUOTED** — a space in the app name splits the command.
   That's why we use space-free `--app-name BCSBeamRemote` and the separate `--product-name "BCS Beam"` (a small
   patch we added — see it in `res/msi/preprocess.py`). Don't pass a spaced `--app-name`.
3. Flutter's `translate()` DOES rebrand at runtime (see §2 KEY) — the native/literal strings are the only ones
   needing hand-edits, all done.
4. Window icon = `flutter/windows/runner/resources/app_icon.ico` (via `LoadIcon(IDI_APP_ICON)` in
   `win32_window.cpp`); tray icon = `res/tray-icon.ico` (compiled via `include_bytes!` in `src/tray.rs`). Two
   different files — both already the "B".
5. (CI-only, N/A locally) ubuntu-20.04 runner deprecated; vcpkg commit was 18 months stale causing msys2 404s —
   both fixed by matching upstream's current pins, already reflected in the yml.

## 7. On-machine validation checklist (the whole point of building locally)

Build UNSIGNED first. Expect a "Unknown Publisher" SmartScreen prompt (signing is §8). Then verify:
- [ ] **Install via the .MSI** (not the portable .exe). The portable exe shows a "Due to UAC, BCS Beam can not
      work properly… Install" nag — that's EXPECTED for portable mode. The MSI does a full system install +
      registers the SYSTEM service (`RustDesk.wxs` CustomAction runs `<exe> --service`), so `is_installed()`=true
      and the UAC nag is gone. This is already handled; just test the MSI path.
- [ ] Installer wizard: window says "**BCS Beam Setup**", "Welcome to the **BCS Beam** Setup Wizard", left panel
      shows the navy BCS Beam art (NOT red RustDesk), EULA mentions Brocent/BCS Beam (no Purslane/rustdesk.com).
- [ ] App window: title-bar top-left icon = **B** (not red), title text = "BCS Beam", "Powered by RustDesk" is
      still present (intended).
- [ ] Tray icon = **B**. "About" / settings show "BCS Beam".
- [ ] It connects to our server (`beam-relay.centoffer.com`) and can start a session.
- [ ] Language (if §3 done): on a Chinese Windows the wizard/UI is Chinese; on English Windows, English.
- [ ] The RustDesk auto-id-report probe (a FINOS feature) — out of scope for the build; ignore.

## 8. After branding is validated — signing (do NOT do first)

Strategy (decided with Jack): layered.
- **RustDesk fork → SignPath Foundation** (free OSS code signing). This repo is a real from-source AGPL fork,
  a defensible SignPath candidate. Apply after a stable unsigned build exists.
- **Outer Inno wrapper / fleetd → Sectigo OV cert** (~$219–225/yr) — commercial, not this repo.
- **Azure Trusted Signing: rejected** (Brocent's Singapore HQ likely fails its geo identity check; no speed/trust
  advantage over OV).
- **Microsoft Security Intelligence whitelist submission** (free) — submit the stable signed binaries to reduce
  Defender/SmartScreen flagging. Separate from code signing; do both.

## 9. Decisions log (don't re-litigate)

- 2026-08-23: self-compile from AGPL source (not RustDesk Pro).
- 2026-08-23: branding scope = customer-visible surfaces only; **keep "Powered by RustDesk"**.
- 2026-08-23: license is **AGPL-3.0**, not GPL-3.0.
- 2026-08-24: build via GitHub Actions was the path; **now moved to local Windows** (quota).
- 2026-08-24: installer display name "BCS Beam" (spaced) via `--product-name`; exe filename `BCSBeamRemote.exe`.
- 2026-08-24: wizard artwork approved by Jack (navy panel + subtle "Beam" light-ray + white text zone).
- 2026-08-24: installer language = **auto-switch by OS language** (Jack's choice); safe delivery = Inno wrapper
  layer + bilingual-buildable MSI (§3).
- 2026-08-24: UAC nag is handled by the MSI/`--silent-install` full install; portable exe showing it is expected.

## 10. What to hand back to Jack when done

A working, validated, UNSIGNED `BCSBeamRemote-<ver>-x86_64.msi` (and portable `.exe`) that passes §7, plus a
note on whether the bilingual wiring (§3) is in. Then he decides on signing (§8).
