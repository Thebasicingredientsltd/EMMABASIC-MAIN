import urllib.request
import re

def get(url):
    return urllib.request.urlopen(url, timeout=60).read().decode("utf-8", "replace")

nav = get("http://127.0.0.1:5000/preview-static/data/nav.js")
print("nav.js has Ltd menu", "The Basic Ingredients Ltd" in nav)

cms = get("http://127.0.0.1:5000/company")
labels = re.findall(r'class="lbl">([^<]+)', cms)
print("CRM sidebar:", labels)

visual = get("http://127.0.0.1:5000/visual")
m = re.search(r'value="company"\s*>([^<]+)', visual)
print("visual picker:", m.group(1) if m else "missing")
