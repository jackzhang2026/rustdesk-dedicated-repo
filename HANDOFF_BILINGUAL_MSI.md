# BCS Beam (RustDesk fork) — Bilingual MSI Handoff

**For: whichever agent picks this up next on Jack's Windows build machine.**
**Date: 2026-08-25. Self-contained — do not assume access to any other machine or
this conversation's context.**

## 0. TL;DR

**Yes, this needs a real recompile.** WiX bakes a culture (language) into an MSI at
build time — it is not something a customer's machine picks at install time by
itself. Today this project only ever builds ONE culture (implicitly the neutral/
en-us default; there is no `<Cultures>` line in the project file at all), even
though a complete Chinese translation already exists and has never been wired in.

1. Add one line to `res/msi/Package/Package.wixproj` (§2).
2. Rebuild the MSI step ONLY — steps 1-6 of the existing build recipe (branding,
   the .exe itself, the portable packer) are unaffected and don't need re-running
   if you already have a built `flutter\build\windows\x64\runner\Release` output
   from a prior session. If you're starting completely fresh, follow
   `HANDOFF_LOCAL_BUILD.md` §4-§5 first, then come back here for the MSI step.
3. You should get TWO MSIs out (one per culture) instead of one. Validate both
   (§4) on real Windows — this is the part nobody has been able to check from
   Linux.
4. Report back per §5.

## 1. Current state (verified 2026-08-25, this repo, `HEAD=aa4fd69`)

- Translation content is **done and complete** — checked programmatically, not by
  eye: `Package.en-us.wxl` and `Package.zh-cn.wxl` (both in
  `res/msi/Package/Language/`) have the exact same 31 string IDs, none missing on
  either side. Same for the WiX-UI-extension overrides,
  `WixExt_en-us.wxl`/`WixExt_zh-cn.wxl` (also 100% matched IDs). Nobody needs to
  translate anything more.
- **The wiring is the only missing piece.** `res/msi/Package/Package.wixproj` has
  no `<Cultures>` element at all right now — confirmed by reading the file
  directly, it's an 18-line SDK-style project with `Configurations`/`Platforms`
  and package references, nothing culture-related. WiX v4's SDK project style is
  expected to auto-discover `.wxl` files by naming convention once `<Cultures>`
  is set (no explicit `<Content Include>` needed for the `Language/` folder,
  matching how the existing `en-us` build already "just works" without one) —
  **this expectation is unverified against a real build**, watch the `msbuild`
  output for any warning about a culture with no matching localization file.

## 2. The change

In `res/msi/Package/Package.wixproj`, inside the first `<PropertyGroup>` (next to
`Configurations`/`Platforms`), add:

```xml
<Cultures>en-US;zh-CN</Cultures>
```

That's it for the project file. Do not touch anything else unless the build tells
you to.

## 3. Rebuild (MSI step only — reuses everything else from HANDOFF_LOCAL_BUILD.md)

Same commands as `HANDOFF_LOCAL_BUILD.md` §5 step 7:

```powershell
cd res\msi
python preprocess.py --arp -d <dist> --app-name "BCSBeamRemote" --product-name "BCS Beam" --manufacturer "Brocent"
nuget restore msi.sln
msbuild msi.sln -p:Configuration=Release -p:Platform=x64 /p:TargetVersion=Windows10
```

**Expected difference from before**: instead of one `Package.msi`, you should get
output under two culture subfolders:
- `res\msi\Package\bin\x64\Release\en-US\Package.msi`
- `res\msi\Package\bin\x64\Release\zh-CN\Package.msi`

Rename them distinctly, e.g. `BCSBeamRemote-<ver>-x86_64-en.msi` /
`BCSBeamRemote-<ver>-x86_64-zh.msi` — do NOT reuse the old single
`BCSBeamRemote-<ver>-x86_64.msi` name for either, so a stale build never gets
confused with a fresh one.

