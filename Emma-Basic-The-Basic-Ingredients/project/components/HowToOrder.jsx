/* ============================================================
   HowToOrder — Become a Distributor page, laid out like the
   "How to Place Your First Order" new-customer sheet.
   Copy is CMS-managed on window.EB_PEOPLE.distributor.
   ============================================================ */
function HowToOrder() {
  const d = (typeof window !== "undefined" && window.EB_PEOPLE && window.EB_PEOPLE.distributor) || {};
  const steps = Array.isArray(d.steps) ? d.steps : [];
  const other = d.otherWays || {};
  const collect = other.collect || {};
  const own = other.ownDistributor || {};
  const sheet = d.sheetFooter || {};
  const title = d.title || "How to Place Your First Order";
  const email = d.email || "beatrice@thebasicingredients.com";

  function shown(section) {
    if (!section || typeof section !== "object") return true;
    return section.visible !== false;
  }

  function cms(field) {
    return { "data-cms-key": "people", "data-cms-path": "distributor." + field };
  }

  function linkEmails(text, keyPrefix) {
    const parts = String(text || "").split(/([A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,})/i);
    return parts.map((part, i) => {
      if (/^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i.test(part)) {
        return (
          <a key={keyPrefix + i} href={"mailto:" + part} style={{ color: "inherit", textDecoration: "underline" }}>
            {part}
          </a>
        );
      }
      return part;
    });
  }

  function lineBlock(lines, path) {
    const items = Array.isArray(lines) ? lines : [];
    return items.map((line, i) => {
      if (!String(line).trim()) {
        return <div key={path + i} style={{ height: 12 }} />;
      }
      return (
        <p key={path + i} style={{
          fontFamily: "var(--f-body)",
          fontSize: "clamp(15px, 1.15vw, 17px)",
          lineHeight: 1.55,
          color: "var(--ink-90)",
          margin: "0 0 6px",
        }}>
          {linkEmails(line, path + i)}
        </p>
      );
    });
  }

  return (
    <section id="how-to-order" style={{
      background: "var(--paper)",
      padding: "clamp(112px, 13vh, 140px) var(--pad-x) clamp(48px, 8vh, 88px)",
    }}>
      <div style={{ maxWidth: 760, margin: "0 auto" }}>

        {shown(d) && (
          <header style={{
            background: "var(--ink)",
            color: "var(--paper)",
            textAlign: "center",
            padding: "28px 24px 26px",
          }}>
            <h1 {...cms("title")} style={{
              fontFamily: "var(--f-body)",
              fontWeight: 600,
              fontSize: "clamp(22px, 2.4vw, 28px)",
              letterSpacing: "-0.02em",
              lineHeight: 1.25,
              margin: "0 0 10px",
              color: "var(--paper)",
            }}>{title}</h1>
            <a {...cms("email")} href={"mailto:" + email} style={{
              fontFamily: "var(--f-body)",
              fontWeight: 600,
              fontSize: "clamp(15px, 1.2vw, 18px)",
              color: "var(--paper)",
              textDecoration: "none",
            }}>{email}</a>
          </header>
        )}

        {steps.map((step, i) => {
          if (!shown(step)) return null;
          const bullets = Array.isArray(step.bullets) ? step.bullets : [];
          return (
            <div key={i} className="hto-step" style={{
              display: "grid",
              gridTemplateColumns: "88px 1fr",
              marginTop: 16,
            }}>
              <div style={{
                background: "var(--ink-90)",
                color: "var(--paper)",
                textAlign: "center",
                padding: "18px 8px 16px",
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                justifyContent: "center",
                gap: 4,
              }}>
                <div style={{ fontSize: 22, lineHeight: 1 }}>{step.icon || ""}</div>
                <div style={{
                  fontFamily: "var(--f-body)",
                  fontWeight: 700,
                  fontSize: "clamp(28px, 3vw, 36px)",
                  lineHeight: 1,
                  color: "var(--paper)",
                }}>{step.number || String(i + 1)}</div>
              </div>
              <div style={{
                background: "var(--paper-shade)",
                padding: "18px 22px 16px",
              }}>
                <h2 style={{
                  fontFamily: "var(--f-body)",
                  fontWeight: 700,
                  fontSize: "clamp(17px, 1.4vw, 20px)",
                  color: "var(--ink)",
                  margin: "0 0 10px",
                  letterSpacing: "-0.015em",
                }}>{step.title}</h2>
                <ul style={{ margin: 0, padding: "0 0 0 1.15em" }}>
                  {bullets.map((b, bi) => (
                    <li key={bi} style={{
                      fontFamily: "var(--f-body)",
                      fontSize: "clamp(15px, 1.15vw, 17px)",
                      lineHeight: 1.55,
                      color: "var(--ink-90)",
                      margin: "0 0 6px",
                    }}>{linkEmails(b, "s" + i + "b" + bi)}</li>
                  ))}
                </ul>
              </div>
            </div>
          );
        })}

        {shown(other) && (
          <div style={{ marginTop: 28 }}>
            <h2 {...cms("otherWays.heading")} style={{
              fontFamily: "var(--f-body)",
              fontWeight: 700,
              fontSize: "clamp(18px, 1.5vw, 22px)",
              color: "var(--ink)",
              margin: "0 0 14px",
              letterSpacing: "-0.015em",
            }}>{other.heading || "Other Ways to Receive Your Order"}</h2>
            <div className="hto-other" style={{
              display: "grid",
              gridTemplateColumns: "1fr 1fr",
              gap: 12,
            }}>
              <div style={{ background: "var(--paper-shade)", padding: "20px 22px 18px" }}>
                <h3 style={{
                  fontFamily: "var(--f-body)",
                  fontWeight: 700,
                  fontSize: "clamp(16px, 1.25vw, 18px)",
                  color: "var(--ink)",
                  margin: "0 0 12px",
                }}>{collect.title || "Collect from Our Warehouse"}</h3>
                {lineBlock(collect.lines, "c")}
              </div>
              <div style={{ background: "var(--paper-shade)", padding: "20px 22px 18px" }}>
                <h3 style={{
                  fontFamily: "var(--f-body)",
                  fontWeight: 700,
                  fontSize: "clamp(16px, 1.25vw, 18px)",
                  color: "var(--ink)",
                  margin: "0 0 12px",
                }}>{own.title || "Use Your Own Distributor"}</h3>
                {lineBlock(own.lines, "o")}
              </div>
            </div>
          </div>
        )}

        {shown(sheet) && (
          <p style={{
            fontFamily: "var(--f-body)",
            fontSize: 13,
            color: "var(--ink-40)",
            textAlign: "center",
            margin: "28px 0 0",
            paddingTop: 16,
            borderTop: "1px solid var(--rule)",
          }}>{sheet.text || "thebasicingredients.com  |  New customer guide  |  May 2026"}</p>
        )}
      </div>
      <style>{`
        @media (max-width: 640px) {
          .hto-step { grid-template-columns: 64px 1fr !important; }
          .hto-other { grid-template-columns: 1fr !important; }
        }
      `}</style>
    </section>
  );
}
window.HowToOrder = HowToOrder;
