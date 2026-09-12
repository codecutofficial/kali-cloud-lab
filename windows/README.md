# Windows lab

A temporary **Windows desktop in your browser** — hosted the same way as the Kali lab:
Docker containers on a Linux runner, published through a **Cloudflare quick tunnel**.

**No VNC anywhere.** The browser gets an **HTML5 RDP** session via
[Apache Guacamole](https://guacamole.apache.org/), which is why it's responsive, auto-fits
the resolution to your browser window, and doesn't drop the session.

```
dockur/windows   →  a real Windows VM (KVM-accelerated QEMU), speaking RDP
guacd            →  Guacamole's RDP proxy
guacamole        →  renders that RDP session as HTML5        (port 8080)
cloudflared      →  makes it public
```

> Workflows only run from `.github/workflows/`, so the runnable file is
> [`.github/workflows/windows-vm.yml`](../.github/workflows/windows-vm.yml).
> This folder holds the docs and helper scripts.

---

## Start it

1. **Actions → "Windows VM (Guacamole HTML5 via Cloudflare)" → Run workflow**.
   - **version** — `11l` (Windows 11 LTSC, the default — smallest full desktop), `11`, `10l`,
     `10`, `2022`, `2025`, or `tiny11`.
   - **ram** / **cores** — default `8G` / `4`.
2. Open the run's **Summary** tab. Within ~2 min it shows your desktop link, the Guacamole
   login, and a second link for watching the install.
3. **Windows installs itself first — typically 15–30 min.** The Summary tab adds a
   "✅ Windows finished installing" line when the desktop is actually ready.
4. Open the link → sign in with the Guacamole login → click **Windows**.

That wait is the one real cost of this approach. It buys you a genuine VM with a proper
desktop, instead of a laggy stream of a CI machine's console.

## Full-speed native RDP (optional)

The browser session is good, but a native RDP client is better still. Port 3389 is published
on the runner, so with [cloudflared](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/)
installed locally you can add a TCP tunnel and point `mstsc` at it. Sign in as `Docker`
with the Windows password from the Summary tab.

## Stopping it

- Click **Cancel run** on the run page (or `gh run cancel <id> --repo <owner>/<repo>`).
- Otherwise it stops itself at ~6h.
- Its `concurrency` group is `windows-vm`, separate from Kali's — both labs can run at once.

---

## Notes & caveats

- **Nothing persists.** Every run installs Windows from scratch. This is a throwaway lab.
- **Public link.** In a public repo the link and passwords sit in publicly viewable run output
  while the job runs. Treat the box as fully exposed — nothing sensitive goes in it. Make the
  repo private if you want the output hidden.
- **GitHub Actions Terms.** Actions is for building/testing/deploying the repo's own software;
  using it as a remote-desktop host is a gray area under GitHub's Acceptable Use Policies. Keep
  it to legitimate, authorized use.
- **Minutes.** Public repos get unlimited Actions minutes. On a **private** repo this burns
  standard Linux minutes for as long as the box is up.
- **Windows licensing** is your responsibility — these are Microsoft's own evaluation images,
  unactivated.

## Legacy workflow

[`.github/workflows/windows-desktop.yml`](../.github/workflows/windows-desktop.yml) is the
earlier approach: it streams the **`windows-latest` runner's own console** over TightVNC +
noVNC. It starts in ~4 min with no install wait, but the stream is laggy, the resolution is
fixed, and sessions drop — which is exactly why the VM + Guacamole workflow above replaced it.
Kept only as a fast fallback.
