# Emma Basic — Content Management System (CMS)

A small local admin panel for editing the Emma Basic website without touching code.
You can edit **products**, **blog posts**, and **homepage content**, upload **images**,
and **publish** your changes straight to GitHub.

## How it works

The website reads its content from three data files:

```
Emma-Basic-The-Basic-Ingredients/project/data/products.js   ← products
Emma-Basic-The-Basic-Ingredients/project/data/journal.js    ← blog posts
Emma-Basic-The-Basic-Ingredients/project/data/homepage.js   ← homepage
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

## Notes

- Editing here changes the data files only; the site keeps working even if the CMS
  isn't running.
- Use `<br/>` inside text fields to force a line break where the design allows it.
