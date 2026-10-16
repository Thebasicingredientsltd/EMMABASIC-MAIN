/* ============================================================
   LifestyleGrid + SiteFooter. No chapter labels, no editorial meta.
   NewsletterCapture and EducationalBlock removed per request.
   ============================================================ */

function LifestyleGrid() {
  const L = (typeof window !== "undefined" && window.EB_HOME && window.EB_HOME.lifestyle) || {};
  const headingLine1 = L.headingLine1 || "The Grit /";
  const headingLine2 = L.headingLine2 || "The Purity.";
  const handle = L.handle || "@emmabasic";
  const followHref = L.followHref || "https://www.instagram.com/emmabasic.london/";
  const tiles = (Array.isArray(L.tiles) && L.tiles.length) ? L.tiles : [
    { image: "assets/homepage/sesame-tennis.png", label: "SESAME SEEDS — TENNIS",     tone: "warm", kind: "purity", span: "tall", position: "center center" },
    { image: "assets/homepage/lifestyle-3.png",   label: "KITCHEN — FAMILY DINNER",   tone: "warm", kind: "purity",              position: "center center" },
    { image: "assets/homepage/lifestyle-4.png",   label: "THE GRIT",                  tone: "cool", kind: "grit",               position: "center center" },
    { image: "assets/homepage/lifestyle-1.png",  label: "POST-RUN — HEATH, 06:14",    tone: "ink",  kind: "grit",   span: "tall", position: "center center" },
    { image: "assets/homepage/sesame-family.png", label: "SESAME OIL — FAMILY",       tone: "ink",  kind: "grit",   span: "wide", position: "center center" },
    { image: "assets/homepage/lifestyle-2.png",   label: "MATCHA POUR — STUDIO",      tone: "warm", kind: "purity",              position: "center center" },
    { image: "assets/homepage/lifestyle-5.png",   label: "LONG RUN NOTES",            tone: "ink",  kind: "grit",               position: "center center" },
    { image: "assets/homepage/sushi-vinegar.png", label: "SUSHI VINEGAR — NATURAL",   tone: "warm", kind: "purity", span: "tall", position: "center center" },
    { image: "assets/homepage/gallery-1.jpg",     label: "EMMA BASIC",                tone: "warm", kind: "purity",              position: "center center" },
    { image: "assets/homepage/gallery-2.jpg",     label: "EMMA BASIC",                tone: "warm", kind: "purity",              position: "center center" },
  ];
  return (
    <section style={{ padding: "clamp(28px, 4vh, 56px) var(--pad-x) clamp(40px, 6vh, 80px)" }}>
      <div style={{ maxWidth: "var(--maxw)", margin: "0 auto" }}>
        <Reveal>
          <div style={{
            display: "grid", gridTemplateColumns: "1fr auto",
            alignItems: "end", gap: 24, marginBottom: "clamp(48px, 6vh, 80px)",
          }}>
            <h2 className="eb-grit-heading" style={{
              fontFamily: "var(--f-display)", fontWeight: 400,
              fontSize: "clamp(52px, 8vw, 132px)",
              letterSpacing: "-0.03em", lineHeight: 0.9, margin: 0,
              fontVariationSettings: '"opsz" 144, "SOFT" 30',
            }}>
              <span style={{ whiteSpace: "nowrap" }}>{headingLine1}</span><br/>
              <em style={{ fontStyle: "normal", fontFamily: "var(--f-body)", fontWeight: 400, letterSpacing: "-0.02em" }}>
                {headingLine2}
              </em>
            </h2>
            <div style={{ display: "flex", justifyContent: "flex-end", alignItems: "end", gap: 20, paddingBottom: 12 }}>
              <span style={{ fontFamily: "var(--f-body)", fontSize: 11, letterSpacing: "0.22em", textTransform: "uppercase", color: "var(--ink-60)" }}>{handle}</span>
              <a href={followHref} target="_blank" rel="noopener noreferrer" style={{
                fontFamily: "var(--f-body)", fontSize: 11, letterSpacing: "0.22em",
                textTransform: "uppercase", color: "var(--ink)",
                textDecoration: "none", borderBottom: "1px solid var(--ink)",
                paddingBottom: 2,
              }}>Follow →</a>
            </div>
          </div>
        </Reveal>

        <div className="eb-lifestyle-grid" style={{
          display: "grid",
          gridTemplateColumns: "repeat(4, 1fr)",
          gridAutoRows: "240px",
          gap: 10,
        }}>
          {tiles.map((t, i) => {
            const span = t.span === "tall" ? { gridRow: "span 2" }
                       : t.span === "wide" ? { gridColumn: "span 2" } : {};
            return (
              <LifestyleTile key={i} tile={t} index={i} span={span} />
            );
          })}
        </div>
        <style>{`
          @media (max-width: 600px) {
            .eb-grit-heading { font-size: 36px !important; }
          }
          @media (max-width: 900px) {
            .eb-lifestyle-grid {
              grid-template-columns: repeat(2, 1fr) !important;
            }
          }
          @media (max-width: 480px) {
            .eb-lifestyle-grid {
              grid-template-columns: 1fr !important;
              grid-auto-rows: 200px !important;
            }
            .eb-lifestyle-grid > * { grid-column: auto !important; grid-row: auto !important; }
          }
          @media (max-width: 768px) {
            .eb-footer-contact { grid-template-columns: 1fr !important; }
            .eb-footer-addresses { grid-template-columns: 1fr 1fr !important; }
            .eb-footer-nav { grid-template-columns: 1fr 1fr !important; }
            .eb-footer-contact p { max-width: 100% !important; }
          }
          @media (max-width: 480px) {
            .eb-footer-addresses { grid-template-columns: 1fr !important; }
            .eb-footer-nav { grid-template-columns: 1fr !important; }
            .eb-footer-bottom { flex-direction: column; gap: 8px; }
          }
        `}</style>
      </div>
    </section>
  );
}

