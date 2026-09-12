# Windows lab

A temporary **Windows VM** — hosted the same way as the Kali lab: Docker containers on a
Linux runner, reached through Tailscale.

**Tailscale only** — nothing is exposed to the public internet. No bore, no Cloudflare,
no browser route. Only devices on your Tailscale network can reach the VM.

```
dockur/windows   →  a real Windows VM (KVM-accelerated QEMU), speaking RDP
Tailscale        →  private WireGuard mesh, fixed address every run
```

> Workflows only run from `.github/workflows/`, so the runnable file is
> [`.github/workflows/windows-vm.yml`](../.github/workflows/windows-vm.yml).
> This folder holds the docs and helper scripts.

---

## Prerequisites

One-time setup — takes ~2 minutes:

1. **Sign up** at [tailscale.com](https://tailscale.com) — free, no card.
2. **Install Tailscale** on your PC and sign in. Leave it running.
3. **Generate an auth key**: [Admin console](https://login.tailscale.com/admin/settings/keys)
   → **Generate auth key** → tick **Ephemeral** + **Reusable** → copy.
4. **Add repo secret**: repo → **Settings → Secrets and variables → Actions →
   New repository secret** → name: `TS_AUTHKEY`, value: the key.

Without `TS_AUTHKEY`, the workflow fails immediately.

---

## Start it

1. **Actions → "Windows VM (Tailscale RDP)" → Run workflow**.
   - **version** — `11l` (Windows 11 LTSC, the default — smallest full desktop), `11`, `10l`,
     `10`, `2022`, `2025`, or `tiny11`.
   - **ram** / **cores** — default `12G` / `3`.
2. Open the run's **Summary** tab. Within ~2 min it shows the RDP address and password.
3. **Windows installs itself first — typically 15–30 min.** The Summary adds a
   "✅ Windows finished installing" line when the desktop actually answers.
4. Connect with `mstsc`.

## ⚡ Connecting

1. Make sure Tailscale is running on your PC (tray icon → "Connected").
2. Press **Win key** → type `mstsc` → Enter.
3. Paste the address from the Summary tab:
   ```
   winlab.<your-tailnet>.ts.net:3389
   ```
4. Username: `Docker`, password from Summary.

This address is **the same every run** — save it in `mstsc` once and reuse it forever.

> Tailscale carries **UDP**, so RDP's fast path (bitmap caching + compression) works at
> full speed. No client-side UDP tweaks needed.
>
> **If you previously disabled client-side UDP for bore**, re-enable it:
> ```powershell
> Set-ItemProperty -Path 'HKLM:\SOFTWARE\Policies\Microsoft\Windows NT\Terminal Services\Client' `
>   -Name fClientDisableUDP -Value 0 -Type DWord
> ```

## Stopping it

- Click **Cancel run** on the run page (or `gh run cancel <id> --repo <owner>/<repo>`).
- Otherwise it stops itself at ~6h.
- Its `concurrency` group is `windows-vm`, separate from Kali's — both labs can run at once.

---

## Notes & caveats

- **Nothing persists.** Every run installs Windows from scratch. This is a throwaway lab.
- **Private.** Only devices on your Tailscale network can reach the VM. Nothing is exposed
  to the public internet — no public links, no public relay, no browser route.
- **GitHub Actions Terms.** Actions is for building/testing/deploying the repo's own software;
  using it as a remote-desktop host is a gray area under GitHub's Acceptable Use Policies. Keep
  it to legitimate, authorized use.
- **Minutes.** Public repos get unlimited Actions minutes. On a **private** repo this burns
  standard Linux minutes for as long as the box is up.
- **Windows licensing** is your responsibility — these are Microsoft's own evaluation images,
  unactivated.
- **Ephemeral nodes.** The key is ephemeral, so each run's node removes itself from your
  tailnet afterwards; the workflow also runs `tailscale logout` on the way out so the name
  stays `winlab` rather than drifting to `winlab-1`.

## Legacy workflow

[`.github/workflows/windows-desktop.yml`](../.github/workflows/windows-desktop.yml) is the
earlier approach: it streams the **`windows-latest` runner's own console** over TightVNC +
noVNC. Disabled — kept only as a reference.
