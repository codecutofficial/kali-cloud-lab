# kali-cloud-lab

Spin up a **temporary Kali Linux GUI desktop on GitHub Actions** and open it in your **browser** from anywhere — a full **XFCE desktop** served over **noVNC** and exposed through a **Cloudflare quick tunnel** (no account, no secrets, no VNC client to install).

Ephemeral by design: a GitHub Actions job is capped at **6 hours**, then everything is destroyed. Throwaway lab, not persistent hosting.

---

## How to use it

1. Runs automatically on every push to `main`. To start one manually:
   **Actions → "Kali Linux GUI (noVNC via Cloudflare)" → Run workflow**.
   - **full_toolset** (optional): also installs `kali-linux-headless` (big arsenal, +~10 min).
   - **geometry** (optional): desktop resolution, default `1360x768`.
2. First run takes **~10–15 min** (desktop + tools install). When it reaches the last step, open the run's **Summary** tab (top of the run page). It shows:
   ```
   🐉 Kali Linux GUI is live
   Open the desktop in any browser (autoconnects):
       https://<random>.trycloudflare.com/vnc.html?autoconnect=true&resize=scale&password=<pass>
   VNC password: <shown here>
   ```
3. Click the link → the **Kali XFCE desktop** loads right in the browser. Your repo is mounted at `/work`.

No scrolling logs — the link + password are in the **Summary tab** (and echoed at the bottom of the last step).

## Ending the box early

- Cancel the workflow run from the Actions tab. Otherwise it auto-stops at ~6h.
- A new run auto-cancels an older in-progress one (via a `concurrency` group), so boxes don't pile up.

## Installing more tools (in a terminal on the desktop)

```bash
apt update
apt install -y metasploit-framework sqlmap gobuster burpsuite   # etc.
apt install -y kali-linux-headless                              # full metapackage
```

---

## Notes & caveats

- **It IS Kali** — `cat /etc/os-release` shows `Kali GNU/Linux Rolling`. `uname -r` shows an `-azure` kernel because *every container shares the host kernel* (GitHub runners are Azure VMs); there's no separate "Kali kernel" in a container. The Kali userland/tools are the real thing.
- **Public link.** Because the repo is **public**, the link + VNC password sit in publicly viewable run output while the job runs — treat the box as exposed and don't put anything sensitive in it. For privacy, make the repo **private**.
- **GitHub Actions Terms.** Actions is meant for building/testing/deploying the repo's own software; using it as a remote-desktop host is a gray area under GitHub's Acceptable Use Policies. Keep it to legitimate, authorized use — learning, CTFs, and testing systems **you're allowed to test**.
- **Nothing persists** between runs except what you commit to the repo.

## What's in here

```
.github/workflows/kali-gui.yml   # the whole thing (XFCE + TigerVNC + noVNC + cloudflared)
README.md
```