function LifestyleTile({ tile, index, span }) {
  const [ref, visible] = useReveal(0.1);
  const [hover, setHover] = React.useState(false);
  return (
    <div ref={ref}
      onMouseEnter={() => setHover(true)}
      onMouseLeave={() => setHover(false)}
      style={{
        position: "relative", overflow: "hidden",
        opacity: visible ? 1 : 0,
        transform: `translateY(${visible ? 0 : 28}px)`,
        transition: `opacity 900ms var(--ease-out) ${index * 50}ms, transform 900ms var(--ease-out) ${index * 50}ms`,
        ...span,
      }}>
      <div style={{
        position: "absolute", inset: 0,
        transform: hover ? "scale(1.05)" : "scale(1)",
        transition: "transform 900ms var(--ease-out)",
      }}>
        {tile.image ? (
          <img src={tile.image} alt={tile.label} style={{ width: "100%", height: "100%", objectFit: "cover", objectPosition: tile.position || "center", display: "block" }} />
        ) : (
          <Placeholder label={tile.label} tone={tile.tone} />
        )}
      </div>
    </div>
  );
}

function pickFooterText(value, fallback) {
  return (typeof value === "string" && value.trim()) ? value : fallback;
}

function pickFooterLines(value, fallback) {
  if (Array.isArray(value)) {
    const lines = value.map(function (line) {
      return String(line == null ? "" : line).trim();
    }).filter(Boolean);
    if (lines.length) return lines;
  }
  if (typeof value === "string" && value.trim()) {
    const lines = value.split(/\r?\n/).map(function (line) { return line.trim(); }).filter(Boolean);
    if (lines.length) return lines;
  }
  return fallback;
}

function pickFooterLinks(value, fallback) {
  if (Array.isArray(value) && value.length) {
    const links = value.filter(function (item) { return item && (item.label || item.href); });
    if (links.length) return links;
  }
  return fallback;
}

function FooterLines({ lines }) {
  return lines.map(function (line, i) {
    return (
      <React.Fragment key={i}>{i > 0 ? <br/> : null}{line}</React.Fragment>
    );
  });
}

