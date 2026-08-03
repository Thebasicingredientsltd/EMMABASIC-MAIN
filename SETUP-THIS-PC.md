# Set up a PC to edit the Emma Basic website

Use this when a **new computer** should edit products, blog posts, and homepage
content the same way the office PC already can.

## One-time setup (about 5 minutes)

1. **Install Python 3** from [python.org/downloads](https://www.python.org/downloads/)  
   Tick **Add python.exe to PATH** during install.

2. **Install Git** from [git-scm.com/download/win](https://git-scm.com/download/win)

3. **Clone the repo** (PowerShell or Command Prompt):

   ```bat
   git clone https://github.com/Thebasicingredientsltd/EMMABASIC-MAIN.git
   cd EMMABASIC-MAIN
   ```

   Put the folder somewhere lasting, e.g. `C:\Website\EMMABASIC-MAIN`.

4. **Double-click `setup-this-pc.bat`**  
   It installs CMS packages and checks GitHub access.

5. **Sign in to GitHub** (needed for the Publish button):

   - Install [GitHub CLI](https://cli.github.com/), then in this folder run:
     ```bat
     gh auth login
     ```
     Choose GitHub.com → HTTPS → Login with a web browser.
   - Your GitHub user must be allowed to push to
     `Thebasicingredientsltd/EMMABASIC-MAIN`. Ask a repo admin if Publish fails.

## Everyday use

Double-click **`start-servers.bat`**. That starts:

| App     | Address                                      |
| ------- | -------------------------------------------- |
| Website | http://localhost:8080                        |
| CMS     | http://localhost:5000                        |

Edit in the CMS → refresh the site to preview → **Publish to GitHub** when ready.

## Already have the folder on another drive?

Copy or move the whole `EMMABASIC-MAIN` folder, then run `setup-this-pc.bat`
once on the new PC. Launchers no longer depend on `C:\Website\...` paths.

## Edit from any browser (optional)

If the online CMS is deployed on Vercel (see `cms/DEPLOY.md`), you can edit
from any PC without installing anything — just open that URL and sign in.
Local setup above is for offline / on-disk editing with a Publish button.
