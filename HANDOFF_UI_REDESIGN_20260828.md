# BCS Beam (RustDesk fork) — UI Redesign Phase 1, Build + Visual Verification

**For: whichever agent/machine is doing the next Windows/Mac build.**
**Date: 2026-08-28. Self-contained — read this fully; the checklist in §4 is what
actually matters, everything before it is context for WHY these specific changes.**

Design record (screenshots/interactive mockup covering every screen touched below,
plus screens NOT touched in this pass): an artifact Jack has already reviewed and
approved — ask him for the link if you want to compare the built app against it
visually. This doc is self-contained without it either way.

---

## 0. TL;DR — what to do

1. Confirm commits `7d7d8bf` and `cbc4756` (see §1) are on GitHub.
2. Pull, rebuild per `HANDOFF_LOCAL_BUILD.md` §4-5 (toolchain/recipe unchanged — this
   is a Dart/Flutter-only change, no Rust code touched, no new dependencies).
3. **Run `flutter analyze` before anything else** — see §3, this is the first real
   compile/analyze check these changes have had. No Flutter toolchain existed on the
   Linux box that wrote them.
4. Visually verify per §4's checklist.
5. Report back per §5.

---

## 1. ⚠️ FIRST: verify both commits reached GitHub

Same recurring caveat as every prior handoff on this repo:

```powershell
git ls-remote https://github.com/jackzhang2026/rustdesk-dedicated-repo.git main
```

Compare against `cbc4756...` (this session's `git push` succeeded and was verified —
`git rev-parse HEAD origin/main` matched after pushing — so this should be a formality,
not a real blocker like it has been in some prior handoffs).

## 2. What this phase actually is — and, just as important, what it ISN'T

Jack asked for the RustDesk-fork client's screens to be redesigned against BCS Beam's
already-approved brand system (blue `#1890FF`, navy `#081C33`, the icon's own
`#1976E8→#0D3B6E` gradient — see `branding/README.md`) instead of stock RustDesk's own
blue (`#0071FF`/`#2C8CFF`), which is what every screen still used despite the sidebar
wordmark/icon already carrying the correct brand colors. The design pass covered: the
home/connect screen, all 9 settings tabs, the in-session toolbar, the chat window, the
account login dialog, and a customer-install-vs-engineer-install comparison.

**This phase (`7d7d8bf`, `cbc4756`) is the color/token layer only** — the part that was
safe to do without a local Flutter toolchain to compile-check against. It does NOT
include:

- **Settings → Display tab's checkbox regrouping** (splitting the current flat
  13-checkbox list into 4 labelled sections). Not attempted because the underlying
  widget (`otherDefaultSettings()` in `common/widgets/setting_widgets.dart`) is shared
  between desktop AND mobile — restructuring it needs a way to actually see both render
  correctly, which this session didn't have.
