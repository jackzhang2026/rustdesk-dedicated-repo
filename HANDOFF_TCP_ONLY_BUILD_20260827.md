# BCS Beam (RustDesk fork) — TCP-Only Rendezvous Build Handoff

**For: Claude Desktop on Jack's Windows machine, continuing the build locally.**
**Date: 2026-08-27. Self-contained — do not assume access to any other machine.**

You are picking up ONE small, well-understood source change on top of the fork's existing
branding/self-update work, and building it into a real installer. This doc is everything
you need — you do not need access to the FINOS main repo or the HK/CN/SG servers to do
this task; you only need this repo and a Windows build box.

---

## 0. TL;DR — what to do

1. **Confirm the commit is actually on GitHub first (§1) — it may not be yet.**
2. Set up the toolchain exactly as in `HANDOFF_LOCAL_BUILD.md` §4 in this repo (Rust 1.75,
   Flutter 3.24.5, LLVM 15.0.6, vcpkg pin — don't re-derive, that doc already has it).
3. Build per `HANDOFF_LOCAL_BUILD.md` §5 (same recipe, nothing about the build steps
   themselves has changed).
4. Validate branding per `HANDOFF_LOCAL_BUILD.md` §7 **AND** the new TCP-only check in
   §4 below (this is the part that's actually new/risky and needs real verification).
5. Report back per §5 below.

---

## 1. ⚠️ FIRST: verify the commit actually reached GitHub

The commit this handoff is about (`b4deeb7`) was made by a Linux-side Claude Code session
that does **not** have git-push permission to this repo (its own permission classifier
blocks `git push` to a public GitHub remote — a known, recurring limitation, not specific
to this commit). Jack was asked to run this push by hand:

```bash
git -C /home/ecs-user/beam-remote-client push origin main
```

**Before doing anything else**, check whether that happened:

```powershell
git ls-remote https://github.com/jackzhang2026/rustdesk-dedicated-repo.git main
```

Compare the SHA it prints against `b4deeb7...` (or just `git clone`/`git pull` and check
`git log --oneline -1` shows `feat(network): force TCP-only rendezvous transport`). **If
the commit isn't there, stop and tell Jack** — don't try to recreate the diff from this
doc's description; ask for the push to happen, or pull the patch a different way. The full
diff is reproduced in §6 below as a fallback ONLY if you truly cannot get the pushed commit.

## 2. What this project is

Same as `HANDOFF_LOCAL_BUILD.md` §1 — BCS Beam Remote, Brocent's rebranded fork of
[RustDesk](https://github.com/rustdesk/rustdesk) 1.3.9, AGPL-3.0-only, backup remote-support
channel (primary is MeshCentral). Repo: `github.com/jackzhang2026/rustdesk-dedicated-repo`.

**Read `HANDOFF_LOCAL_BUILD.md` in this same repo first** for: toolchain setup (§4), the
authoritative build recipe (§5), known landmines (§6), the on-machine validation checklist
(§7), signing strategy (§8), and the decisions log (§9). None of that changed — this doc
only adds what's new since then.

## 3. What changed and why (commit `b4deeb7`)

**One functional change, in `src/rendezvous_mediator.rs`:** `RendezvousMediator::start()`
now **always** calls `start_tcp()` — the branch that used to decide UDP-vs-TCP based on
`is_http_proxy` / the `disable-udp` builtin option / a `TEST_TCP` debug flag is gone
entirely. The client will never attempt UDP rendezvous again, full stop.

**Why:** TASK-061 #13 (see `backend/docs/BCS_BEAM_OPEN_ISSUES_REGISTER.md` in the FINOS
main repo if you ever get access to it — not required for this task). Short version: our
mainland-China RustDesk relay (a box in `cn-hangzhou` that mainland clients connect to
instead of the HK server directly, to route around a GFW RST-injection issue on raw
cross-border RustDesk TCP) only forwards TCP 21115-21117. UDP 21116 has no path through it
at all — the mainland cloud instance's own network egress blocks all outbound UDP to
foreign IPs, so there's no way to bridge it even if we wanted to. Since the hbbs/hbbr
server fleet also runs `-k _` (always-relay mode), direct P2P via UDP hole-punching was
never usable in this deployment to begin with — there is no downside to removing the UDP
attempt.

Before this change, the only way to get TCP-only behavior was hand-editing
`disable-udp = "Y"` into the user's local `%APPDATA%\BCS Beam\config\BCS Beam2.toml` —
error-prone for non-technical staff, and that option was **never exposed in the Settings
UI** to begin with. This change makes TCP-only the compiled-in, permanent behavior for
every BCS Beam install — no config file editing, ever, for anyone.

**Also touched, mechanically (cleanup, not functional):** two now-unused imports removed
(`proxy::Proxy`, `ui_interface::get_builtin_option`) — the compiler would otherwise warn
(possibly error, depending on lint settings) on unused imports. `NOTICE.md` updated with a
new disclosure entry per this fork's AGPL-3.0 change-tracking practice — read it, it has
the same explanation in the repo's own permanent record.

**Not compiler-verified before this handoff** — the Linux box that made this change has
no Rust toolchain at all. Every symbol touched by the removed code was manually traced
with `grep` across the whole file to confirm nothing else in `rendezvous_mediator.rs`
still references it, but a real `cargo build`/`cargo check` has never run over this diff.
**This means your build in §0/§5 IS the first real compile-check** — if it fails, the
likely candidates are exactly those two import removals or a subtlety in how
`start_tcp()`/`start_udp()` are still both defined (only the *decision* between them was
removed, both functions' bodies are untouched) — look there first, don't assume it's an
unrelated toolchain/environment issue.

## 4. Validation checklist — do this IN ADDITION TO `HANDOFF_LOCAL_BUILD.md` §7

The branding checklist in that doc still applies unchanged. Add these TCP-specific checks:

- [ ] **Build succeeds** (the real first-time compile check for this diff — see §3 above).
- [ ] Point the built client's ID/Relay server at `beam-relaycn.brocent.com` (the mainland
      relay's domain — it resolves to a real box, `120.26.3.214`, that only accepts TCP on
      21115-21117; it will NOT respond to UDP 21116 at all, by design).
- [ ] **Confirm it connects/registers successfully** using ONLY that server address —
      no config file edits, `disable-udp` untouched, fresh default config.
- [ ] **Confirm zero outbound UDP to port 21116 is even attempted.** Easiest way: Windows
      Resource Monitor (`resmon.exe`) → Network tab → filter by the BCS Beam process → look
      at active TCP/UDP connections while it's registering/connecting. Or `netstat -ano |
      findstr :21116` while the client is running — you should see a TCP connection, never
      UDP. (A packet capture with Wireshark filtered on `udp.port == 21116` showing zero
      packets is the more rigorous version if you have it handy.)
- [ ] Do a real two-machine remote-control session through `beam-relaycn.brocent.com` if
      you have a second Windows machine/VM available — confirms the whole path (register →
      relay-connect → actual screen-share) works end-to-end on TCP, not just registration.
      If you only have one machine, registration-succeeding + zero-UDP is still a strong
      signal and is an acceptable minimum bar to report back on.
- [ ] Also spot-check the OLD default server (`beam-relay.centoffer.com`, the HK box) still
      works the same way — this change is server-agnostic, it should behave identically
      against either relay, just always-TCP now instead of always-UDP-first.

## 5. What to hand back to Jack when done

A working, validated build (same artifact types as `HANDOFF_LOCAL_BUILD.md` §10: unsigned
`BCSBeamRemote-<ver>-x86_64.msi` + portable `.exe`) that passes **both** that doc's §7
checklist and the §4 checklist above, plus explicit confirmation of:
1. Whether it compiled cleanly on the first try, or what had to be fixed (report even
   trivial fixes — this diff has never been compiler-checked, so any friction here is
   useful signal for next time).
2. The zero-outbound-UDP-21116 confirmation, with whatever evidence you captured
   (resmon/netstat/Wireshark screenshot or description).
3. Whether the two-machine remote-control test happened or only the registration/zero-UDP
   check (say which, don't imply full end-to-end if you only did the minimum).

If the build fails in a way that looks caused by this diff (not a toolchain/environment
issue), fix it and note what was wrong in your report — you know Rust/this codebase in
context better than the session that wrote the diff blind (no compiler on that machine).

## 6. Fallback: the diff, if §1's pushed-commit check fails

Only use this if you've confirmed via §1 that `b4deeb7` genuinely never reached GitHub and
Jack can't push it either. Apply by hand to a checkout of this repo at its current `main`
tip (as of this handoff, that tip should be `63c6e04` + this diff on top):

```diff
diff --git a/src/rendezvous_mediator.rs b/src/rendezvous_mediator.rs
index 69fc886..6a9d9b3 100644
--- a/src/rendezvous_mediator.rs
+++ b/src/rendezvous_mediator.rs
@@ -16,7 +16,6 @@ use hbb_common::{
     futures::future::join_all,
     log,
     protobuf::Message as _,
-    proxy::Proxy,
     rendezvous_proto::*,
     sleep,
     socket_client::{self, connect_tcp, is_ipv4},
@@ -29,7 +28,6 @@ use hbb_common::{
 use crate::{
     check_port,
     server::{check_zombie, new as new_server, ServerPtr},
-    ui_interface::get_builtin_option,
 };

 type Message = RendezvousMessage;
@@ -383,21 +381,14 @@ impl RendezvousMediator {

     pub async fn start(server: ServerPtr, host: String) -> ResultType<()> {
         log::info!("start rendezvous mediator of {}", host);
-        //If the investment agent type is http or https, then tcp forwarding is enabled.
-        let is_http_proxy = if let Some(conf) = Config::get_socks() {
-            let proxy = Proxy::from_conf(&conf, None)?;
-            proxy.is_http_or_https()
-        } else {
-            false
-        };
-        if (cfg!(debug_assertions) && option_env!("TEST_TCP").is_some())
-            || is_http_proxy
-            || get_builtin_option(config::keys::OPTION_DISABLE_UDP) == "Y"
-        {
-            Self::start_tcp(server, host).await
-        } else {
-            Self::start_udp(server, host).await
-        }
+        // BCS Beam: always use TCP rendezvous, unconditionally. Our mainland-China relay
+        // hop (CN box -> HK via TCP-encapsulated IPsec, see BCS_BEAM_OPEN_ISSUES_REGISTER.md
+        // #13) forwards TCP only — UDP 21116 has no path through it. And since the hbbs/hbbr
+        // fleet runs `-k _` (always-relay), direct P2P via UDP hole-punching was never usable
+        // in this deployment anyway, so there is no upside to attempting UDP first. This
+        // removes the need for end users to hand-edit `disable-udp = "Y"` into their local
+        // config file — it was never exposed in the Settings UI and was error-prone to set.
+        Self::start_tcp(server, host).await
     }

     async fn handle_request_relay(&self, rr: RequestRelay, server: ServerPtr) -> ResultType<()> {
```

`NOTICE.md` also has a new disclosure section (see the live file at `main` tip, or ask
Jack to push — it's not essential to have it before building, only before the NEXT public
release, since it's a documentation-only AGPL-compliance file).

## 7. Context you probably don't need but is here just in case

This is unrelated to any pending Jack decisions (e.g. §3's bilingual-installer question in
`HANDOFF_LOCAL_BUILD.md`, or signing in §8 of that doc) — treat this as an independent,
orthogonal patch on top of whatever state that other work is in. Don't block this task on
those, and don't let this task block those.
