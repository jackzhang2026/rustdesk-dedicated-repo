# BCS Beam (RustDesk fork) — UDP-first/TCP-fallback Build, Recompile + Test

**For: whichever agent/machine is doing the next Windows build.**
**Date: 2026-08-27. Self-contained — read this fully before testing; the expected
pass/fail pattern below is not obvious from just running the app.**

This supersedes two earlier same-day handoffs on this repo
(`HANDOFF_TCP_ONLY_BUILD_20260827.md`, and the `secure_tcp()` fix that followed it — no
separate doc was written for that one, it's commit `c29bb26`). Read this doc; you don't
need to re-read those, but don't be surprised if you see their names in `git log`.

---

## 0. TL;DR — what to do

1. Confirm commit `b18c867` (see §1) is actually on GitHub.
2. Pull it, rebuild per `HANDOFF_LOCAL_BUILD.md` §4-5 (toolchain/recipe unchanged).
3. Test per §4 below — **read §3 first** so you know which failure is expected and which
   one is new.
4. Report back per §5.

---

## 1. ⚠️ FIRST: verify the commit reached GitHub

Same recurring caveat as every prior handoff on this repo — the session that makes these
fixes cannot `git push` (its own permission classifier blocks it on a public GitHub
remote), Jack pushes by hand afterward. Check before doing anything else:

```powershell
git ls-remote https://github.com/jackzhang2026/rustdesk-dedicated-repo.git main
```

Compare against `b18c867...`. If it's not there, stop and ask Jack to push rather than
hand-applying anything from memory.

## 2. The story so far (context, don't skip — explains why §3/§4 look the way they do)

TASK-061 #13 needed mainland-China clients to reach our RustDesk relay without crossing
the border directly (GFW RST-injects raw cross-border RustDesk TCP). The fix: mainland
clients hit a domestic relay box (CN/SH) that tunnels to our real HK server over
TCP-encapsulated IPsec — because the mainland cloud boxes' *own* outbound network egress
blocks UDP entirely, this whole relay path only carries TCP.

That produced three same-day iterations on the client, in order:

1. **`b4deeb7`** — forced the client to *always* use TCP, unconditionally, for every
   connection regardless of location. Real device testing found it never reached "Ready."
2. **`c29bb26`** — root-caused that failure to `secure_tcp()`: our self-hosted `hbbs`
   never proactively sends the optional encryption handshake message the client was
   waiting for (verified with a raw socket probe — connect, wait, zero bytes back). Fixed
   the client to treat that as a graceful no-op instead of a fatal timeout.
3. **This handoff (`b18c867`)** — revises `b4deeb7`'s "always TCP" further, because it
   turned out to be the wrong scope: forcing TCP for *every* client broke nothing for
   mainland-relay users but was a straight regression for anyone connecting directly to
   our HK/SG servers (or any residential/office network reaching them) — they'd been
   working fine over UDP, and forcing TCP took away the lower-overhead direct-P2P path for
   no benefit. A hostname-based "TCP only for these specific relay domains" rule was
   considered and rejected too, once smart/GeoDNS plans to put HK/SG/CN/SH all behind one
   shared hostname made "decide by which domain name was typed" structurally impossible —
   the client can't tell from the hostname which kind of backend a given DNS answer
   routed it to.

   The fix in this commit: **try UDP first, fall back to TCP automatically per-connection**
   if UDP gets zero responses after enough attempts (see `src/rendezvous_mediator.rs` for
   the exact threshold/comments). This adapts correctly no matter what the client actually
   connects to, with no manual config either way.

## 3. ⚠️ Read this before testing — there is a KNOWN, SEPARATE, still-open server-side gap

**Independent of anything in this client repo**, we found (by cloning and reading the
actual `rustdesk/rustdesk-server` source) that the **open-source `hbbs` server does not
implement client registration over TCP at all** — its TCP message handler explicitly
rejects `RegisterPk` with `NOT_SUPPORT` and has no handler branch for `RegisterPeer`
whatsoever (both are fully implemented on the UDP side). This isn't a bug we introduced;
it's how upstream's OSS server has always worked — likely a deliberate gap versus their
paid Server Pro product.

**What this means for your testing right now, today:** the UDP-first path in this build
should work exactly like it always did (nothing changed there for a client that never
needs the fallback). But **the TCP-fallback path will still fail to register** until a
separate, not-yet-done server-side patch lands (tracked as its own follow-up, adding real
`RegisterPeer`/`RegisterPk` handling to a forked `hbbs`). If you test against a scenario
that forces the TCP fallback (e.g. connecting through the CN/SH mainland relay boxes,
where UDP genuinely can't reach the server), **expect it to still not reach Ready** — that
is the current known, already-tracked state of the world, not a new regression in this
commit. Don't burn time re-diagnosing it; just confirm it fails the *same way* as before
(hangs registering, not a new crash) and report it as "expected, waiting on server fix."

**What SHOULD fully work today:** any connection where UDP works at all — i.e., testing
directly against `beam-relayhk.brocent.com` / `beam-relaysg.brocent.com` (not through the
CN/SH relay) from a normal residential/office network. That path never needed the TCP
fallback in the first place and should behave exactly as it did before any of today's
three client changes — this is the regression check for `b4deeb7`'s original mistake.

## 4. What to actually test

- [ ] Build succeeds (first real compile check for this diff — no Rust toolchain on the
      Linux box that wrote it; if it doesn't compile, the error is almost certainly in
      `src/rendezvous_mediator.rs`, not elsewhere — see the diff in §6).
- [ ] **Direct-to-HK/SG test (this should fully pass — this is the regression check):**
      point the client at `beam-relayhk.brocent.com` or `beam-relaysg.brocent.com` from an
      ordinary network (not through CN/SH). Confirm it reaches Ready quickly (UDP working
      on the first try, no ~30s delay) — same speed/behavior as before any of today's three
      changes.
- [ ] **Mainland-relay test (expected to still fail, confirm it fails the RIGHT way):**
      point the client at `beam-relaycn.brocent.com` (or `beam-relaysh...` once that box is
      confirmed ready — ask if unsure). Confirm you see roughly a ~30 second delay
      (UDP being tried and timing out) before it visibly switches to attempting TCP, and
      that the TCP attempt itself now gets *past* the handshake stage (no more
      connect→instant-fail→reconnect loop from `secure_tcp()`) but still doesn't reach
      Ready (this is the known server-side gap from §3, not a new bug).
- [ ] Zero outbound UDP to port 21116 is **no longer the right thing to check** — this
      build is expected to send UDP now, that's the whole point. Don't reuse that old
      checklist item.

## 5. What to hand back to Jack when done

1. Whether it compiled cleanly, or what had to be fixed.
2. Direct-to-HK/SG result — this one needs to be a clean pass; if it isn't, that's a real
   new regression worth flagging loudly.
3. Mainland-relay result — confirm it fails in the *expected* way described in §3 (reaches
   the TCP-fallback stage, gets past handshake, still doesn't register) rather than some
   other new failure mode.
4. Don't build/ship this as "done" — the mainland-relay path genuinely isn't usable yet
   until the separate server-side patch lands. This build is a checkpoint, not the finish
   line.

## 6. Fallback: the diff, if §1's pushed-commit check fails

Only if `b18c867` genuinely never reached GitHub. This sits on top of `c29bb26`
(the `secure_tcp()` fix) which sits on top of `b4deeb7`.

```diff
diff --git a/src/rendezvous_mediator.rs b/src/rendezvous_mediator.rs
index 6a9d9b3..1f2781b 100644
--- a/src/rendezvous_mediator.rs
+++ b/src/rendezvous_mediator.rs
@@ -156,6 +156,15 @@ impl RendezvousMediator {
         let mut reg_timeout = MIN_REG_TIMEOUT;
         const MAX_FAILS1: i64 = 2;
         const MAX_FAILS2: i64 = 4;
+        // BCS Beam (TASK-061 #13, 2026-08-27): if we have NEVER received a single response
+        // since this loop started, give up on UDP after this many consecutive timed-out
+        // registration attempts and let start() fall back to TCP. Deliberately well past
+        // MAX_FAILS2 so this only fires for "UDP flatly doesn't work on this path" (e.g. a
+        // mainland cloud relay hop whose own egress blocks outbound UDP) — once a single
+        // response has ever arrived, `update_latency()` resets `fails` to 0 on every
+        // success, so ordinary transient packet loss on an otherwise-working path never
+        // reaches this threshold.
+        const MAX_FAILS_NEVER_WORKED: i64 = 10;
         const DNS_INTERVAL: i64 = 60_000;
         let mut fails = 0;
         let mut last_register_resp: Option<Instant> = None;
@@ -224,6 +233,13 @@ impl RendezvousMediator {
                     if timeout || (last_register_sent.is_none() && expired) {
                         if timeout {
                             fails += 1;
+                            if last_register_resp.is_none() && fails >= MAX_FAILS_NEVER_WORKED {
+                                bail!(
+                                    "UDP rendezvous to {} got zero responses after {} attempts",
+                                    host,
+                                    fails
+                                );
+                            }
                             if fails >= MAX_FAILS2 {
                                 Config::update_latency(&host, -1);
                                 old_latency = 0;
@@ -381,14 +397,32 @@ impl RendezvousMediator {
 
     pub async fn start(server: ServerPtr, host: String) -> ResultType<()> {
         log::info!("start rendezvous mediator of {}", host);
-        // BCS Beam: always use TCP rendezvous, unconditionally. Our mainland-China relay
-        // hop (CN box -> HK via TCP-encapsulated IPsec, see BCS_BEAM_OPEN_ISSUES_REGISTER.md
-        // #13) forwards TCP only — UDP 21116 has no path through it. And since the hbbs/hbbr
-        // fleet runs `-k _` (always-relay), direct P2P via UDP hole-punching was never usable
-        // in this deployment anyway, so there is no upside to attempting UDP first. This
-        // removes the need for end users to hand-edit `disable-udp = "Y"` into their local
-        // config file — it was never exposed in the Settings UI and was error-prone to set.
-        Self::start_tcp(server, host).await
+        // BCS Beam (TASK-061 #13, revised 2026-08-27): try UDP first, fall back to TCP if
+        // UDP never gets a single response. Superseded the earlier "always TCP" version
+        // (b4deeb7) once we planned for smart/GeoDNS unifying all our relay entry points
+        // (HK/SG/CN/SH) under one hostname — the client can no longer tell from the
+        // hostname alone whether it landed on a UDP-capable direct entry (HK/SG, or any
+        // residential/office network reaching them) or a TCP-only mainland relay hop
+        // (CN/SH, whose own cloud egress blocks outbound UDP). Trying UDP first preserves
+        // the P2P/lower-overhead path for the majority of users where it already works;
+        // start_udp() below now gives up and returns an error after
+        // MAX_FAILS_NEVER_WORKED consecutive registration timeouts with zero responses
+        // ever received, which we catch here and fall back to start_tcp(). Costs a bounded
+        // ~30s UDP probe on every reconnect for users on a TCP-only path — a documented
+        // tradeoff, not a bug; caching "last transport that worked" per-server to skip the
+        // probe on subsequent reconnects is a reasonable follow-up, not done here to keep
+        // this diff small and easy to verify without a local compiler.
+        match Self::start_udp(server.clone(), host.clone()).await {
+            Err(e) => {
+                log::warn!(
+                    "UDP rendezvous to {} unavailable ({}), falling back to TCP",
+                    host,
+                    e
+                );
+                Self::start_tcp(server, host).await
+            }
+            ok => ok,
+        }
     }
 
     async fn handle_request_relay(&self, rr: RequestRelay, server: ServerPtr) -> ResultType<()> {
```

`NOTICE.md` also has the corresponding disclosure section revised (pull it along, not
essential before building).

## 7. Context you probably don't need

Unrelated to the macOS branding work (`a4788ab` etc.) that may also be sitting on `main` —
separate, independent effort, don't block on it either direction.
