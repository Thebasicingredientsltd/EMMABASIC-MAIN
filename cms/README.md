# Emma Basic — Content Management System (CMS)

A small local admin panel for editing the Emma Basic website without touching code.
You can edit **products**, **blog posts**, and **homepage content**, upload **images**,
and **publish** your changes straight to GitHub.

## How it works

The website reads its content from data files, one per area:

```
Emma-Basic-The-Basic-Ingredients/project/data/products.js   ← products
Emma-Basic-The-Basic-Ingredients/project/data/journal.js    ← blog posts
Emma-Basic-The-Basic-Ingredients/project/data/homepage.js   ← homepage
Emma-Basic-The-Basic-Ingredients/project/data/site.js       ← under construction switch
```

The CMS edits those files for you through friendly forms. Uploaded images are saved
into `Emma-Basic-The-Basic-Ingredients/project/assets/uploads/`.

## Running it

**Easiest:** double-click **`start-cms.bat`**. It installs the requirement (Flask),
opens your browser, and starts the CMS.

**Manually:**

```bash
cd cms
python -m pip install -r requirements.txt
python app.py
```

Then open <http://localhost:5000>.

To preview the site while editing, also run the website server (in the `project` folder):

```bash
cd Emma-Basic-The-Basic-Ingredients/project
python -m http.server 8080
```

The site is at <http://localhost:8080/Emma%20Basic%20Homepage.html>. After saving in the
CMS, refresh the site to see changes.

## Publishing

On the **Dashboard**, the *Publish to GitHub* button commits every pending change and
pushes it to `Thebasicingredientsltd/EMMABASIC-MAIN`. Publishing requires GitHub CLI
(`gh`) to already be signed in (it is, on this machine).

## What you can edit

- **Products** — image, name, origin, lot, badge, tagline, Amazon link, selling points,
  ingredients, and the "never in the jar" list.
- **Blog** — cover image, category, date, title, excerpt, featured flag, plus the full
  article (hero image, intro, and body with headings/dividers).
- **Homepage** — hero, additive-free banner, founder narrative, the "Flip the pack"
  comparison, and the lifestyle image grid.

## Taking the website down for a while

**Under construction** (sidebar, under *Tools*) hides the whole website behind a
holding page. Turn it on before a round of content changes and nobody sees a
half-finished page; turn it off when you're happy.

- Every page redirects to `under-construction.html` *before* it draws anything,
  so there is no flash of the work in progress.
- The headline, message, note and contact address on that page are all editable
  on the same screen.
- **Your preview link** on that screen keeps the real website visible to you.
  Open it once and you can click through every page as normal while everyone
  else gets the holding page. Add `?preview=off` to any address to stop. Anyone
  who has the link can see the site, so keep it to yourself — press *Make a new
  link* if it gets passed around.
- While it's on, every CRM page carries a banner with a **Put the site back up**
  button, so it can't be left on by accident.
- The CMS's own visual editor ignores the holding page, so you can keep editing.

## Notes

- Editing here changes the data files only; the site keeps working even if the CMS
  isn't running.
- Use `<br/>` inside text fields to force a line break where the design allows it.
