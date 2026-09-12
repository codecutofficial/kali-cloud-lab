# Setup Guide

Two labs, three connection methods. This page walks through every way in and rates them.

---

## Kali Linux

**Workflow**: Actions → **"Kali Linux (RDP + browser desktop)"** → Run workflow

First run takes ~5–10 min (pulls a multi-GB image). After that, both addresses appear in
the run's **Summary** tab.

### Method 1 — Native RDP via bore (recommended)

| | |
|---|---|
| Speed | ⚡⚡⚡⚡ Fast — RDP protocol caches bitmaps locally |
| Setup | Install an RDP client (Windows has `mstsc` built in) |
| Address | `bore.pub:<port>` — **changes every run**, copy from Summary |
| Desktop | XFCE (lightweight, cheap to redraw over a tunnel) |
| Login | `abc` / password from Summary |

**How to connect:**

1. Open the run's **Summary** tab and copy the `bore.pub:<port>` address.
2. Press **Win key** → type `mstsc` → Enter.
3. Paste the address into **Computer** → Connect.
4. Accept the certificate warning (self-signed cert, expected).
5. Username: `abc`, password from Summary.

> **First-time setup (Windows):** bore relays TCP only — you must disable client-side UDP
> or the connection will hang at "Configuring remote session…".
>
> Run once in an **admin PowerShell**:
> ```powershell
> New-Item -Path 'HKLM:\SOFTWARE\Policies\Microsoft\Windows NT\Terminal Services\Client' -Force | Out-Null
> Set-ItemProperty -Path 'HKLM:\SOFTWARE\Policies\Microsoft\Windows NT\Terminal Services\Client' `
>   -Name fClientDisableUDP -Value 1 -Type DWord
> ```
> Safe to leave set — it only affects transport negotiation.

> **On Linux/macOS:** use Remmina or FreeRDP:
> ```bash
> xfreerdp /v:bore.pub:<port> /u:abc /p:<password>
> ```

### Method 2 — Browser via Cloudflare (zero setup)

| | |
|---|---|
| Speed | ⚡⚡⚡ Good — Cloudflare edge is usually close to you |
| Setup | None — just a browser |
| Address | `https://<random>.trycloudflare.com` from Summary |
| Desktop | KDE Plasma (full desktop, Wayland) |
| Login | `kali` / password from Summary |

**How to connect:**

1. Open the run's **Summary** tab and click the `trycloudflare.com` link.
2. Username: `kali`, password from Summary.
3. Full KDE desktop loads in your browser.

### Which is faster?

**RDP via bore wins on protocol** — it caches bitmaps locally and sizes to your window,
while the browser re-encodes every frame server-side. But bore routes through a single
server in **New Jersey**, while Cloudflare picks an **edge near you**.

- **Close to the US**: RDP is noticeably faster.
- **Far from the US** (India, Asia, Europe): the network detour can cancel out the
  protocol advantage. Open both, drag a window around in each, keep the winner.

> Both are the same machine, same user (`abc`), same files. Only the desktop environment
> and the network path differ.

---

## Windows VM

**Workflow**: Actions → **"Windows VM (Guacamole HTML5 via Cloudflare)"** → Run workflow

Windows installs itself first — typically **15–30 min**. The Summary shows addresses
immediately, but RDP won't answer until the install finishes (a "Windows finished
installing" line appears when it's ready). You can watch the install via the browser link.

### Method 1 — Tailscale RDP (recommended — fastest)

| | |
|---|---|
| Speed | ⚡⚡⚡⚡⚡ Fastest — picks a relay near you + carries UDP |
| Setup | One-time: Tailscale account + `TS_AUTHKEY` repo secret |
| Address | `winlab.<tailnet>.ts.net:3389` — **same address every run** |
| Exposure | Private — only your own devices can reach it |
| Login | `Docker` / password from Summary |

**One-time setup (do this once, never again):**

