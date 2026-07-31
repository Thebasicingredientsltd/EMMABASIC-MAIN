# Running the Emma Basic CMS online (Vercel)

The CMS can run in two modes, selected by the `CMS_BACKEND` environment variable:

| Mode              | Reads          | Writes                              | Publish            |
| ----------------- | -------------- | ----------------------------------- | ------------------ |
| `local` (default) | files on disk  | files on disk                       | Publish button (`git push`) |
| `github`          | GitHub API     | GitHub API (one commit per save)    | **automatic** on every save |

Online it must run in **`github`** mode, because a serverless filesystem is
read-only. In this mode each save commits the changed data/image files straight
to the repo via the GitHub Git Data API; the site's normal Vercel deploy then
picks the commit up and goes live. No local checkout or `git` binary is needed.

## What changed to make this possible

- `storage.py` — a small persistence layer with `local` and `github` backends.
- `app.py` — all file reads/writes and image uploads now go through `storage`,
  uploads are batched so a form save is a **single commit**, and a password
  login guards every page when online.
- `api/index.py` + `vercel.json` — the Vercel Python entry point.

## Deploy steps

1. **Create a GitHub token** with write access to this repository's *Contents*:
   - Fine-grained PAT → Repository access: this repo → Permissions → *Contents: Read and write*.
   - (A classic PAT with the `repo` scope also works.)

2. **Create a new Vercel project** pointing at the **`cms/`** directory of this
   repo (Root Directory = `cms`). Vercel will detect `vercel.json` and build
   `api/index.py` with the Python runtime.

3. **Set Environment Variables** in the Vercel project (see `.env.example`):
   - `CMS_BACKEND=github`
   - `CMS_PASSWORD=` a long random password (what you type to sign in)
   - `CMS_SECRET=` a long random hex string (signs the session cookie)
   - `GITHUB_TOKEN=` the token from step 1
   - `GITHUB_REPO=Thebasicingredientsltd/EMMABASIC-MAIN`
   - `GITHUB_BRANCH=main` (the branch the live site deploys from)

4. **Deploy.** Open the deployment URL, sign in with `CMS_PASSWORD`, and edit as
   usual. Saves commit + deploy automatically; the "Publish" button just
   confirms that auto-publish is on.

## Notes & caveats

- **Auto-publish:** in `github` mode there is no manual publish — every save is
  live after the resulting deploy finishes (typically under a minute).
- **Deploys per save:** a normal save is one commit → one deploy. Drag-and-drop
  image uploads (`/api/upload`) commit immediately so the preview works, so
  uploading several images then saving can produce a few deploys. Inline file
  fields submitted *with* a form are folded into that form's single commit.
- **Private repos:** image previews are proxied through the authenticated API,
  so they work even if the repo is private.
- **Security:** never commit real secrets. Set them only as Vercel env vars.
  The token can commit to your repo, so treat it like a password.

## Local development

Nothing changes: run `python app.py` with no env vars for the classic
on-disk + Publish-button workflow. Set `CMS_PASSWORD` locally if you want to
test the login flow, or `CMS_BACKEND=github` (plus the GitHub vars) to test the
online path against a branch.
