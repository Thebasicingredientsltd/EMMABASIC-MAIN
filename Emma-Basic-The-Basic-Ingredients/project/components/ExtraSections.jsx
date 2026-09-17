/* Extra CMS sections — freeform blocks added from the visual editor. */
function ExtraSections({ source }) {
  const data = source || {};
  const sections = (data.extraSections || []).filter(function (s) {
    return s && s.visible !== false;
  });
  if (!sections.length) return null;
  return (
    <>
      {sections.map(function (s) {
        const html = String(s.body || "").replace(/\n/g, "<br/>");
        return (
          <section key={s.id} id={s.id} style={{
            background: "var(--paper)",
            padding: "var(--section-y) var(--pad-x)",
          }}>
            <div style={{ maxWidth: "var(--maxw)", margin: "0 auto" }}>
              <h2 style={{
                fontFamily: "var(--f-display)",
                fontSize: "clamp(32px, 5vw, 56px)",
                fontWeight: 400,
                letterSpacing: "-0.03em",
                margin: "0 0 16px",
              }}>{s.heading}</h2>
              <p style={{
                fontFamily: "var(--f-body)",
                fontSize: 18,
                lineHeight: 1.55,
                maxWidth: 680,
                margin: 0,
              }} dangerouslySetInnerHTML={{ __html: html }} />
            </div>
          </section>
        );
      })}
    </>
  );
}
window.ExtraSections = ExtraSections;