1. **Sign up** at [tailscale.com](https://tailscale.com) — free, no card.
2. **Install Tailscale** on your PC and sign in. Leave it running.
3. **Generate an auth key**: [Admin console](https://login.tailscale.com/admin/settings/keys)
   → **Generate auth key** → tick **Ephemeral** + **Reusable** → copy.
4. **Add repo secret**: repo → **Settings → Secrets and variables → Actions →
   New repository secret** → name: `TS_AUTHKEY`, value: the key.

**How to connect:**

1. Make sure Tailscale is running on your PC (tray icon → "Connected").
2. Open `mstsc` → paste `winlab.<your-tailnet>.ts.net:3389`.
3. Username: `Docker`, password from Summary.

> Tailscale carries **UDP**, so RDP's fast path (bitmap caching + compression) works at
> full speed. The address never changes across runs — save it in `mstsc` once.
>
> **If you previously disabled client-side UDP for bore**, re-enable it for Tailscale:
> ```powershell
> Set-ItemProperty -Path 'HKLM:\SOFTWARE\Policies\Microsoft\Windows NT\Terminal Services\Client' `
>   -Name fClientDisableUDP -Value 0 -Type DWord
> ```

### Method 2 — bore RDP (no setup needed)

| | |
|---|---|
| Speed | ⚡⚡⚡⚡ Fast — RDP protocol, but TCP only via New Jersey |
| Setup | None — always on |
| Address | `bore.pub:<port>` — **changes every run** |
| Exposure | Public relay — open to the internet while live |
| Login | `Docker` / password from Summary |

**How to connect:**

1. Copy the `bore.pub:<port>` from the Summary tab.
2. Open `mstsc` → paste it into **Computer** → Connect.
3. Username: `Docker`, password from Summary.

> Requires the same UDP-disable tweak as Kali bore (see above). bore relays TCP only.

### Method 3 — Browser via Guacamole + Cloudflare (zero setup)

| | |
|---|---|
| Speed | ⚡⚡ Slowest — server re-encodes every RDP frame as HTML5 |
| Setup | None — just a browser |
| Address | `https://<random>.trycloudflare.com` from Summary |
| Login | `guacadmin` / password from Summary, then click **Windows** |

**How to connect:**

1. Click the `trycloudflare.com` link from the Summary tab.
2. Sign in: `guacadmin` / password from Summary.
3. Click **Windows** to open the desktop.

> Use this only when you can't install an RDP client. Every frame is decoded from RDP,
> re-encoded to H.264, and streamed to your browser — that double-encode is where the
> lag comes from.

---

## Speed Rankings

| Rank | Method | Lab | Why |
|------|--------|-----|-----|
| 1 | **Tailscale RDP** | Windows | UDP + nearby relay + native RDP protocol |
| 2 | **bore RDP** | Kali / Windows | Native RDP, but TCP-only via New Jersey |
| 3 | **Cloudflare browser** | Kali | Cloudflare edge is close, decent H.264 stream |
| 4 | **Guacamole browser** | Windows | Double re-encode (RDP → H.264 → browser) |

> If you're **far from the US**, Cloudflare browser (Kali) might beat bore RDP because
> Cloudflare routes through an edge near you. Test both.

---

## Quick Reference

| | Kali | Windows |
|---|---|---|
| Workflow | "Kali Linux (RDP + browser desktop)" | "Windows VM (Guacamole HTML5 via Cloudflare)" |
| Startup time | ~5–10 min | ~15–30 min (Windows install) |
| RDP user | `abc` | `Docker` |
| Browser user | `kali` | `guacadmin` |
| Tailscale | not available | `winlab.<tailnet>.ts.net:3389` |
| bore | `bore.pub:<port>` | `bore.pub:<port>` |
| Browser | `trycloudflare.com` link | `trycloudflare.com` link |
| Auto-stop | ~6 hours | ~6 hours |
| Persists data | no | no |

Passwords are random per run — always check the **Summary** tab.
