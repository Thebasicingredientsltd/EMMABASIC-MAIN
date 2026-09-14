/* ============================================================
   OrderSection — "How to order" accordion for trade customers.
   Content is CMS-managed via data/people.js (window.EB_PEOPLE.trade),
   so editing the trade copy in the CMS keeps working after the move.
   ============================================================ */
function OrderSection() {
  const [open, setOpen] = React.useState(null);
  const d = (typeof window !== "undefined" && window.EB_PEOPLE && window.EB_PEOPLE.trade) || {};
  const eyebrow = d.eyebrow || "For trade customers";
  const heading = d.heading || "How to order.";
  const intro = d.intro || "All orders are subject to account approval. Get in touch to open a trade account and start ordering.";
  const items = (d.items && d.items.length) ? d.items : [
    { q: "Open a trade account", a: "Two payment terms depending on your CreditSafe rating: Cash in Advance or Net 30 Days Credit.", forms: [
      { label: "Cash in Advance - Application Form", href: "assets/forms/The Basic - Cash Advance Account updated.pdf" },
      { label: "Net 30 Days Credit - Application Form", href: "assets/forms/The Basic - Account Application Form updated.pdf" },
    ]},
    { q: "Order schedule", a: "Place your order by 10:00 AM on Day 1 for Day 3 delivery. Email boris@thebasicingredients.com with the product code, product name, and quantity required." },
    { q: "Minimum order", a: "Minimum order value is assessed case by case, based on your delivery distance and estimated volume. Get in touch with your address and an idea of what you need and we will come back to you with a figure." },
    { q: "Collection - Ambient", a: "Kinaxia Logistics, DC115, Danes Way, Dirft, Crick, NN6 7GZ. Monday to Friday, 07:00-20:00." },
    { q: "Collection - Frozen", a: "JS Davidson Ltd, Shrewsbury Avenue, Woodston Industrial Estate, Peterborough, PE2 7LB. Monday to Friday, 06:00-15:00." },
    { q: "Use your existing distributor", a: "If you prefer to use your favourite distributor then please put us in touch, we will gladly make contact." },
  ];
  return (
    <section id="trade" style={{ background: "var(--paper-shade)", borderTop: "1px solid var(--rule)", padding: "clamp(80px, 12vw, 160px) var(--pad-x)" }}>
      <div style={{ maxWidth: "var(--maxw)", margin: "0 auto" }}>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "clamp(32px, 6vw, 96px)", marginBottom: "clamp(48px, 7vh, 80px)", alignItems: "end" }} className="tbi-order-header">
          <Reveal>
            <div>
              <span style={{ fontFamily: "var(--f-mono)", fontSize: 10.5, letterSpacing: "0.24em", textTransform: "uppercase", color: "var(--ink-60)", display: "block", marginBottom: 20 }}>{eyebrow}</span>
              <h2 style={{ fontFamily: "var(--f-display)", fontWeight: 400, fontSize: "clamp(36px, 4.5vw, 72px)", lineHeight: 1.0, letterSpacing: "-0.035em", margin: 0, fontVariationSettings: '"opsz" 144, "SOFT" 20' }}>{heading}</h2>
            </div>
          </Reveal>
          <Reveal delay={100}>
            <p style={{ fontFamily: "var(--f-body)", fontSize: "clamp(16px, 1.3vw, 18px)", lineHeight: 1.72, margin: 0, color: "var(--ink-60)" }}>
              {intro}
            </p>
          </Reveal>
        </div>
        <div style={{ borderTop: "1px solid var(--rule)" }}>
          {items.map((item, i) => (
            <Reveal key={i} delay={i * 50}>
              <div style={{ borderBottom: "1px solid var(--rule)" }}>
                <button onClick={() => setOpen(open === i ? null : i)} style={{ width: "100%", display: "flex", justifyContent: "space-between", alignItems: "center", gap: 24, padding: "22px 0", background: "none", border: "none", cursor: "pointer", textAlign: "left" }}>
                  <span style={{ fontFamily: "var(--f-body)", fontWeight: 400, fontSize: "clamp(17px, 1.3vw, 19px)", color: "var(--ink)", lineHeight: 1.4 }}>{item.q}</span>
                  <span style={{ fontFamily: "var(--f-mono)", fontSize: 16, color: "var(--ink-60)", flexShrink: 0, transform: open === i ? "rotate(45deg)" : "rotate(0deg)", transition: "transform 300ms var(--ease-out)", display: "inline-block" }}>+</span>
                </button>
                <div style={{ overflow: "hidden", maxHeight: open === i ? 600 : 0, transition: "max-height 400ms var(--ease-out)" }}>
                  <p style={{ fontFamily: "var(--f-body)", fontWeight: 400, fontSize: "clamp(17px, 1.3vw, 19px)", lineHeight: 1.65, color: "var(--ink-90)", margin: "0 0 28px" }}>{item.a}</p>
                  {item.forms && (
                    <div style={{ display: "flex", flexDirection: "column", gap: 12, marginBottom: 28 }}>
                      {item.forms.map(f => (
                        <a key={f.label} href={f.href} download style={{ display: "inline-flex", alignItems: "center", gap: 10, fontFamily: "var(--f-mono)", fontSize: 10.5, letterSpacing: "0.18em", textTransform: "uppercase", textDecoration: "none", color: "var(--ink)", border: "1px solid var(--rule)", padding: "12px 20px", width: "fit-content", transition: "background 180ms var(--ease-out)" }}
                          onMouseEnter={e => e.currentTarget.style.background = "var(--paper-shade)"}
                          onMouseLeave={e => e.currentTarget.style.background = "transparent"}>
                          {f.label}
                        </a>
                      ))}
                      <p style={{ fontFamily: "var(--f-body)", fontSize: "clamp(13px, 1vw, 14px)", lineHeight: 1.6, margin: "4px 0 0", color: "var(--ink-60)" }}>
                        Please contact <a href="mailto:boris@thebasicingredients.com" style={{ color: "var(--ink)", textDecoration: "underline" }}>boris@thebasicingredients.com</a> to open your account.
                      </p>
                    </div>
                  )}
                </div>
              </div>
            </Reveal>
          ))}
        </div>
      </div>
      <style>{`@media (max-width: 768px) { .tbi-order-header { grid-template-columns: 1fr !important; } }`}</style>
    </section>
  );
}
window.OrderSection = OrderSection;
