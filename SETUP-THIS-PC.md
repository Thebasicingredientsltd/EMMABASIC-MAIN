# Set up a PC to edit the Emma Basic website

## This PC’s repo folder

```
C:\Cloud\OneDrive - The Basic Ingredients Ltd\Documents\GitHub\EMMABASIC-MAIN
```

Open that folder in File Explorer for all steps below.

## One-time setup

1. **Install Python 3** from [python.org/downloads](https://www.python.org/downloads/)  
   Tick **Add python.exe to PATH** during install.

2. **Install Git** from [git-scm.com/download/win](https://git-scm.com/download/win)  
   (Skip if GitHub Desktop / Git is already installed.)

3. In the folder above, double-click **`setup-this-pc.bat`**.  
   It installs CMS packages and checks GitHub access.

4. **Sign in to GitHub** (needed for the Publish button):

   - Install [GitHub CLI](https://cli.github.com/) if needed, then open Command Prompt **in that folder** and run:
     ```bat
     gh auth login
     ```
     Choose GitHub.com → HTTPS → Login with a web browser.
   - Your GitHub user must be allowed to push to
     `Thebasicingredientsltd/EMMABASIC-MAIN`. Ask a repo admin if Publish fails.

## Everyday use

In the same folder, double-click **`start-servers.bat`**. That starts:

| App     | Address               |
| ------- | --------------------- |
| Website | http://localhost:8080 |
| CMS     | http://localhost:5000 |

Edit in the CMS → refresh the site to preview → **Publish to GitHub** when ready.

Tip: right-click `start-servers.bat` → **Send to → Desktop (create shortcut)**.

## Notes

- Launchers use paths relative to this folder, including OneDrive paths with spaces.
- Keep the repo fully synced in OneDrive before editing (Files On-Demand: make sure
  the folder is available offline if you work without a network).
- Optional: edit from any browser if the online CMS is deployed (see `cms/DEPLOY.md`).
