/* ============================================================
   Under-construction gate. Toggled from the CMS, which stores the
   switch on data/site.js.

   This runs as the first script in <head>, before the browser has
   reached <body>, so a visitor is sent to under-construction.html
   without ever painting a frame of the real page. That ordering is
   the whole point — loading it any later would show the content we
   are trying to hide.
   ============================================================ */
(function () {
  var TARGET = "under-construction.html";
  var STORE_KEY = "eb-preview";
  var PARAM = "preview";

  function param(name) {
    var match = new RegExp("[?&]" + name + "=([^&#]*)").exec(window.location.search);
    return match ? decodeURIComponent(match[1].replace(/\+/g, " ")) : null;
  }

  // Storage throws rather than returning null in some privacy modes, so every
  // access is guarded. A visitor who blocks it simply doesn't keep the pass.
  function readPass() {
    try {
      return window.localStorage.getItem(STORE_KEY) || "";
    } catch (err) {
      return "";
    }
  }

  function writePass(value) {
    try {
      if (value) window.localStorage.setItem(STORE_KEY, value);
      else window.localStorage.removeItem(STORE_KEY);
    } catch (err) {
      /* nothing to do — the pass just won't survive this page */
    }
  }

  function dropParam() {
    if (!window.history || !window.history.replaceState) return;
    var search = window.location.search
      .replace(new RegExp("([?&])" + PARAM + "=[^&#]*(&|$)"), "$1")
      .replace(/[?&]$/, "");
    window.history.replaceState(
      null, "", window.location.pathname + search + window.location.hash
    );
  }

  var settings = (window.EB_SITE || {}).maintenance || {};
  var requested = param(PARAM);

  // `?preview=<key>` is remembered so the owner can click through the whole
  // site on one pass; `?preview=off` hands it back.
  if (requested !== null) {
    writePass(requested === "off" ? "" : requested);
    dropParam();
  }

  // Only an explicit `true` hides the site. If site.js is missing, stale, or
  // malformed the website stays up.
  if (settings.enabled !== true) return;

  var key = String(settings.previewKey || "");
  var pass = requested !== null && requested !== "off" ? requested : readPass();
  if (key && pass === key) return;

  // The navigation is instant, but the browser keeps parsing until it commits.
  // Blanking to paper colour means the gap reads as a page still loading
  // rather than a flash of the content being worked on.
  var root = document.documentElement;
  root.style.background = "#F6F6F6";
  root.style.visibility = "hidden";
  window.location.replace(TARGET);
})();
