# kali-cloud-lab

Spin up a **temporary Kali Linux box on GitHub Actions** and get a **public link** (SSH + browser terminal) to use it from anywhere — powered by [`mxschmitt/action-tmate`](https://github.com/mxschmitt/action-tmate).

The box is ephemeral: a GitHub Actions job is capped at **6 hours**, then everything is destroyed. This is a throwaway lab, not persistent hosting.

---

## How to use it

1. Go to the **Actions** tab of this repo.
2. It also runs automatically on every push to `main`.
3. To start one manually: **Actions → "Kali Linux (tmate remote access)" → Run workflow**.
   - Optional toggle: **full_toolset** installs `kali-linux-headless` (big, ~5–10 min). Off by default (a light, fast toolset).
4. Open the running job → the **Start tmate session** step. It prints, and refreshes every few seconds:
   ```
   SSH: ssh <random>@nyc1.tmate.io
   Web: https://tmate.io/t/<random>
   ```
5. Click the **Web** link → a terminal opens in your browser (works on any device).
6. In that terminal, type:
   ```
   kali
   ```
   That drops you into the **Kali Linux** root shell. Your repo files are mounted at `/work` inside it.

## Ending the box early

- Run `touch /continue` inside the session, **or**
- Cancel the workflow run from the Actions tab.

Otherwise it stops on its own at the 6-hour limit.

## Installing more tools

Inside the Kali shell:
```bash
apt-get update
apt-get install -y <tool>          # e.g. metasploit-framework, sqlmap, gobuster
# or a big metapackage:
apt-get install -y kali-linux-headless
```

---

## ⚠️ Read this

- **Public repo = public link.** While the job runs, the tmate link sits in **publicly viewable logs**, so anyone who sees it can connect to the shell. If that matters to you:
  - Set `limit-access-to-actor: true` in `.github/workflows/kali-tmate.yml` (restricts SSH to *your* GitHub-registered SSH keys), **or**
  - Make the repo **private**.
- **GitHub Actions Terms.** Actions is intended for building/testing/deploying the repo's own software. Using it as a general remote-access host is a gray area under GitHub's Acceptable Use Policies. Keep this to legitimate, authorized use (learning, CTFs, security research on systems you're allowed to test). Don't use it to attack third parties or for anything you're not authorized to do.
- **It's temporary.** Nothing persists between runs except what you commit to the repo.

## What's in here

```
.github/workflows/kali-tmate.yml   # the whole thing
README.md
```
