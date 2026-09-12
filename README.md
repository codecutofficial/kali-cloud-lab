# kali-cloud-lab

Spin up a **temporary Kali Linux desktop on GitHub Actions** and reach it from anywhere — a full **KDE desktop with a taskbar**, from the maintained [LinuxServer.io Kali image](https://docs.linuxserver.io/images/docker-kali-linux/). No account, no secrets, nothing you must install.

Two ways in, and every run gives you both:

- **Native RDP** — `mstsc`, Remmina, FreeRDP. Port 3389 is tunnelled out with [bore](https://github.com/ekzhang/bore).
- **Browser** — the image's own web desktop through a **Cloudflare quick tunnel**. Zero setup.

Ephemeral by design: a GitHub Actions job is capped at **6 hours**, then everything is destroyed. Throwaway lab, not persistent hosting.

---

## How to use it

1. **Actions → "Kali Linux (RDP + browser desktop)" → Run workflow** → branch `main` → **Run workflow**. (Manual only — a push never starts a box.) Leave **rdp** ticked unless you only want the browser route.
2. First run takes **~5–10 min** (it pulls a multi-GB image and boots a full desktop). When it reaches the last step, open the run's **Summary** tab (top of the run page). It shows both addresses:
   ```
   🐉 Kali Linux desktop is live

   ⚡ Remote Desktop        bore.pub:<port>              abc / <password>
   🌐 Browser desktop       https://<random>.trycloudflare.com   kali / <password>
   ```
3. Paste the `bore.pub:PORT` into an RDP client, **or** open the `https://` link in a browser.

No scrolling logs — both addresses are in the **Summary tab** (and echoed at the bottom of the last step).

> **The two logins are different accounts.** RDP signs in as **`abc`**, the real Linux user.
> `kali` is only the browser page's HTTP login. Same machine, same files, same home directory.

### Which route should you use?

Worth actually testing rather than assuming — it depends on where you are:

| | Native RDP (bore) | Browser (Cloudflare) |
|---|---|---|
| Setup | an RDP client | none |
| Protocol | RDP — caches bitmaps locally, sizes to your window | H.264 stream, re-encoded server-side |
| Network path | one relay in **New Jersey** | **Cloudflare's nearest edge to you** |
| Desktop | XFCE (light, cheap to redraw) | KDE Plasma |

RDP is the better protocol; Cloudflare is usually the shorter path. If you're far from the US
the detour can cost more than the protocol saves, so open both, drag a window around in each,
and keep whichever feels better.

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
- **Two desktops, one machine.** The browser gets KDE Plasma (Wayland); RDP gets its own XFCE session. xrdp is an X11 server and can't attach to a Wayland session, so it starts its own — XFCE by choice, since it's much cheaper to redraw over a tunnel. Both run as `abc` and share `/config`, so your files and tools are the same either way.
- **Public link + passwordless root.** The repo is **public**, so the links and passwords sit in publicly viewable run output while the job runs, and the desktop terminal has **passwordless `sudo`**. `bore.pub` is a free public relay, so while the run is live the RDP port is reachable by anyone who reads that output. Treat the box as fully exposed — don't put anything sensitive in it. For privacy, make the repo **private**.
- **GitHub Actions Terms.** Actions is meant for building/testing/deploying the repo's own software; using it as a remote-desktop host is a gray area under GitHub's Acceptable Use Policies. Keep it to legitimate, authorized use — learning, CTFs, and testing systems **you're allowed to test**.
- **Nothing persists** between runs.

## What's in here

```
.github/workflows/kali-gui.yml        # Kali desktop — xrdp/bore + LinuxServer image/cloudflared
.github/workflows/windows-vm.yml      # Windows VM (dockur/windows + Guacamole HTML5 RDP)
.github/workflows/windows-desktop.yml # legacy: windows-latest console over noVNC
windows/                              # Windows lab guide + tuning scripts
README.md
```

Both labs have their own workflow and their own `concurrency` group — so a Kali box and a
Windows box can run **at the same time** without cancelling each other. Neither starts on a
push; you launch them from the Actions tab.

### 🪟 Windows lab

A temporary **Windows VM**, hosted the same way as Kali — Docker containers on a Linux runner.
A real Windows VM (`dockur/windows`, KVM-accelerated) that you reach two ways:

- **Native Remote Desktop** (`mstsc`) — the fast path. The runner has no inbound IP, so port
  3389 is tunnelled out. Every run offers **both** relays and you use whichever you prefer:
  - **bore** — on by default, nothing to install. A `bore.pub:PORT` you paste into `mstsc`.
    The port changes each run, and it needs a one-time client tweak (it relays TCP only).
  - **Tailscale** — set a `TS_AUTHKEY` secret once and you also get a fixed
    `winlab.<tailnet>.ts.net:3389`: same address every run, never exposed to the internet,
    and it carries UDP, so it's usually the smoother of the two.
- **Browser** — **Apache Guacamole** renders the same RDP session as HTML5 over cloudflared,
  for when you can't install a client. Slower, since the server re-encodes every frame.

**No VNC.** See **[windows/README.md](windows/README.md)**.

Start it: **Actions → "Windows VM (Guacamole HTML5 via Cloudflare)" → Run workflow**, then take
the RDP address + logins from that run's **Summary** tab. Windows installs itself first, so the
desktop is ready after **~15–30 min**.
