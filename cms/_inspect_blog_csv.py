# Temporary inspector — not part of the import.
import csv
import json
import pathlib
import collections
import sys

sys.stdout.reconfigure(encoding="utf-8")

p = pathlib.Path(r"C:\Users\TBIL_Manager\Downloads\Blog.csv")
with p.open(encoding="utf-8-sig", newline="") as f:
    rows = list(csv.DictReader(f))

print("nrows", len(rows))
types = collections.Counter()
for i, r in enumerate(rows):
    title = r.get("Title") or ""
    pub = r.get("Published on") or ""
    slug = r.get("Blog (Title)") or ""
    author = r.get("Author") or ""
    long = r.get("Long Description") or ""
    ntypes = []
    texts = []
    try:
        doc = json.loads(long)

        def walk(n, depth=0):
            if not isinstance(n, dict):
                return
            t = n.get("type")
            if t:
                types[t] += 1
                ntypes.append(t)
            td = n.get("textData") or {}
            if td.get("text"):
                texts.append(td["text"][:80])
            hd = n.get("headingData")
            if hd:
                ntypes.append("HEADING_L" + str(hd.get("level")))
            for c in n.get("nodes") or []:
                walk(c, depth + 1)

        walk(doc)
    except Exception as e:
        print("json fail", i, e)
    print(
        f"{i:02d} pub={bool(pub)!s:5} author={author!r:22} slug={slug} title={title!r}"
    )
    print("    types", sorted(set(ntypes)))
    print("    first_text", texts[:3])

print("ALL TYPES", dict(types))
