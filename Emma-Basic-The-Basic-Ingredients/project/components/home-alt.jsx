/* ============================================================
   Shared building blocks for the alternative homepage designs
   (Hub / Bento / Tabs). Reads the same CMS data the live site
   uses (window.EB_PRODUCTS, EB_HOME, EB_JOURNAL), so editing
   content in the CMS updates every design automatically.
   ============================================================ */

const EB_PRODUCTS_ALT = Array.isArray(window.EB_PRODUCTS) ? window.EB_PRODUCTS : [];
const EB_HOME_ALT = window.EB_HOME || {};
const EB_JOURNAL_ALT = window.EB_JOURNAL || { posts: [] };

/* A product card — pedestal image + editorial meta. */
function AltProductCard({ product, aspect = "3 / 4" }) {
  const [hover, setHover] = React.useState(false);
  const zoom = product.imageZoom || 1;
  return (
    <a
      href={`product.html?id=${product.id}`}
      onMouseEnter={() => setHover(true)}
      onMouseLeave={() => setHover(false)}
      style={{ display: "grid", gap: 14, textDecoration: "none", color: "inherit" }}
    >
      <div style={{
        position: "relative", aspectRatio: aspect, background: "var(--paper-shade)",
        border: "1px solid var(--rule)", overflow: "hidden",
        display: "flex", alignItems: "center", justifyContent: "center",
        boxShadow: "0 4px 28px rgba(10,10,10,0.05)",
      }}>
        <div style={{ position: "absolute", inset: "6%", background: "#fff", borderRadius: 4, boxShadow: "0 2px 12px rgba(10,10,10,0.06)" }} />
        <img
          src={product.image} alt={product.name} loading="lazy"
          style={{
            position: "absolute", inset: 0, width: "100%", height: "100%",
            objectFit: "contain", padding: "8%",
            objectPosition: product.imagePosition || "center center",
            transform: `scale(${hover ? zoom * 1.05 : zoom})`,
            transition: "transform 700ms var(--ease-out)", zIndex: 1,
          }}
        />
        {product.pill && (
          <span style={{
            position: "absolute", top: 12, left: 12, zIndex: 2,
            fontFamily: "var(--f-body)", fontSize: 9.5, letterSpacing: "0.18em",
            textTransform: "uppercase", padding: "5px 9px",
            border: "1px solid var(--ink)", background: "var(--paper-bright)",
          }}>{product.pill}</span>
        )}
      </div>
      <div style={{ display: "grid", gap: 6 }}>
        <span style={{ fontFamily: "var(--f-body)", fontSize: 10, letterSpacing: "0.2em", textTransform: "uppercase", color: "var(--ink-60)" }}>{product.origin}</span>
        <h3 style={{
          fontFamily: "var(--f-display)", fontWeight: 400, fontSize: "clamp(16px, 1.5vw, 21px)",
          letterSpacing: "-0.015em", lineHeight: 1.1, margin: 0,
          fontVariationSettings: '"opsz" 144, "SOFT" 30',
        }}>{product.name}</h3>
      </div>
    </a>
  );
}

/* A blog / journal card. */
function AltJournalCard({ post, big = false }) {
  const [hover, setHover] = React.useState(false);
  return (
    <a
      href={`journal-post.html?id=${post.id}`}
      onMouseEnter={() => setHover(true)}
      onMouseLeave={() => setHover(false)}
      style={{ display: "grid", gap: 14, textDecoration: "none", color: "inherit" }}
    >
      <div style={{ aspectRatio: big ? "16 / 10" : "4 / 3", overflow: "hidden", border: "1px solid var(--rule)" }}>
        <img src={post.image} alt="" loading="lazy" style={{
          width: "100%", height: "100%", objectFit: "cover",
          transform: hover ? "scale(1.04)" : "scale(1)", transition: "transform 800ms var(--ease-out)",
        }} />
      </div>
      <div style={{ display: "grid", gap: 8 }}>
        <span style={{ fontFamily: "var(--f-body)", fontSize: 10, letterSpacing: "0.2em", textTransform: "uppercase", color: "var(--ink-60)" }}>{post.category} &middot; {post.date}</span>
        <h3 style={{
          fontFamily: "var(--f-display)", fontWeight: 400,
          fontSize: big ? "clamp(24px, 3vw, 38px)" : "clamp(17px, 1.5vw, 22px)",
          letterSpacing: "-0.015em", lineHeight: 1.12, margin: 0,
          fontVariationSettings: '"opsz" 144, "SOFT" 40',
        }}>{post.title}</h3>
      </div>
    </a>
  );
}

/* A small reusable button. */
function AltButton({ href, label, primary = false }) {
  return (
    <a href={href} style={{
      display: "inline-flex", alignItems: "center", gap: 10,
      fontFamily: "var(--f-body)", fontSize: 11.5, letterSpacing: "0.18em", textTransform: "uppercase",
      textDecoration: "none", padding: "14px 22px",
      border: "1px solid var(--ink)",
      background: primary ? "var(--ink)" : "transparent",
      color: primary ? "var(--paper-bright, #fff)" : "var(--ink)",
      transition: "background 200ms var(--ease-out), color 200ms var(--ease-out)",
    }}>
      {label} <span style={{ fontFamily: "var(--f-mono)" }}>&rarr;</span>
    </a>
  );
}

/* Fixed bar to jump between the design options (comparison tool). */
function DesignSwitch() {
  const cur = window.EB_DESIGN || "";
  const items = [
    { id: "current", label: "Current", href: "Emma Basic Homepage.html" },
    { id: "hub", label: "1 · Hub", href: "home-hub.html" },
    { id: "bento", label: "2 · Bento", href: "home-bento.html" },
    { id: "tabs", label: "3 · Tabs", href: "home-tabs.html" },
  ];
  return (
    <div style={{
      position: "fixed", bottom: 18, left: "50%", transform: "translateX(-50%)",
      zIndex: 60, display: "flex", gap: 4, alignItems: "center",
      background: "var(--paper-bright, #fff)", border: "1px solid var(--rule)",
      borderRadius: 999, padding: "6px 8px",
      boxShadow: "0 8px 34px rgba(10,10,10,0.16)",
    }}>
      <span style={{ fontFamily: "var(--f-mono)", fontSize: 10, letterSpacing: "0.16em", textTransform: "uppercase", color: "var(--ink-60)", padding: "0 6px" }}>Design</span>
      {items.map(it => (
        <a key={it.id} href={it.href} style={{
          fontFamily: "var(--f-body)", fontSize: 11.5, letterSpacing: "0.1em", textTransform: "uppercase",
          textDecoration: "none", padding: "7px 12px", borderRadius: 999,
          color: cur === it.id ? "var(--paper-bright, #fff)" : "var(--ink)",
          background: cur === it.id ? "var(--ink)" : "transparent",
          whiteSpace: "nowrap",
        }}>{it.label}</a>
      ))}
    </div>
  );
}

window.AltProductCard = AltProductCard;
window.AltJournalCard = AltJournalCard;
window.AltButton = AltButton;
window.DesignSwitch = DesignSwitch;
