# kali-cloud-lab

Spin up a **temporary Kali Linux box on GitHub Actions** and get a **public browser link** to use it from anywhere — a web terminal (`ttyd`) exposed through a **Cloudflare quick tunnel** (no account, no secrets, no SSH client needed).

Ephemeral by design: a GitHub Actions job is capped at **6 hours**, then everything is destroyed. This is a throwaway lab, not persistent hosting.

---

## How to use it

1. It runs automatically on every push to `main`. To start one manually:
   **Actions → "Kali Linux (web terminal via Cloudflare)" → Run workflow**.
   - Optional toggle **full_toolset** installs `kali-linux-headless` (big, ~5–10 min). Off by default.
2. Open the running job. When it reaches **Launch web terminal + public tunnel**, go to the run's **Summary** tab (top of the run page). It shows:
   ```
   🐉 Your Kali Linux is live
   Open in any browser, from anywhere:
       https://<random-words>.trycloudflare.com
   Login — user: kali · password: <shown here>
   ```
3. Open that link, enter the login, and you're in the **Kali root shell**. Your repo is mounted at `/work`.

No scrolling through logs — the link is in the **Summary tab** and also echoed at the bottom of that step.

## Ending the box early

- Cancel the workflow run from the Actions tab. Otherwise it auto-stops at ~6h.

## Installing more tools

In the Kali shell:
```bash
apt-get update
apt-get install -y metasploit-framework sqlmap gobuster   # etc.
apt-get install -y kali-linux-headless                    # big metapackage
```

---

## ⚠️ Read this

- **The link is unauthenticated beyond the basic-auth login shown in the run.** Because this repo is **public**, that link and its password sit in **publicly viewable logs/summary** while the job runs — so treat it as exposed. If that matters:
  - Make the repo **private**, or
  - Remove the tunnel and use SSH-key-gated access instead.
- **GitHub Actions Terms.** Actions is meant for building/testing/deploying the repo's own software; using it as a general remote-access host is a gray area under GitHub's Acceptable Use Policies. Keep this to legitimate, authorized use — learning, CTFs, and security testing on systems **you are allowed to test**. Don't point it at third parties.
- **Nothing persists** between runs except what you commit to the repo.

## What's in here

```
.github/workflows/kali-web.yml   # the whole thing (ttyd + cloudflared + Kali)
README.md
```
