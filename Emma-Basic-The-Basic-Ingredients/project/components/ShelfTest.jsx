/* ============================================================
   ShelfTest — replaces the "two typefaces" thesis.
   Side-by-side label comparison: supermarket vs Emma Basic.
   Dramatizes the ingredient-list difference.
   ============================================================ */
function ShelfTest() {
  const S = (typeof window !== "undefined" && window.EB_HOME && window.EB_HOME.shelfTest) || {};
  const headingLine1 = S.headingLine1 || "Flip the pack.";
  const headingLine2 = S.headingLine2 || "Read the jar.";
  const subtitle = S.subtitle || 'Two packs of crispy seaweed.<br/>Both in the "healthy snacks" aisle.';
  const closingLine1 = S.closingLine1 || "If it's in the pack, it's on the label.";
  const closingLine2 = S.closingLine2 || "That's the whole promise.";
  // Competitor: Yutaka Seasoned Seaweed Snack (widely sold in UK supermarkets)
  const supermarket = (Array.isArray(S.theirs) && S.theirs.length) ? S.theirs : [
    "Seaweed (70%)",
    "Soybean oil",
    "Sugar",
    "Salt",
    "Monosodium glutamate (E621)",
    "Dextrose",
    "Hydrolysed soy protein",
    "Yeast extract",
    "Flavour enhancer: disodium 5'-ribonucleotides (E635)",
  ];
  // Emma Basic Crispy Seaweed — product label
  const emma = (Array.isArray(S.ours) && S.ours.length) ? S.ours : [
    "Roasted nori seaweed",
    "Extra virgin olive oil",
    "Sea salt",
  ];

  return (
    <section style={{
      padding: "clamp(60px, 9vh, 110px) var(--pad-x) clamp(32px, 5vh, 64px)",
      background: "var(--paper)",
      color: "var(--ink)",
      overflow: "hidden",
    }}>
      <div style={{ maxWidth: 1320, margin: "0 auto" }}>

        <div className="eb-shelftest-header" style={{
          display: "grid", gridTemplateColumns: "1fr auto", alignItems: "end",
          gap: 32, marginBottom: "clamp(56px, 8vh, 96px)",
        }}>
          <Reveal>
            <h2 className="eb-shelftest-heading" style={{
              fontFamily: "var(--f-display)", fontWeight: 400,
              fontSize: "clamp(52px, 8vw, 132px)",
              lineHeight: 0.9, letterSpacing: "-0.03em", margin: 0,
              fontFeatureSettings: "normal",
            }}>
              <span style={{ fontFamily: "'Minerva Modern'", fontWeight: 400 }}>{headingLine1}</span><br/>
              <em style={{ fontStyle: "normal", fontFamily: "var(--f-body)", fontWeight: 400, letterSpacing: "-0.02em" }}>
                {headingLine2}
              </em>
            </h2>
          </Reveal>
          <Reveal delay={180}>
            <p className="eb-shelftest-subtitle" style={{
              fontFamily: "var(--f-body)", fontSize: 15, lineHeight: 1.6,
              maxWidth: 320, margin: 0, color: "var(--ink-90)",
              textAlign: "right", paddingBottom: 12,
            }} dangerouslySetInnerHTML={{ __html: subtitle }} />
          </Reveal>
        </div>

        <div className="eb-shelftest-grid" style={{
          display: "grid", gridTemplateColumns: "1fr 1fr",
          gap: "clamp(16px, 2.4vw, 40px)",
          alignItems: "stretch",
        }}>
          <LabelCard kind="theirs" items={supermarket} />
          <LabelCard kind="ours" items={emma} />
        </div>

        <Reveal delay={400}>
          <div style={{
            marginTop: "clamp(64px, 10vh, 112px)",
            display: "flex", justifyContent: "center",
          }}>
            <p style={{
              fontFamily: "var(--f-display)", fontStyle: "italic",
              fontSize: "clamp(24px, 3vw, 42px)",
              lineHeight: 1.25, margin: 0, textAlign: "center",
              maxWidth: 720,
              fontVariationSettings: '"opsz" 144, "SOFT" 80',
            }}>
              {closingLine1}<br/>
              <span style={{ fontStyle: "normal", fontFamily: "var(--f-display)", fontVariationSettings: '"opsz" 144, "SOFT" 30' }}>
                {closingLine2}
              </span>
            </p>
          </div>
        </Reveal>
      </div>
    </section>
  );
}