function SiteFooter({ visible }) {
  if (visible === false) {
    return null;
  }
  const F = (typeof window !== "undefined" && window.EB_SITE && window.EB_SITE.footer) || {};
  const contactHeading = pickFooterText(F.contactHeading, "Get in touch");
  const contactBody = pickFooterText(
    F.contactBody,
    "If any Emma Basic product does not live up to your expectations, reach out and we will make every effort to arrange a replacement or refund."
  );
  const emailLabel = pickFooterText(F.emailLabel, "Email");
  const email = pickFooterText(F.email, "Boris@thebasicingredients.com");
  const londonHeading = pickFooterText(F.londonHeading, "London");
  const londonLines = pickFooterLines(F.londonLines, [
    "The Basic Ingredients Ltd",
    "4 New Concordia Wharf",
    "Mill Street",
    "London SE1 2BB",
  ]);
  const rotterdamHeading = pickFooterText(F.rotterdamHeading, "Rotterdam");
  const rotterdamLines = pickFooterLines(F.rotterdamLines, [
    "The Basic Ingredients B.V.",
    "Westplein 12–14",
    "3016BM Rotterdam",
    "The Netherlands",
  ]);
  const wordmarkLines = pickFooterLines(F.wordmark, ["Emma", "Basic."]);
  const cols = [
    [pickFooterText(F.browseHeading, "Browse"), pickFooterLinks(F.browseLinks, [
      { label: "Matcha", href: "Our Products.html#cat-matcha" },
      { label: "Oils", href: "Our Products.html#cat-oils" },
      { label: "Pantry", href: "Our Products.html#cat-pantry" },
      { label: "Full Collection", href: "Our Products.html" },
    ])],
    [pickFooterText(F.companyHeading, "Company"), pickFooterLinks(F.companyLinks, [
      { label: "Our Story", href: "Our Story.html" },
      { label: "People & Places", href: "People%20%26%20Places.html" },
      { label: "Find us", href: "Places.html" },
      { label: "Journal", href: "Journal.html" },
    ])],
  ];
  const legalLeft = pickFooterText(F.legalLeft, "© The Basic Ingredients Ltd · MMXXVI");
  const legalCenter = pickFooterText(F.legalCenter, "No Additives. Ever.");
  const legalRight = pickFooterText(F.legalRight, "London · Rotterdam");

  return (
    <footer style={{ background: "var(--paper)", borderTop: "1px solid var(--rule)" }}>
      <div style={{ maxWidth: "var(--maxw)", margin: "0 auto" }}>

        {/* Get in touch banner */}
        <div className="eb-footer-contact" style={{
          padding: "clamp(40px, 5vw, 64px) var(--pad-x)",
          borderBottom: "1px solid var(--rule)",
          display: "grid",
          gridTemplateColumns: "1fr 1fr",
          gap: "clamp(32px, 5vw, 80px)",
          alignItems: "start",
        }}>
          <div>
            <div style={{
              fontFamily: "var(--f-body)", fontSize: 10, letterSpacing: "0.22em",
              textTransform: "uppercase", color: "var(--ink-60)", marginBottom: 16,
            }}>{contactHeading}</div>
            <p style={{
              fontFamily: "var(--f-body)",
              fontSize: "clamp(18px, 1.8vw, 26px)", lineHeight: 1.35,
              margin: "0 0 28px",
              fontWeight: 400,
              maxWidth: 480,
            }}>
              {contactBody}
            </p>
            <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
              <a href={"mailto:" + email} style={{
                fontFamily: "var(--f-body)", fontSize: 16, letterSpacing: "0.14em",
                color: "var(--ink)", textDecoration: "none",
                display: "inline-flex", alignItems: "center", gap: 10,
              }}>
                <span style={{ opacity: 0.45, fontSize: 9, letterSpacing: "0.22em", textTransform: "uppercase" }}>{emailLabel}</span>
                {email}
              </a>
            </div>
          </div>

          {/* Office addresses */}
          <div className="eb-footer-addresses" style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 32 }}>
            <div>
              <div style={{
                fontFamily: "var(--f-body)", fontSize: 9.5, letterSpacing: "0.22em",
                textTransform: "uppercase", color: "var(--ink-60)", marginBottom: 14,
              }}>{londonHeading}</div>
              <address style={{
                fontStyle: "normal",
                fontFamily: "var(--f-display)", fontSize: 14, lineHeight: 1.75,
                fontVariationSettings: '"opsz" 14, "SOFT" 20',
                color: "var(--ink)",
              }}>
                <FooterLines lines={londonLines} />
              </address>
            </div>
            <div>
              <div style={{
                fontFamily: "var(--f-body)", fontSize: 9.5, letterSpacing: "0.22em",
                textTransform: "uppercase", color: "var(--ink-60)", marginBottom: 14,
              }}>{rotterdamHeading}</div>
              <address style={{
                fontStyle: "normal",
                fontFamily: "var(--f-display)", fontSize: 14, lineHeight: 1.75,
                fontVariationSettings: '"opsz" 14, "SOFT" 20',
                color: "var(--ink)",
              }}>
                <FooterLines lines={rotterdamLines} />
              </address>
            </div>
          </div>
        </div>

        {/* Nav + wordmark row */}
        <div className="eb-footer-nav" style={{
          padding: "clamp(40px, 5vw, 64px) var(--pad-x)",
          display: "grid", gridTemplateColumns: "1.4fr repeat(2, 1fr)", gap: 40,
          paddingBottom: 48,
        }}>
          <div>
            <div style={{
              fontFamily: "var(--f-display)", fontSize: "clamp(56px, 7vw, 96px)",
              letterSpacing: "-0.02em", lineHeight: 0.9,
              fontVariationSettings: '"opsz" 144, "SOFT" 20',
            }}>
              <FooterLines lines={wordmarkLines} />
            </div>
          </div>
          {cols.map(([h, items]) => (
            <div key={h}>
              <div style={{ fontFamily: "var(--f-body)", fontSize: 10.5, letterSpacing: "0.22em", textTransform: "uppercase", color: "var(--ink-60)", marginBottom: 20 }}>{h}</div>
              <ul style={{ listStyle: "none", padding: 0, margin: 0, display: "grid", gap: 12 }}>
                {items.map(x => (
                  <li key={x.label} style={{ fontFamily: "var(--f-body)", fontSize: 15, color: "var(--ink)" }}>
                    <a href={x.href} style={{ color: "inherit", textDecoration: "none" }}>{x.label}</a>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        {/* Bottom bar */}
        <div className="eb-footer-bottom" style={{
          padding: "24px var(--pad-x)",
          borderTop: "1px solid var(--rule)",
          display: "flex", justifyContent: "space-between",
          fontFamily: "var(--f-body)", fontSize: 10.5, letterSpacing: "0.22em",
          textTransform: "uppercase", color: "var(--ink-60)",
        }}>
          <span>{legalLeft}</span>
          <span>{legalCenter}</span>
          <span>{legalRight}</span>
        </div>
      </div>
    </footer>
  );
}

function AdditiveFreeBanner() {
  const [ref, visible] = useReveal(0.2);
  const B = (typeof window !== "undefined" && window.EB_HOME && window.EB_HOME.banner) || {};
  const bannerText = B.text || "The only mainstream brand in UK retail committed to additive-free across the entire range.";
  const bannerTag = B.tag || "Never Any Additives.";
  return (
    <section ref={ref} style={{
      background: "var(--ink)",
      color: "var(--paper)",
      padding: "clamp(48px, 7vh, 88px) var(--pad-x)",
      overflow: "hidden",
    }}>
      <div style={{ maxWidth: "var(--maxw)", margin: "0 auto", display: "flex", alignItems: "center", justifyContent: "space-between", gap: 32, flexWrap: "wrap", alignItems: "baseline" }}>
        <p style={{
          fontFamily: '"Futura", sans-serif', fontWeight: 400,
          fontSize: "clamp(18px, 2.2vw, 34px)",
          lineHeight: 1.2, letterSpacing: "0", margin: 0,
          opacity: visible ? 1 : 0,
          transform: `translateY(${visible ? 0 : 20}px)`,
          transition: "opacity 900ms var(--ease-out), transform 900ms var(--ease-out)",
          maxWidth: "72ch",
        }}>
          {bannerText}
        </p>
        <span style={{
          fontFamily: '"Futura", sans-serif', fontWeight: 400, fontStyle: "normal", fontSize: "clamp(13px, 1vw, 17px)",
          letterSpacing: "0.22em", color: "rgba(246,246,246,0.45)",
          whiteSpace: "nowrap", flexShrink: 0,
          opacity: visible ? 1 : 0,
          transition: "opacity 900ms var(--ease-out) 200ms",
        }}>
          {bannerTag}
        </span>
      </div>
    </section>
  );
}

window.AdditiveFreeBanner = AdditiveFreeBanner;
window.LifestyleGrid = LifestyleGrid;
window.SiteFooter = SiteFooter;
