/* ============================================================
   PRODUCTS — data model (no pricing).
   Content is CMS-managed and loaded from data/products.js
   (window.EB_PRODUCTS). This file only wires it up + owns <Pill>.
   ============================================================ */

const PRODUCTS = (typeof window !== "undefined" && Array.isArray(window.EB_PRODUCTS)) ? window.EB_PRODUCTS : [];

function Pill({ label }) {
  const isColorful = label === "BEST SELLER" || label === "NEW FORMULA" || label === "GLUTEN FREE" || label === "SOURCE OF PROTEIN" || label.startsWith("GREAT TASTE");
  return (
    <span style={{
      fontFamily: "var(--f-body)", fontSize: 9.5, letterSpacing: "0.22em",
      padding: "5px 9px",
      border: "1px solid var(--ink)",
      background: isColorful ? "var(--daylight)" : "var(--paper-bright)",
      color: "var(--ink)", textTransform: "uppercase",
    }}>{label}</span>
  );
}

window.PRODUCTS = PRODUCTS;
window.Pill = Pill;
