/* ============================================================
   PRODUCTS CATALOG — loader.
   The full range (categories, products, nutrition, ingredients,
   selling points, Q&A, Amazon links) now lives in:
       data/catalog.js  ->  window.EB_CATALOG
   which the CMS reads and writes. Edit content there or, better,
   through the CMS — not in this file.
   ============================================================ */

const CATALOG = Array.isArray(window.EB_CATALOG) ? window.EB_CATALOG : [];

/* Flat list — useful for search, count, and cross-links. */
const CATALOG_FLAT = CATALOG.flatMap(c =>
  (c.products || []).map(p => ({
    ...p,
    category: c.name,
    categoryNumber: c.number,
    categoryId: c.id,
  }))
);

window.CATALOG = CATALOG;
window.CATALOG_FLAT = CATALOG_FLAT;
