/* ============================================================
   SlideOutPanel — drawer UX. No price, no basket CTA.
   ============================================================ */
function SlideOutPanel({ product, open, onClose }) {
  const [mounted, setMounted] = React.useState(false);
  React.useEffect(() => {
    if (open) { setMounted(true); document.body.style.overflow = "hidden"; }
    else { document.body.style.overflow = ""; const t = setTimeout(() => setMounted(false), 450); return () => clearTimeout(t); }
  }, [open]);
  React.useEffect(() => {
    const onKey = (e) => { if (e.key === "Escape") onClose(); };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);
  if (!mounted && !open) return null;
  const p = product;
  return (
    <>
      <div onClick={onClose} style={{
        position: "fixed", inset: 0, zIndex: 60,
        background: "rgba(10,10,10,0.5)",
        opacity: open ? 1 : 0,
        transition: "opacity var(--dur-drawer) var(--ease-out)",
        pointerEvents: open ? "auto" : "none",
      }}/>
      <aside style={{
        position: "fixed", top: 0, right: 0, bottom: 0, zIndex: 70,
        width: "min(620px, 92vw)",
        background: "var(--paper-bright)",
        transform: open ? "translateX(0)" : "translateX(100%)",
        transition: "transform var(--dur-drawer) var(--ease-out)",
        display: "flex", flexDirection: "column",
        overflow: "hidden",
      }}>
        <div style={{
          display: "flex", justifyContent: "space-between", alignItems: "center",
          padding: "20px 28px", borderBottom: "1px solid var(--rule)", flexShrink: 0,
        }}>
          <span style={{ fontFamily: "var(--f-body)", fontSize: 10.5, letterSpacing: "0.22em", textTransform: "uppercase", color: "var(--ink-60)" }}>
            Label Decoder
          </span>
          <button onClick={onClose} style={{
            background: "transparent", border: 0, cursor: "pointer",
            fontFamily: "var(--f-body)", fontSize: 11, letterSpacing: "0.22em",
            textTransform: "uppercase", color: "var(--ink)",
            display: "flex", alignItems: "center", gap: 10,
          }}>
            Close <span style={{ fontSize: 18 }}>×</span>
          </button>
        </div>
        <div style={{ flex: 1, overflowY: "auto" }}>
          {p && <DrawerContent p={p} />}
        </div>
        <div style={{
          padding: "16px 28px", borderTop: "1px solid var(--rule)",
          display: "flex", justifyContent: "space-between", flexShrink: 0,
          fontFamily: "var(--f-body)", fontSize: 10.5, letterSpacing: "0.22em",
          textTransform: "uppercase", color: "var(--ink-60)",
        }}>
          <span>{p && p.origin}</span>
        </div>
      </aside>
    </>
  );
}

function DrawerContent({ p }) {
  return (
    <div>
      {/* Product image */}
      <div style={{ position: "relative", aspectRatio: "4/3", overflow: "hidden", background: "var(--paper-bright)" }}>
        {p.image ? (
          <img src={p.image} alt={p.name} style={{
            width: "100%", height: "100%",
            objectFit: "cover",
            objectPosition: p.imagePosition || "center center",
            display: "block",
          }} />
        ) : (
          <Placeholder label={`${p.name.toUpperCase()}`} tone={p.tone} />
        )}
        {p.pill && <div style={{ position: "absolute", top: 20, left: 20 }}><Pill label={p.pill} /></div>}
      </div>

      {/* Name + tagline */}
      <div style={{ padding: "32px 28px 24px" }}>
        <h2 style={{
          fontFamily: '"Minerva Modern", var(--f-display)', fontWeight: 400,
          fontSize: 40, letterSpacing: "-0.02em", lineHeight: 1, margin: 0,
        }}>{p.name}</h2>
        <p style={{
          fontFamily: "var(--f-body)", fontWeight: 400,
          fontSize: 16, lineHeight: 1.5, margin: "12px 0 0",
          color: "var(--ink-90)", maxWidth: 500, letterSpacing: "0",
        }}>{p.tagline}</p>
      </div>

      {/* Why it's good */}
      {(p.usps || p.ours) && (
        <div style={{ padding: "0 28px 28px" }}>
          <div style={{ fontFamily: "var(--f-body)", fontSize: 10.5, letterSpacing: "0.22em", textTransform: "uppercase", color: "var(--ink-60)", marginBottom: 16 }}>
            Why it's good
          </div>
          <ul style={{ listStyle: "none", padding: 0, margin: 0, display: "grid", gap: 12 }}>
            {(p.usps || p.ours).map((x, i) => (
              <li key={i} style={{
                fontFamily: "var(--f-body)", fontSize: 14, lineHeight: 1.5,
                display: "grid", gridTemplateColumns: "auto 1fr", gap: 12,
                borderTop: i === 0 ? "1px solid var(--rule)" : "none",
                paddingTop: i === 0 ? 12 : 0,
              }}>
                <span style={{ fontFamily: "var(--f-mono)", fontSize: 9.5, color: "var(--ink-60)", paddingTop: 2 }}>
                  {String(i + 1).padStart(2, "0")}
                </span>
                <span>{x}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Ingredients */}
      <div style={{ padding: "0 28px 28px" }}>
        <div style={{ fontFamily: "var(--f-body)", fontSize: 10.5, letterSpacing: "0.22em", textTransform: "uppercase", color: "var(--ink-60)", marginBottom: 14 }}>
          Ingredients
        </div>
        <p style={{
          fontFamily: "var(--f-body)", fontSize: 15, lineHeight: 1.6, margin: 0,
          color: "var(--ink-90)",
        }}>{p.ingredients.join(" ")}</p>
      </div>

      {/* Never in the pack */}
      <div style={{ padding: "0 28px 28px" }}>
        <div style={{ fontFamily: "var(--f-body)", fontSize: 10.5, letterSpacing: "0.22em", textTransform: "uppercase", color: "var(--ink-60)", marginBottom: 14 }}>
          Never in the pack
        </div>
        <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
          {p.notTested.map(n => (
            <span key={n} style={{
              padding: "6px 11px", border: "1px solid var(--rule-strong)",
              fontFamily: "var(--f-body)", fontSize: 10.5, letterSpacing: "0.22em",
              textTransform: "uppercase", color: "var(--ink-90)",
              textDecoration: "line-through", textDecorationThickness: "1px",
            }}>{n}</span>
          ))}
        </div>
      </div>

      {/* Show me more button */}
      <div style={{ padding: "0 28px 40px" }}>
          <a href={`product.html?id=${p.id}`} style={{
            display: "inline-flex", alignItems: "center", gap: 10,
            padding: "14px 24px",
            background: "var(--ink)", color: "var(--paper)",
            fontFamily: "var(--f-body)", fontSize: 12.5, letterSpacing: "0.14em",
            textTransform: "uppercase", textDecoration: "none",
            border: "1px solid var(--ink)",
            transition: "background 180ms var(--ease-out), color 180ms var(--ease-out)",
          }}
            onMouseEnter={e => { e.currentTarget.style.background = "transparent"; e.currentTarget.style.color = "var(--ink)"; }}
            onMouseLeave={e => { e.currentTarget.style.background = "var(--ink)"; e.currentTarget.style.color = "var(--paper)"; }}
          >
            <span>Show me more</span>
            <span style={{ fontFamily: "var(--f-mono)", fontSize: 11 }}>→</span>
          </a>
        </div>
    </div>
  );
}

window.SlideOutPanel = SlideOutPanel;
