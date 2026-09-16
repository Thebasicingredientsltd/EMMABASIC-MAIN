/* Click-to-edit overlay for the CRM visual preview (same origin). */
(function () {
  if (!window.__CMS_VISUAL) return;

  function stores() {
    return [
      ["homepage", window.EB_HOME],
      ["people", window.EB_PEOPLE],
      ["journal", window.EB_JOURNAL],
      ["products", window.EB_PRODUCTS],
      ["catalog", window.EB_CATALOG],
      ["nav", window.EB_NAV]
    ].filter(function (pair) { return pair[1]; });
  }

  function walk(obj, prefix, out) {
    if (obj == null) return;
    if (typeof obj === "string") {
      if (obj.trim()) out.push({ path: prefix, value: obj });
      return;
    }
    if (Array.isArray(obj)) {
      obj.forEach(function (v, i) { walk(v, prefix + "[" + i + "]", out); });
      return;
    }
    if (typeof obj === "object") {
      Object.keys(obj).forEach(function (k) {
        walk(obj[k], prefix ? prefix + "." + k : k, out);
      });
    }
  }

  function plain(s) {
    var d = document.createElement("div");
    d.innerHTML = s;
    return (d.innerText || "").replace(/\s+/g, " ").trim();
  }

  function textOf(el) {
    return (el.innerText || "").replace(/\s+/g, " ").trim();
  }

  function isImage(val) {
    return /\.(png|jpe?g|gif|webp|avif|svg)(\?|$)/i.test(val);
  }

  function collect() {
    var out = [];
    stores().forEach(function (pair) {
      var fields = [];
      walk(pair[1], "", fields);
      fields.forEach(function (f) {
        f.key = pair[0];
        out.push(f);
      });
    });
    return out;
  }

  function markText(el, f) {
    if (el.getAttribute("data-cms-bound")) return;
    el.setAttribute("data-cms-bound", f.key + ":" + f.path);
    el.setAttribute("contenteditable", "true");
    el.style.outline = "1px dashed rgba(154,107,63,0.7)";
    el.style.outlineOffset = "3px";
    el.style.cursor = "text";
    el.addEventListener("click", function (e) { e.preventDefault(); e.stopPropagation(); });
    el.addEventListener("blur", function () {
      var hasHtml = /<(br|p|em|strong|i|b)\b/i.test(f.value) || /<br/i.test(el.innerHTML);
      save(f.key, f.path, hasHtml ? el.innerHTML : (el.innerText || "").trim());
    });
  }

  function markImage(img, f) {
    if (img.getAttribute("data-cms-bound")) return;
    img.setAttribute("data-cms-bound", f.key + ":" + f.path);
    img.style.outline = "2px dashed rgba(154,107,63,0.8)";
    img.style.outlineOffset = "2px";
    img.style.cursor = "pointer";
    img.title = "Click to replace this photo";
    img.addEventListener("click", function (e) {
      e.preventDefault();
      e.stopPropagation();
      var input = document.createElement("input");
      input.type = "file";
      input.accept = "image/*";
      input.onchange = function () {
        if (!input.files || !input.files[0]) return;
        var fd = new FormData();
        fd.append("file", input.files[0]);
        fd.append("key", f.key);
        fd.append("path", f.path);
        fetch("/api/visual/image", { method: "POST", body: fd })
          .then(function (r) { return r.json(); })
          .then(function (j) {
            if (j.ok && j.url) img.src = j.url + (j.url.indexOf("?") >= 0 ? "&" : "?") + "t=" + Date.now();
            window.parent.postMessage({ type: "__cms_visual_saved", ok: !!j.ok, error: j.error }, "*");
          });
      };
      input.click();
    }, true);
  }

  function save(key, path, value) {
    fetch("/api/visual/patch", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ key: key, path: path, value: value })
    }).then(function (r) { return r.json(); })
      .then(function (j) {
        window.parent.postMessage({ type: "__cms_visual_saved", ok: !!j.ok, error: j.error }, "*");
      });
  }

  function bind() {
    var fields = collect();
    var byText = {};
    fields.forEach(function (f) {
      if (isImage(f.value)) return;
      var t = plain(f.value);
      if (t.length < 8) return;
      byText[t] = (byText[t] || []).concat([f]);
    });
    var selectors = "h1,h2,h3,h4,p,span,em,a,li,blockquote,figcaption,button,label,td,th";
    Object.keys(byText).forEach(function (t) {
      if (byText[t].length !== 1) return;
      var f = byText[t][0];
      document.querySelectorAll(selectors).forEach(function (el) {
        if (el.closest("[data-cms-bound]")) return;
        if (el.querySelector(selectors)) return;
        if (plain(el.innerHTML) === t || textOf(el) === t) markText(el, f);
      });
    });
    fields.forEach(function (f) {
      if (!isImage(f.value)) return;
      var name = f.value.split("/").pop();
      if (!name) return;
      document.querySelectorAll("img").forEach(function (img) {
        var src = img.getAttribute("src") || "";
        try { src = decodeURIComponent(src); } catch (e) {}
        if (src.indexOf(name) !== -1) markImage(img, f);
      });
    });
  }

  var attempts = 0;
  function tick() {
    bind();
    attempts += 1;
    if (attempts < 25) setTimeout(tick, 350);
  }
  if (document.readyState === "complete") tick();
  else window.addEventListener("load", tick);
})();
