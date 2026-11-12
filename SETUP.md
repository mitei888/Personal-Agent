# Setting up the Personal Agent on a new Mac (the Mac mini)

**Only ONE Mac runs Bob + the reminder schedule at a time** (otherwise you get double replies and double reminders).
The mini is the "live" machine. The MacBook is for editing: change files → `git push` → mini pulls.

## 1. Install
```
# Claude Code (then run `claude` once and log in)
curl -fsSL https://claude.ai/install.sh | bash
# Bun (needed by the Discord plugin)
curl -fsSL https://bun.sh/install | bash
# Homebrew tools
brew install tmux mosh
# Python packages for reminders + briefing
python3 -m pip install --user pyyaml icalendar recurring-ical-events
```

## 2. Get the files
- `git clone git@github.com:mitei888/Personal-Agent.git ~/Personal_Agent`
  (add the mini's own SSH key to GitHub first: `ssh-keygen -t ed25519`, paste `~/.ssh/id_ed25519.pub` in GitHub → Settings → SSH keys)
- Keep the folder at **`~/Personal_Agent`** (Claude's memory is keyed to that path).

## 3. Copy the private files (AirDrop / USB — never via git)
| From MacBook | To mini (same place) |
|---|---|
| `~/Personal_Agent/.env`, `~/Personal_Agent/.agent.env` | same |
| `~/Personal_Agent/Travel, Entertain, Food/.env`, `Travel, Entertain, Food/Personal_Files/` | same |
| `~/Personal_Agent/Santa Monica Tax/` | same |
| `~/.claude/channels/discord/` (bot token + pairing/allowlist) | same — keeps you paired, no new code |
| `~/.claude/projects/-Users-<you>-Personal-Agent/memory/` | same folder name on the mini (`<you>` = mini username) |

## 4. Discord plugin
```
cd ~/Personal_Agent && claude
/plugin install discord@claude-plugins-official      # choose user scope
/exit
```

## 5. Switch the MacBook OFF (on the MacBook)
```
~/Personal_Agent/tools/install_schedule.sh off
```
…and quit any `claude --channels …` session on the MacBook.

## 6. Switch the mini ON (on the mini)
```
~/Personal_Agent/tools/install_schedule.sh
cd ~/Personal_Agent && python3 tools/remind.py --test     # should DM you "connected"
~/Personal_Agent/tools/install_bob.sh    # starts Bob in tmux now + at every login
# attach: tmux attach -t bob   ·   detach: Ctrl+B then D   ·   log: tools/bob.log
# remove autostart: tools/install_bob.sh off
# manual start instead:  tmux new -A -s bob  then  claude --channels plugin:discord@claude-plugins-official
```
For unattended restarts after a power cut, turn on **automatic login**
(System Settings → Users & Groups; needs FileVault off) — the job runs at login.

## 7. Mini settings
- System Settings → General → Sharing → **Remote Login** on (only your user)
- System Settings → Energy → **Prevent automatic sleeping** + **Start up after power failure**
- **Tailscale** installed + signed in (same account as the iPhone), **Launch at login** on — see §8
- Claude in Chrome extension in the mini's Chrome (only if you want Bob to browse/book), then in Bob: `/chrome` → **Enabled by default** (applies to every Claude session on this Mac, all folders)
- Keep 1Password locked / no auto-fill while Bob browses — Miranda logs in herself via Jump

## 8. Remote access from the iPhone (set up 11 Nov 2026)
Bob is kept alive by `tools/start_bob.sh` (launchd watchdog, every 2 min) and gets a fresh conversation daily 04:00–06:59 her time (`tools/refresh_bob.sh`). Pause the watchdog: `touch tools/.bob_pause`.

| Tool | Route | Use for |
|---|---|---|
| **Blink** (SSH) | Tailscale only | Talking to Bob, commands: `ssh bob` → `tmux attach -d -t bob` (detach: Ctrl-b, d) |
| **Jump Desktop**, "HK Mini" entry | Jump's own service, works on mobile data too | Anything on screen: logins, pop-ups, Chrome. Main backup if Tailscale is down |
| Jump, `100.96.9.33` port 5900 (VNC) | Tailscale | Optional spare (Jump's Fluid port 20020 isn't open over Tailscale) |

**Addresses (Tailscale):** mini = `100.96.9.33` (`mirandas-mac-mini-hk`), iPhone = `100.77.68.76` (`iphone197`). Full list: Tailscale app or login.tailscale.com → Machines.

**Blink host `bob`:** HostName `100.96.9.33`, User `user`, Key = the iPhone's Secure Enclave key (ECDSA, fingerprint ends `…L1RRswE`), mosh off (mosh not installed yet).
- The key is locked to that iPhone. **New phone:** install Tailscale + Blink, create a new key in Blink (`config` → Keys), send the public key to Bob to add to `~/.ssh/authorized_keys`, and remove the old phone's line.
- If `ssh bob` gives "socket error", test `ssh user@100.96.9.33` and check Tailscale is on (not NordVPN).

**VPNs on the mini — how they fit together:**
- **WireGuard "New HK Mini"** (firm, `vpn.ferrettocap.com`): split tunnel, only `10.9.0.0/24` (mini = `10.9.0.12`). Always on. Don't edit `AllowedIPs`. An iPhone WireGuard profile would need the tech team.
- **Tailscale + Mullvad add-on:** country exit node (currently Vancouver, CA). Replaces NordVPN on the mini.
- **NordVPN: keep OFF on the mini.** Its DNS server `100.64.0.2` sits in Tailscale's `100.64.x.x` range → with both on, DNS dies and no websites load. If Nord is ever needed there: Nord → Custom DNS `103.86.96.100`.
- **iPhone:** only one VPN at a time — Tailscale when using Blink (exit node "None" is fine), NordVPN otherwise. Nord auto-connect can kick Tailscale off mid-session.

**Bob restart (correct way):** `tmux kill-session -t bob && ~/Personal_Agent/tools/start_bob.sh`. Never start plain `claude` in the bob window — without `--channels` Discord DMs don't arrive.

**Open items (as of 12 Nov 2026):**
1. **Push to GitHub** — commit `5aad077` (watchdog, daily refresh, form rules, this file) is local only.
2. **Lock down SSH (most important)** — the mini has a public IP on en0, SSH is on, firewall off. Switch sshd to key-only (`PasswordAuthentication no`, `KbdInteractiveAuthentication no` in `/etc/ssh/sshd_config.d/`), turn on the macOS firewall. Needs Miranda's admin password; test `ssh bob` from Blink before closing the old session.
3. **1Password extension** — turn OFF: Offer to fill and save in fields, Universal sign in, Autofocus sign in prompts, Sign in automatically after autofill, and all "Show … in autofill suggestions". Auto-lock ~5 min (app → Settings → Security).
4. **Tailscale on the mini** — turn on "Launch at login" in its settings (it's in Login Items, but its own toggle read off).
5. **Test "fresh start" on Discord** — check Bob can restart himself via `tools/refresh_bob.sh --now` (auto-mode may block it; the 04:00 daily refresh runs regardless).
6. Optional: `brew install mosh` (then mosh on in Blink); remove stale Tailscale devices `macbook-pro-5`, `mirandas-mac-mini`; cancel NordVPN on the mini if not needed; add how the 4 extra travellers in `travel_ids.md` relate to Miranda (for "book for my parents").

## Day-to-day: editing on the MacBook
1. Edit on the MacBook (don't run Bob or the schedule there) → `git commit` → `git push`
2. On the mini: `cd ~/Personal_Agent && git pull`
3. If you changed `CLAUDE.md` or `.claude/agents/*`, restart Bob (they load at start-up).
   Changes to `reminders.yaml` / `trips.yaml` need no restart.