function LabelCard({ kind, items }) {
  const [ref, visible] = useReveal(0.15);
  const isOurs = kind === "ours";

  return (
    <div ref={ref} style={{
      position: "relative",
      background: isOurs ? "var(--paper-bright)" : "#EFECE4",
      border: `1px solid ${isOurs ? "var(--ink)" : "var(--rule-strong)"}`,
      padding: "clamp(28px, 3.4vw, 56px)",
      minHeight: 560,
      display: "flex", flexDirection: "column",
      opacity: visible ? 1 : 0,
      transform: `translateY(${visible ? 0 : 40}px)`,
      transition: `opacity 1000ms var(--ease-out) ${isOurs ? 260 : 120}ms, transform 1000ms var(--ease-out) ${isOurs ? 260 : 120}ms`,
    }}>
      {/* Top meta row */}
      <div className="eb-label-meta" style={{
        display: "flex", justifyContent: "space-between",
        paddingBottom: 20, borderBottom: `1px solid ${isOurs ? "var(--ink)" : "var(--rule-strong)"}`,
        fontFamily: "var(--f-body)", fontSize: 10, letterSpacing: "0.22em",
        textTransform: "uppercase", color: isOurs ? "var(--ink)" : "var(--ink-60)",
      }}>
        <span>{isOurs ? "Emma Basic" : "Competitor Benchmark"}</span>
        <span>Ingredients</span>
      </div>

      {/* Headline mark */}
      <div style={{
        paddingTop: "clamp(24px, 4vh, 44px)",
        paddingBottom: "clamp(20px, 3vh, 32px)",
        display: "flex", alignItems: "baseline", gap: 18,
      }}>
        <span className="eb-label-number" style={{
          fontFamily: "var(--f-display)", fontWeight: 400,
          fontSize: "clamp(72px, 10vw, 156px)", lineHeight: 0.82,
          letterSpacing: "-0.03em",
          color: isOurs ? "var(--ink)" : "var(--ink-60)",
          fontVariationSettings: '"opsz" 144, "SOFT" 30',
        }}>
          {items.length}
        </span>
        <span style={{
          fontFamily: "var(--f-body)", fontSize: 11, letterSpacing: "0.22em",
          textTransform: "uppercase", color: isOurs ? "var(--ink)" : "var(--ink-60)",
          paddingBottom: 16,
        }}>
          {isOurs ? (items.length === 1 ? "Ingredient Only" : "Ingredients Only") : (items.length === 1 ? "Ingredient" : "Ingredients")}
        </span>
      </div>

      {/* Ingredient list */}
      <ol style={{
        listStyle: "none", margin: 0, padding: 0,
        display: "grid", gap: 10,
        flex: 1,
      }}>
        {items.map((x, i) => (
          <LabelRow key={i} text={x} index={i} dim={!isOurs} strikethrough={!isOurs && shouldStrike(x)} visible={visible} />
        ))}
      </ol>

      {/* Bottom tag */}
      <div style={{
        marginTop: "clamp(24px, 4vh, 40px)",
        paddingTop: 20, borderTop: `1px solid ${isOurs ? "var(--ink)" : "var(--rule-strong)"}`,
        display: "flex", justifyContent: "space-between", alignItems: "center",
      }}>
        <span style={{
          fontFamily: "var(--f-body)", fontSize: 10, letterSpacing: "0.22em",
          textTransform: "uppercase", color: isOurs ? "var(--ink)" : "var(--ink-60)",
        }}>
          {isOurs ? "Nothing else." : "Incl. MSG & flavour enhancers"}
        </span>
        {isOurs && (
          <span style={{
            fontFamily: "var(--f-display)", fontStyle: "italic",
            fontSize: 20, color: "var(--ink)",
            fontVariationSettings: '"opsz" 24, "SOFT" 100',
          }}>
            — Emma
          </span>
        )}
      </div>
    </div>
  );
}

function LabelRow({ text, index, dim, strikethrough, visible }) {
  return (
    <li className="eb-label-row" style={{
      display: "grid", gridTemplateColumns: "auto 1fr", gap: 14,
      fontFamily: "var(--f-body)",
      fontSize: "clamp(13.5px, 1vw, 15.5px)", lineHeight: 1.45,
      color: dim ? "var(--ink-60)" : "var(--ink)",
      textDecoration: strikethrough ? "line-through" : "none",
      textDecorationThickness: "0.5px",
      opacity: visible ? 1 : 0,
      transform: `translateY(${visible ? 0 : 10}px)`,
      transition: `opacity 500ms var(--ease-out) ${400 + index * 40}ms, transform 500ms var(--ease-out) ${400 + index * 40}ms`,
    }}>
      <span style={{ fontFamily: "var(--f-mono)", fontSize: 10, paddingTop: 2, opacity: 0.6 }}>
        {String(index + 1).padStart(2, "0")}
      </span>
      <span>{text}</span>
    </li>
  );
}

// Strike through anything that reads as a chemical additive
function shouldStrike(s) {
  return /\bE\d{2,3}|emulsifier|stabiliser|preservative|antioxidant|modified|regulator|colour|flavouring|lecithin|xanthan|sorbate|monosodium|glutamate|dextrose|hydrolysed|flavour enhancer|soybean oil/i.test(s);
}

const _shelfStyle = document.createElement("style");
_shelfStyle.textContent = `
  @media (max-width: 600px) {
    .eb-shelftest-grid { gap: 10px !important; }
    .eb-shelftest-grid > div { padding: 16px !important; min-height: 0 !important; }
    .eb-label-number { font-size: 52px !important; }
    .eb-label-row { font-size: 11px !important; }
    .eb-label-meta { font-size: 8.5px !important; letter-spacing: 0.22em !important; }
    .eb-shelftest-heading { font-size: 38px !important; white-space: nowrap; }
    .eb-shelftest-header { grid-template-columns: 1fr !important; }
    .eb-shelftest-subtitle { text-align: left !important; max-width: 100% !important; padding-bottom: 0 !important; }
  }
`;
document.head.appendChild(_shelfStyle);

window.ShelfTest = ShelfTest;
