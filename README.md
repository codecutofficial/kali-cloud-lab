# kali-cloud-lab

Spin up a **temporary Kali Linux desktop on GitHub Actions** and open it in your **browser** from anywhere — a full **KDE desktop with a taskbar**, served over **KasmVNC** by the maintained [LinuxServer.io Kali image](https://docs.linuxserver.io/images/docker-kali-linux/) and exposed through a **Cloudflare quick tunnel** (no account, no secrets, nothing to install locally).

Ephemeral by design: a GitHub Actions job is capped at **6 hours**, then everything is destroyed. Throwaway lab, not persistent hosting.

---

## How to use it

1. **Actions → "Kali Linux GUI (LinuxServer desktop via Cloudflare)" → Run workflow** → branch `main` → **Run workflow**. (Manual only — a push never starts a box.)
2. First run takes **~5–10 min** (it pulls a multi-GB image and boots a full desktop). When it reaches the last step, open the run's **Summary** tab (top of the run page). It shows:
   ```
   🐉 Kali Linux desktop is live
   Open in any browser:
       https://<random>.trycloudflare.com
   user: kali
   password: <shown here>
   ```
3. Click the link → your browser prompts for the login above → the **Kali KDE desktop** loads right in the tab.

No scrolling logs — the link + login are in the **Summary tab** (and echoed at the bottom of the last step).

## Ending the box early

- Cancel the workflow run from the Actions tab. Otherwise it auto-stops at ~6h.
- A new run auto-cancels an older in-progress one (via a `concurrency` group), so boxes don't pile up.

## Installing more tools (in a terminal on the desktop)

Open the terminal from the taskbar, then:

```bash
sudo apt update
sudo apt install -y metasploit-framework sqlmap gobuster   # etc.
sudo apt install -y kali-linux-headless                    # full metapackage
```

---

## Notes & caveats

- **It IS Kali** — the desktop runs the `lscr.io/linuxserver/kali-linux` image; `cat /etc/os-release` shows `Kali GNU/Linux Rolling`. `uname -r` reports an `-azure` kernel because *every container shares the host kernel* (GitHub runners are Azure VMs); there is no separate "Kali kernel" in a container. The Kali userland/tools are the real thing.
- **Public link + passwordless root.** The repo is **public**, so the link and password sit in publicly viewable run output while the job runs, and the desktop terminal has **passwordless `sudo`**. Treat the box as fully exposed — don't put anything sensitive in it. For privacy, make the repo **private**.
- **GitHub Actions Terms.** Actions is meant for building/testing/deploying the repo's own software; using it as a remote-desktop host is a gray area under GitHub's Acceptable Use Policies. Keep it to legitimate, authorized use — learning, CTFs, and testing systems **you're allowed to test**.
- **Nothing persists** between runs.

## What's in here

```
.github/workflows/kali-gui.yml        # Kali Linux desktop (LinuxServer image + cloudflared)
.github/workflows/windows-vm.yml      # Windows VM (dockur/windows + Guacamole HTML5 RDP)
.github/workflows/windows-desktop.yml # legacy: windows-latest console over noVNC
windows/                              # Windows lab guide + tools.ps1
README.md
```

Both labs have their own workflow and their own `concurrency` group — so a Kali box and a
Windows box can run **at the same time** without cancelling each other. Neither starts on a
push; you launch them from the Actions tab.

### 🪟 Windows lab

A temporary **Windows VM**, hosted the same way as Kali — Docker containers on a Linux runner.
A real Windows VM (`dockur/windows`, KVM-accelerated) that you reach two ways:

- **Native Remote Desktop** (`mstsc`) — the fast path. The runner has no inbound IP, so it
  tunnels port 3389 out through **bore** (zero setup, a `bore.pub:PORT` you paste into `mstsc`)
  or, if you set a `TS_AUTHKEY` secret, **Tailscale** (a fixed `winlab.<tailnet>.ts.net:3389`
  that's the same every run and never exposed to the internet).
- **Browser** — **Apache Guacamole** renders the same RDP session as HTML5 over cloudflared,
  for when you can't install a client. Slower, since the server re-encodes every frame.

**No VNC.** See **[windows/README.md](windows/README.md)**.

Start it: **Actions → "Windows VM (Guacamole HTML5 via Cloudflare)" → Run workflow**, then take
the RDP address + logins from that run's **Summary** tab. Windows installs itself first, so the
desktop is ready after **~15–30 min**.