- **The device list (Recent/Favorites/LAN tabs) becoming search-first with visible
  "last connected" timestamps.** Real scope, not a restyle — confirmed in an earlier
  investigation that "last connected" needs a new field threaded from Rust
  (`PeerConfig::peers()`'s `SystemTime`) into the Dart `Peer` model and its JSON
  payload; it's only used server-side for sort order today, never surfaced to the UI.
  This is its own follow-up, not started.
- **The customer-install vs. engineer-install packaging split** (`conn-type:
  incoming`/`outgoing` via a signed `custom.txt` at MSI-build time — the mechanism
  already exists dormant in this fork, confirmed working end-to-end for `isIncomingOnly`/
  `isOutgoingOnly`, just never wired into BCS Beam's actual release packaging). A real,
  separate decision Jack hasn't greenlit for implementation yet — don't build it
  speculatively.
- **The account-login dialog's backend target.** Flagged during design review: this
  dialog's "Login" button authenticates against `{api-server}/api/login`, which resolves
  to the public `https://admin.rustdesk.com` by default (a completely separate config key
  from the branded rendezvous server `beam-relay.centoffer.com`, which only carries the
  actual remote-control session). **Jack has already routed this to a different agent —
  do not touch `api-server`/`custom-rendezvous-server` config as part of this handoff.**
  The login dialog's own visual styling (focus color, button color) IS covered by this
  phase's token changes; its backend target is explicitly out of scope here.

## 3. ⚠️ Read this before testing — zero local compile/analyze verification exists yet

No Flutter SDK was available on the box that wrote these changes (confirmed: `flutter`
and `dart` both absent). Every edit was small, targeted, and hand-verified for Dart
syntax by re-reading the diff — but **this is the first real `flutter analyze`/build
these changes will ever see.** If something doesn't compile, it's most likely one of:

- A missing import (unlikely — every new symbol used, `MaterialStateProperty`,
  `BorderSide`, `Colors`, `LinearGradient`, `Alignment`, is a type already used
  elsewhere in the same file before this change).
- A stale/renamed API — e.g. if this Flutter SDK version has migrated
  `MaterialStateProperty` → `WidgetStateProperty` (a real rename in newer Flutter). The
  existing (pre-this-change) code in `desktop_setting_page.dart` already used
  `MaterialStateProperty.all<Color>(...)` for the exact button style this change
  replaces, so if that identifier is stale, it was ALREADY stale before this change —
  not something this phase introduced, but worth fixing in the same pass if you hit it.

## 4. What to actually verify (visual — no functional/behavioral change in this phase)

- [ ] `flutter analyze` — zero new errors/warnings in the 5 touched files:
      `flutter/lib/common.dart`, `flutter/lib/common/widgets/chat_page.dart`,
      `flutter/lib/desktop/pages/desktop_home_page.dart`,
      `flutter/lib/desktop/pages/desktop_setting_page.dart`.
- [ ] **Home screen**: the left accent bar next to "ID" and the ID value itself
      (`912 480 663`-style number) should render brand blue `#1890FF`, not the old
      `#0071FF`. ID and One-time Password values should both be visibly larger/bolder
      than before (24px/bold vs. the old 22px/15px) — check neither overflows or clips
      inside its card, especially the password field at the default (narrower,
      non-incoming-only) sidebar width.
- [ ] **In-session toolbar** (connect to any device, or just open the remote page): the
      pin button and any hover states should be brand blue, not stock RustDesk blue —
      this should be automatic (the toolbar's own color constants already referenced
      `MyTheme.button`/`.accent`, no toolbar file was edited directly) — if it's NOT
      brand blue, something about how the theme change propagates is broken and worth
      flagging as a real bug, not expected.
- [ ] **Chat window**: send a message to yourself/test peer both directions if possible
      — your own messages should be brand blue (unchanged behavior, still `accent`), the
      other party's bubble should be a muted navy-grey, NOT Material's default
      blue-grey.
- [ ] **Settings → Safety tab**: enable "Use IP whitelisting" — the warning icon next to
      it should be a warm amber/orange (`#F5A623`), not the old slightly-different
      hardcoded yellow. Check "Change ID"'s button now has a red outline (danger style)
      instead of looking like every other plain button.
- [ ] **Settings → General tab**: find the Wayland card (Linux only — skip if testing on
      Windows/Mac) — "Clear Wayland screen selection" should have the SAME red-outline
      danger style as "Change ID" above, not its old solid-red-fill look.
- [ ] **Settings → About tab and → License tab**: the copyright banner at the bottom of
      each should be a vertical gradient (darker blue at the bottom) instead of a flat
      solid blue.
- [ ] **Settings → Account tab → Login dialog**: username/password field focus ring and
      the "Login" button should be brand blue. The Google/GitHub/Microsoft buttons
      (if the server offers them) should stay in each provider's OWN brand color —
      that's intentional, not a bug, don't "fix" it to be blue.
- [ ] **Dark mode**: flip Settings → General → Theme to Dark and spot-check the above
      again — both `lightTheme` and `darkTheme` were edited in the same commit, but only
      light mode was visually reasoned through carefully; dark mode is worth an actual
      look.

## 5. What to hand back to Jack when done

1. Whether `flutter analyze` and the build were clean, or what had to be fixed (and
   whether the fix was a real bug in this change vs. a pre-existing stale API this
   change happened to touch).
2. Pass/fail on each checklist item in §4, with a screenshot for anything that doesn't
   match the description (especially: does the toolbar actually inherit the brand color
   automatically like it should, and does the ID/password text overflow/clip anywhere).
3. Explicitly confirm dark mode wasn't broken by the `ColorScheme.primary` change in
   `cbc4756` — that one was found and fixed via code review, not visual testing, so it's
   the least-verified part of this phase.
4. Don't build/ship this as "the redesign is done" — this is the color/token layer only;
   §2's three deferred items (Display tab regrouping, device list rework, customer/
   engineer packaging split) are real, separately-scoped follow-ups, not forgotten.

## 6. Files touched, for reference

- `flutter/lib/common.dart` — `MyTheme.accent`/`.button` unified to `#1890FF`;
  `ColorScheme.primary` in both themes fixed from stock `Colors.blue`; added
  `brandGradient`, `chatBubbleOther`, `warningColor` tokens.
- `flutter/lib/common/widgets/chat_page.dart` — other-party bubble uses
  `MyTheme.chatBubbleOther` instead of `Colors.blueGrey`.
- `flutter/lib/desktop/pages/desktop_setting_page.dart` — Safety tab warning icon color;
  new shared `_dangerButtonStyle` applied to "Change ID" and "Clear Wayland screen
  selection"; About/License copyright banners use `MyTheme.brandGradient`.
- `flutter/lib/desktop/pages/desktop_home_page.dart` — ID/password value font size/weight
  bump, ID board height adjusted to fit.

No files under `src/` (Rust) were touched — this is a pure Flutter/Dart change.

---

## 7. STATUS UPDATE (2026-08-29, Windows build session) — BUILT & VALIDATED

Executed per §0 on the Windows build machine. Results:

**Build (§3): clean.** `flutter analyze` on the 4 touched files: **0 errors, 0
warnings** — 26 info-level hits, all pre-existing codebase-wide deprecations
(`MaterialStateProperty`, `ColorScheme.background`, `RawKeyDownEvent`); the feared
`MaterialStateProperty`→`WidgetStateProperty` rename is deprecation-info only on this
SDK, compiles fine, nothing had to be fixed. Full pipeline (build.py → assemble →
preprocess → msbuild) passed in ~6 min (Rust layer fully incremental — no Rust
changes, so `librustdesk.dll` and the About page's "Build date" still read
2026-08-27; the Dart AOT snapshot `app.so` is fresh from this build, confirmed
deployed via install-dir timestamp).

**Artifacts:** `BCSBeamRemote-1.3.9.29799544-uiredesign-x86_64-{en-US,zh-CN}.msi`
(SHA-256 65930DE6… / EB43FE40…). Installed on Jack's machine (upgrade over
29797178): single ARP entry, service running, **network regression passed** — home
screen shows Ready, and hbbs logged `update_pk 1565553973` at the exact second the
new service started.

**Visual checklist (§4), from Jack's screenshots (6: home/Security/License/About
light + General/home dark):**

- ✅ Home (light + dark): ID accent bar + ID value brand blue; ID `1 565 553 973`
  and one-time password `gwd2ng` visibly larger/bolder, **no overflow or clipping**;
  dark-mode logo variant correct.
- ✅ Dark mode overall: no color anomalies on General/home — the `cbc4756`
  `ColorScheme.primary` fix (the least-verified change) did NOT break dark mode;
  accent blue renders correctly on radios/checkboxes/buttons.
- ✅ About + License: copyright banner renders correctly, white text legible. The
  gradient is subtle at screenshot size — no visual defect either way.
- ⬜ **Not yet verified** (security settings were locked in the screenshot /
  requires a live session): "Change ID" danger-outline style, IP-whitelist amber
  warning icon, chat bubble colors, in-session toolbar inheritance. No reason to
  expect failure — same token mechanism as the verified items — but §4 marks these
  open until someone unlocks security settings / runs a session.
- n/a Wayland card (Linux only).

**Verdict: phase-1 color/token layer is live and validated on real hardware.**
§2's three deferred items (Display-tab regrouping, device-list rework,
customer/engineer packaging split) remain open follow-ups, per §5.4.
