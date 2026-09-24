/* Emma Basic — apply CMS SEO to the document head.
   Static pages already have tags written on save; this keeps product and
   journal-post pages (which share one HTML file) in sync with ?id=. */
(function () {
  var ORIGIN = "https://emmabasic.co.uk";
  var script = document.currentScript;
  var page = (script && script.getAttribute("data-eb-seo")) || "";

  function queryId() {
    try {
      return new URLSearchParams(window.location.search).get("id") || "";
    } catch (err) {
      return "";
    }
  }

  function text(value) {
    return String(value == null ? "" : value)
      .replace(/<br\s*\/?>/gi, " ")
      .replace(/<[^>]+>/g, "")
      .replace(/\s+/g, " ")
      .trim();
  }

  function absUrl(path) {
    var raw = text(path);
    if (!raw) return "";
    if (/^https?:\/\//i.test(raw)) return raw;
    if (raw.indexOf("//") === 0) return "https:" + raw;
    if (raw.charAt(0) === "/") return ORIGIN + raw;
    return ORIGIN + "/" + raw.replace(/^\.\//, "");
  }

  function stored(obj) {
    return (obj && obj.seo) || {};
  }

  function pick(itemSeo, pageSeo, fallback) {
    return text(itemSeo) || text(pageSeo) || text(fallback) || "";
  }

  function findProduct(id) {
    var catalog = window.EB_CATALOG;
    var cats = Array.isArray(catalog) ? catalog : (catalog && catalog.categories) || [];
    for (var i = 0; i < cats.length; i++) {
      var products = (cats[i] && cats[i].products) || [];
      for (var j = 0; j < products.length; j++) {
        if (products[j] && products[j].id === id) return products[j];
      }
    }
    return null;
  }

  function findPost(id) {
    var journal = window.EB_JOURNAL || {};
    var posts = journal.posts || [];
    for (var i = 0; i < posts.length; i++) {
      if (posts[i] && posts[i].id === id) return posts[i];
    }
    return null;
  }

  function pageBundle() {
    switch (page) {
      case "homepage":
        return window.EB_HOME || {};
      case "catalog":
      case "product":
        return (!Array.isArray(window.EB_CATALOG) && window.EB_CATALOG) || {};
      case "journal":
      case "journal_post":
        return window.EB_JOURNAL || {};
      case "people":
      case "distributor":
        return window.EB_PEOPLE || {};
      case "places":
        return window.EB_PLACES || {};
      case "story":
        return window.EB_STORY || {};
      case "company":
        return window.EB_COMPANY || {};
      case "matcha":
        return window.EB_MATCHA || {};
      default:
        return {};
    }
  }

  function resolve() {
    var data = pageBundle();
    var pageSeo = stored(page === "distributor" ? data.distributor : data);
    var item = null;
    var itemSeo = {};
    var fallbackTitle = document.title || "Emma Basic";
    var fallbackDesc = "";
    var fallbackImage = "";
    var canonical = "";
    var ogType = page === "journal_post" ? "article" : "website";
    var id = queryId();

    if (page === "product") {
      item = findProduct(id);
      itemSeo = stored(item);
      if (item) {
        fallbackTitle = item.name ? item.name + " — Emma Basic" : fallbackTitle;
        fallbackDesc = item.tagline || fallbackDesc;
        fallbackImage = item.image || fallbackImage;
        canonical = ORIGIN + "/product.html?id=" + encodeURIComponent(id);
      }
    } else if (page === "journal_post") {
      item = findPost(id);
      itemSeo = stored(item);
      if (item) {
        fallbackTitle = item.title ? item.title + " — Emma Basic" : fallbackTitle;
        fallbackDesc = item.excerpt || fallbackDesc;
        fallbackImage = item.image || fallbackImage;
        canonical = ORIGIN + "/journal-post.html?id=" + encodeURIComponent(id);
      }
    } else if (page === "distributor") {
      fallbackTitle = (data.distributor && data.distributor.title) || fallbackTitle;
    }

    if (!canonical) {
      if (page === "homepage") canonical = ORIGIN + "/";
      else canonical = ORIGIN + window.location.pathname.replace(/^\//, "/");
    }

    return {
      title: pick(itemSeo.title, pageSeo.title, fallbackTitle) || "Emma Basic",
      description: pick(itemSeo.description, pageSeo.description, fallbackDesc),
      canonical: pick(itemSeo.canonical, pageSeo.canonical, canonical),
      image: pick(itemSeo.image, pageSeo.image, fallbackImage),
      ogType: text(itemSeo.ogType) || (page === "journal_post" ? ogType : text(pageSeo.ogType)) || ogType,
      noindex: !!(itemSeo.noindex || pageSeo.noindex)
    };
  }

  function setAttr(selector, attr, value) {
    var el = document.head.querySelector(selector);
    if (!value) {
      if (el && el.getAttribute("data-cms-seo") === "1") el.parentNode.removeChild(el);
      return;
    }
    if (!el) {
      var name = selector.match(/^([a-z]+)/i);
      el = document.createElement(name ? name[1] : "meta");
      var prop = selector.match(/\[([a-z:]+)="([^"]+)"\]/i);
      if (prop) el.setAttribute(prop[1], prop[2]);
      el.setAttribute("data-cms-seo", "1");
      document.head.appendChild(el);
    }
    el.setAttribute(attr, value);
  }

  function apply(seo) {
    document.title = seo.title;
    var titleEl = document.head.querySelector("title");
    if (titleEl) titleEl.textContent = seo.title;
    setAttr('meta[name="description"]', "content", seo.description);
    setAttr('link[rel="canonical"]', "href", seo.canonical);
    setAttr('meta[property="og:title"]', "content", seo.title);
    setAttr('meta[property="og:description"]', "content", seo.description);
    setAttr('meta[property="og:url"]', "content", seo.canonical);
    setAttr('meta[property="og:type"]', "content", seo.ogType);
    setAttr('meta[property="og:site_name"]', "content", "Emma Basic");
    var image = absUrl(seo.image);
    setAttr('meta[property="og:image"]', "content", image);
    setAttr('meta[name="twitter:title"]', "content", seo.title);
    setAttr('meta[name="twitter:description"]', "content", seo.description);
    setAttr('meta[name="twitter:image"]', "content", image);
    setAttr('meta[name="twitter:card"]', "content", image ? "summary_large_image" : "summary");
    setAttr('meta[name="robots"]', "content", seo.noindex ? "noindex, nofollow" : "");
  }

  apply(resolve());
})();