**If the build fails or only produces one culture**: read the actual `msbuild`
error/warning text before guessing — WiX v4's exact convention for where it
expects localization files (relative to the `.wixproj` vs an explicit
`<WixVariable>`/`<Content Include>`) was NOT verified against a real compile as
of this handoff. If auto-discovery doesn't work, the fallback is to explicitly
reference each `.wxl`:
```xml
<ItemGroup>
  <Content Include="Language\Package.en-us.wxl" />
  <Content Include="Language\Package.zh-cn.wxl" />
  <Content Include="Language\WixExt_en-us.wxl" />
  <Content Include="Language\WixExt_zh-cn.wxl" />
</ItemGroup>
```
Try the plain `<Cultures>` line first; only add the explicit `<Content Include>`
block if the build genuinely doesn't pick the files up on its own.

## 4. On-machine validation (the real point — untested from Linux)

For EACH of the two MSIs:
- [ ] Install it standalone (not via the Inno wrapper — this is testing the raw
      MSI). Confirm the installer wizard, EULA, and any other visible MSI UI
      text is actually in the right language (not just "the build succeeded").
- [ ] Confirm branding still holds in BOTH — BCS Beam name/icons/wizard artwork,
      "Powered by RustDesk" still present. Bilingual wiring should not have
      touched any of that; this is a regression check, not new work.
- [ ] The zh-CN one specifically: check for mojibake/encoding issues (garbled
      characters) — a classic WiX bilingual-build failure mode when a `.wxl`
      file's encoding doesn't match what the culture pass expects.
- [ ] Confirm the app itself still connects to `beam-relay.centoffer.com` after
      installing from either MSI (language wiring shouldn't affect this, but
      it's a one-line check and this exact class of "unrelated build step broke
      something else" has happened before in this repo, see
      `HANDOFF_LOCAL_BUILD.md` §6).

## 5. What to hand back

- Confirmation both MSIs build and both pass §4.
- If you had to add the explicit `<Content Include>` fallback, say so (that's
  useful signal about WiX v4's actual behavior for next time).
- **Do not decide the bigger architecture question yourself** — whether the
  *unified* BCS Beam installer (the outer Inno Setup wrapper, a SEPARATE
  pipeline in the main finance repo, not this one) should (a) just silently
  pick which of these two MSIs to embed based on Jack's own choice per build,
  (b) auto-detect the OS's display language and pick accordingly, or (c)
  attempt the riskier single-auto-switching-MSI approach (embedding the zh-CN
  culture as a transform into the en-us MSI via `wix msi transform` +
  `msidb`/`WiSubStg.vbs` — nobody has verified this on Windows yet; treat as a
  separate, later, opt-in stretch goal, not part of this handoff's scope) — that
  decision belongs to Jack. Just get both MSIs building and validated, then stop
  and report.
- Update the main finance repo's tracking once done: this work closes item #15
  in `backend/docs/BCS_BEAM_OPEN_ISSUES_REGISTER.md` (that repo is
  `/home/ecs-user` on the Linux box, not reachable from a pure Windows session —
  relay the result back to Jack/the next Linux-side session to update it there).

## 6. Things NOT in scope for this handoff (don't re-do)

- Icon/branding — already done and verified across earlier commits
  (`cc4363a`→`319c0fc`→`a9dbfab`), don't re-touch.
- Code signing (SignPath/Sectigo) — separate, later step, comes after ALL
  branding+language work is validated (see `HANDOFF_LOCAL_BUILD.md` §8).
- The self-hosted update-check feature (`aa4fd69`, the tip commit of this repo
  as of this handoff) — already implemented, unrelated to bilingual MSI work.
- **Do not push this repo's commits to `origin/main` as a side effect of working
  on this.** Per this project's push policy (CLAUDE.md §6j in the main finance
  repo): local commits only during development, public GitHub push happens ONLY
  at actual deploy time, together with a version tag. `origin/main` is
  currently 1 commit behind local `HEAD` (`aa4fd69`) — that's expected and
  intentional, not something to "fix" by pushing.
