# Windows lab

A temporary **Windows Server desktop in your browser**, running on GitHub Actions.

Unlike the Kali lab, nothing gets downloaded or installed to *become* Windows — GitHub Actions
already gives you a **real `windows-latest` runner** (Windows Server 2022/2025, 4 vCPU, 16 GB RAM).
This lab just streams the desktop that's already sitting there:

```
runner console session  ──TightVNC──>  :5900  ──websockify/noVNC──>  :6080  ──cloudflared──>  https://<random>.trycloudflare.com
                        ──RDP────────>  :3389  ──cloudflared (tcp)──>  optional full-speed client
```

Ephemeral: a job is capped at **6 hours**, then everything is destroyed.

> The runnable workflow lives at [`.github/workflows/windows-desktop.yml`](../.github/workflows/windows-desktop.yml)
> — GitHub only executes workflows from `.github/workflows/`, so it can't live in this folder.
> This folder holds the docs and helper scripts.

---

## Start it

1. **Actions → "Windows Desktop (noVNC via Cloudflare)" → Run workflow** → branch `main` → **Run workflow**.
2. Wait **~3–5 min**, then open the run's **Summary** tab. It shows:
   ```
   🪟 Windows desktop is live
   Open the desktop in any browser (autoconnects):
       https://<random>.trycloudflare.com/vnc.html?autoconnect=true&resize=scale&password=<pass>
   VNC password: <shown here>

   Windows sign-in (only needed if the session locks)
   user: runneradmin   password: <shown here>
   ```
3. Click the link → the Windows desktop loads in the tab.

The link and passwords are **new every run**. Always take them from the Summary tab of that run.

## Full-speed RDP (optional)

noVNC in the browser is fine for clicking around but is slow to redraw. For a real desktop
experience, the workflow also opens a TCP tunnel for RDP (input `expose_rdp`, on by default).
You need [cloudflared](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/)
installed locally, then:

```bash
cloudflared access rdp --hostname <rdp-hostname-from-summary> --url localhost:33389
```

Now point any Remote Desktop client at **localhost:33389** and sign in with the Windows
credentials from the Summary tab.

## Installing tools on the box

Chocolatey is preinstalled on the runner. In a PowerShell window on the desktop:

```powershell
choco install -y firefox vscode 7zip notepadplusplus
```

Or run the bundled helper (the repo is checked out on the runner):

```powershell
powershell -ExecutionPolicy Bypass -File windows\tools.ps1
```

## Stopping it

- Click **Cancel run** on the run page (or `gh run cancel <id> --repo <owner>/<repo>`).
- Otherwise it stops itself at ~6h.
- A new run auto-cancels an older one (`concurrency` group `windows-desktop`), which is
  **separate** from the Kali group — so a Windows box and a Kali box can run at the same time.

---

## Notes & caveats

- **Black screen / lock screen?** The stream shows the *console session*. The workflow disables
  sleep, monitor blanking and the lock screen for this reason. If you ever land on a lock screen,
  sign in with the Windows credentials from the Summary tab.
- **Public link.** In a public repo the link and passwords sit in publicly viewable run output
  while the job runs, and the desktop account is a local admin. Treat the box as fully exposed —
  nothing sensitive goes in it. Make the repo private if you want the output hidden.
- **GitHub Actions Terms.** Actions is for building/testing/deploying the repo's own software;
  using it as a remote-desktop host is a gray area under GitHub's Acceptable Use Policies. Keep it
  to legitimate, authorized use.
- **Minutes.** Public repos get unlimited Actions minutes. On a **private** repo, Windows runners
  bill at **2× the Linux rate**, so a 6h box burns ~720 minutes of quota.
- **Nothing persists** between runs.
