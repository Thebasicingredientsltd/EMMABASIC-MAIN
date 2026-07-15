/* ============================================================
   PageHero — reusable interior-page hero. TypeReveal headline,
   hairline wipe, subtitle fade-up.
   ============================================================ */
function PageHero({ eyebrow, title, titleItalic, subtitle }) {
  const [lineRef, lineVisible] = useReveal(0.1);

  return (
    <section className="eb-page-hero" style={{
      padding: "180px var(--pad-x) clamp(32px, 5vh, 56px)",
      background: "#F6F6F6",
      color: "var(--ink)",
    }}>
      <div style={{ maxWidth: "var(--maxw)", margin: "0 auto" }}>

        {/* Eyebrow + hairline sweep */}
        <div ref={lineRef} style={{ marginBottom: 40 }}>
          <span style={{
            fontFamily: "var(--f-body)", fontSize: 11, letterSpacing: "0.22em",
            textTransform: "uppercase", color: "var(--ink-60)",
            display: "block", marginBottom: 16,
            opacity: lineVisible ? 1 : 0,
            transition: "opacity 600ms var(--ease-out) 100ms",
          }}>{eyebrow}</span>
          <div style={{
            height: 1, background: "var(--rule)",
            transformOrigin: "left",
            transform: lineVisible ? "scaleX(1)" : "scaleX(0)",
            transition: "transform 1000ms cubic-bezier(0.76, 0, 0.24, 1) 200ms",
          }} />
        </div>

        <div className="eb-page-hero__cols" style={{
          display: "grid",
          gridTemplateColumns: (subtitle && title) ? "1fr 1fr" : "1fr",
          gap: "clamp(32px, 6vw, 96px)",
          alignItems: "end",
        }}>
          {title && <h1 style={{
            fontFamily: "var(--f-display)", fontWeight: 400,
            fontSize: "clamp(40px, 5.5vw, 88px)",
            lineHeight: 1.05, letterSpacing: "-0.035em", margin: 0,
            overflow: "visible", paddingBottom: "0.08em",
            fontVariationSettings: '"opsz" 144, "SOFT" 30',
          }}>
            <TypeReveal text={title} delay={300} stagger={50} style={{ display: "block" }} />
            {titleItalic && (
              <em style={{ display: "block", fontStyle: "normal", fontFamily: "var(--f-body)", fontWeight: 400, letterSpacing: "-0.02em", marginTop: "-0.12em", wordSpacing: "-0.08em" }}>
                <TypeReveal text={titleItalic} delay={500} stagger={50} />
              </em>
            )}
          </h1>}

          {subtitle && (
            <Reveal delay={700}>
              <p style={{
                fontFamily: "var(--f-display)", fontStyle: "italic",
                fontSize: "clamp(16px, 1.4vw, 22px)", lineHeight: 1.5,
                margin: 0, paddingBottom: 8,
                color: "var(--ink-90)",
              }}>
                {subtitle}
              </p>
            </Reveal>
          )}
        </div>
      </div>
      <style>{`
        @media (max-width: 768px) {
          .eb-page-hero { padding-top: 120px !important; }
          .eb-page-hero__cols { grid-template-columns: 1fr !important; }
        }
      `}</style>
    </section>
  );
}
window.PageHero = PageHero;
