# Windows lab

A temporary **Windows VM** — hosted the same way as the Kali lab: Docker containers on a
Linux runner, reached through an outbound tunnel.

Two ways in, and the run gives you both:

- **Native Remote Desktop** (`mstsc`) — the fast one. Use this.
- **Browser** — HTML5 RDP via [Apache Guacamole](https://guacamole.apache.org/), for when
  you can't install anything locally. Slower, because the server re-encodes every frame.

**No VNC anywhere.**

```
dockur/windows   →  a real Windows VM (KVM-accelerated QEMU), speaking RDP
                       ├─ bore / Tailscale  →  native RDP to your mstsc   ⚡
                       └─ guacd + guacamole →  HTML5 in a browser   (8080)
cloudflared      →  makes the browser route public
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
2. Open the run's **Summary** tab. Within ~2 min it shows the RDP address, the browser link,
   and the logins.
3. **Windows installs itself first — typically 15–30 min.** The Summary adds a
   "✅ Windows finished installing" line when the desktop actually answers.
4. Connect with `mstsc` (below) or the browser link.

That wait is the one real cost of this approach. It buys you a genuine VM with a proper
desktop, instead of a laggy stream of a CI machine's console.

## ⚡ Native Remote Desktop (recommended — it's the fast one)

The browser session re-encodes every frame on the server, which is where the lag comes from.
A real RDP client talks RDP end to end, sizes itself to your window, and caches bitmaps
locally. Same VM, dramatically better feel.

The runner sits behind Azure NAT with **no inbound-reachable IP**, so you can't dial it
directly — no port-forward or firewall rule exists for you to open. Something has to dial
*out* and relay. The workflow sets up whichever of these is available:

### bore — nothing to install (default)

Already on by default. The Summary tab shows:

```
bore.pub:41337
```

Press **Windows key**, type `mstsc`, Enter, and paste that into **Computer**. Sign in as
`Docker` with the password from the Summary tab.

> It is a `host:port` pair — **not** an `https://` link. Pasting a `trycloudflare.com` URL
> into `mstsc` gives *"The remote computer name is not valid"*; that link is for a browser.

#### Required one-time PC setup: turn off client-side UDP

Do this once or the connection will hang at *"Configuring remote session…"* and then fail
with *"This computer can't connect to the remote computer."*

`mstsc` tries to open a **UDP** transport alongside TCP. bore relays **TCP only**, so that
UDP channel never answers and the client waits on it until it gives up. In an **admin**
PowerShell:

```powershell
New-Item -Path 'HKLM:\SOFTWARE\Policies\Microsoft\Windows NT\Terminal Services\Client' -Force | Out-Null
Set-ItemProperty -Path 'HKLM:\SOFTWARE\Policies\Microsoft\Windows NT\Terminal Services\Client' `
  -Name fClientDisableUDP -Value 1 -Type DWord
```

This only affects how your client negotiates transport; TCP-based RDP is unaffected, so it
is safe to leave set. (Tailscale carries UDP fine and doesn't need this.)

The other catch: **the port is different every run**, so you copy it from the Summary each
time. `bore.pub` is also a free community relay — if it's having a bad day, the workflow
reconnects automatically and posts the new port as a warning annotation.

### Tailscale — a fixed address that never changes (optional, free)

If re-copying the port annoys you, this removes that step permanently. One-time setup:

1. Sign up at [tailscale.com](https://tailscale.com) (free, personal use, no card).
2. Install Tailscale on your PC and sign in. Leave it running — that's the only local step,
   and you do it **once**, not per run.
3. Admin console → **Settings → Keys → Generate auth key**. Turn on **Ephemeral** and
   **Reusable**. Copy the key.
4. In this repo: **Settings → Secrets and variables → Actions → New repository secret**,
   named `TS_AUTHKEY`, pasting that key as the value.

From then on every run registers itself as `winlab` and the Summary shows a constant address:

```
winlab.your-tailnet.ts.net:3389
```

Save it in `mstsc` once and reuse it forever. It's also **private** — the port is never
exposed to the internet, only to your own devices, unlike bore and the browser link.

The key is *ephemeral*, so each run's node removes itself from your tailnet afterwards; the
workflow also runs `tailscale logout` on the way out so the name stays `winlab` rather than
drifting to `winlab-1`. Keep the key in the repo secret — never in the workflow file.

## Browser route (slower, but zero setup)

The Summary's `trycloudflare.com` link opens the same desktop through Guacamole's HTML5
client. Sign in with the `guacadmin` password from the Summary, then click **Windows**. Use
this when you're on a machine where you can't install an RDP client.

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
- **bore.pub is a public relay.** Your RDP port is open to the internet while the run is live,
  and the password is in the public run output, so assume anyone could reach it. The Windows
  password is random per run, which is the only thing in front of it. Tailscale avoids this
  entirely — nothing is internet-exposed there.
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
