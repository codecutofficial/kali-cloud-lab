# kali-cloud-lab

Spin up a **temporary Kali Linux desktop on GitHub Actions** and open it in your **browser** from anywhere — a full **KDE desktop with a taskbar**, served over **KasmVNC** by the maintained [LinuxServer.io Kali image](https://docs.linuxserver.io/images/docker-kali-linux/) and exposed through a **Cloudflare quick tunnel** (no account, no secrets, nothing to install locally).

Ephemeral by design: a GitHub Actions job is capped at **6 hours**, then everything is destroyed. Throwaway lab, not persistent hosting.

---

## How to use it

1. Runs automatically on every push to `main`. To start one manually:
   **Actions → "Kali Linux GUI (LinuxServer desktop via Cloudflare)" → Run workflow**.
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
.github/workflows/kali-gui.yml   # the whole thing (LinuxServer Kali desktop + cloudflared)
README.md
```
