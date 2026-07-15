/* ============================================================
   FounderNarrative — office photo zooms in as you scroll into
   it, peaks near full-bleed, zooms back out as you leave.
   ============================================================ */

const _EB_FOUNDER = (typeof window !== "undefined" && window.EB_HOME && window.EB_HOME.founder) || {};
const FOUNDER_IMAGE = _EB_FOUNDER.image || "assets/homepage/office-photo.webp";
const FOUNDER_INTRO = _EB_FOUNDER.introLine || "I am a mum, who has learned to read food labels over the years.";
const FOUNDER_PARAGRAPHS = (Array.isArray(_EB_FOUNDER.paragraphs) && _EB_FOUNDER.paragraphs.length) ? _EB_FOUNDER.paragraphs : [
  "Not just food labels, but also skincare, clothing, furniture — anything that comes into direct contact with the human body, I always check the components first. We cook most meals at home, from scratch. Some of the veggies, home grown from our allotment. We never cook alone. Home cooking is not a chore but a way of spending time together. Our daughter is 12. Every moment with her is precious before she flies away from the nest of mum & dad.",
  "Born and bred in a food manufacturer, reading labels comes naturally to me. These days, food packaging is cunningly designed. When you see an &ldquo;organic&rdquo; logo or a nutrition claim, it leads you to believe the product is healthy. The reality is that even organic and &ldquo;nutritious&rdquo; foods can contain ultra-processed ingredients (UPFs) and additives.",
  "There are over 1,000 additives approved by EU food authorities and thousands more worldwide — legal but harmful to us. Additives are sneaky — they can alter colours, create addictive flavours, and extend shelf life indefinitely. If you're not in the food industry — whether you're an engineer, an accountant, or even a doctor — reading food labels can be daunting.",
  "For this reason, Emma Basic was born.",
  'Emma Basic promises "Never Any Additives." We\'ve removed additives from all our products, so you don\'t have to spend 10,000 hours decoding unpronounceable ingredients. By choosing Emma Basic, you protect yourself and your family from the thousands of additives widely used in today\'s food industry.',
];

const PREVIEW_COUNT = 2;

function useScrollBell(ref) {
  const [t, setT] = React.useState(0);
  React.useEffect(() => {
    const el = ref.current;
    if (!el) return;
    let rafId = null;
    function update() {
      if (rafId) return;
      rafId = requestAnimationFrame(() => {
        rafId = null;
        const rect = el.getBoundingClientRect();
        const vh = window.innerHeight;
        const elH = rect.height;
        const entered = vh - rect.top;
        const total = vh + elH;
        const raw = entered / total;
        const bell = Math.max(0, Math.min(1, 1 - Math.abs(raw - 0.5) * 2));
        setT(bell);
      });
    }
    window.addEventListener("scroll", update, { passive: true });
    update();
    return () => { window.removeEventListener("scroll", update); if (rafId) cancelAnimationFrame(rafId); };
  }, []);
  return t;
}

function FounderNarrative({ hideReadMore = false }) {
  const sectionRef = React.useRef(null);
  const t = useScrollBell(sectionRef);
  const [revealRef, visible] = useReveal(0);
  const [textRevealRef, textVisible] = useReveal(0.05);
  const [expanded, setExpanded] = React.useState(false);

  // t goes 0→1→0 as section scrolls through viewport
  // container padding shrinks to near-zero at peak (full bleed)
  // On mobile, skip the zoom effect and show full-width with minimal padding
  const isMobile = typeof window !== "undefined" && window.innerWidth <= 600;
  const sidePad = isMobile ? "0px" : `calc(3cm + (8vw - 3cm) * ${Math.max(0, 1 - t * 1.4).toFixed(3)})`;
  const imgScale = isMobile ? 1 : 1 + t * 0.14;
  const imgAspect = isMobile ? "3/4" : "auto";

  const visibleParas = hideReadMore || expanded
    ? FOUNDER_PARAGRAPHS
    : FOUNDER_PARAGRAPHS.slice(0, PREVIEW_COUNT);

  return (
    <>
      {/* ── Office photo — zooms to full-bleed on scroll ── */}
      <section
        ref={sectionRef}
        style={{ padding: "clamp(20px, 3vh, 40px) 0 0", background: "var(--paper)", overflow: "hidden" }}
      >
        <div style={{ margin: "0 auto", padding: `0 ${sidePad}`, transition: "padding 60ms linear" }}>
          <div
            ref={revealRef}
            style={{
              position: "relative",
              overflow: "hidden",
              clipPath: visible ? "inset(0% 0% 0% 0%)" : "inset(8% 0% 8% 0%)",
              opacity: visible ? 1 : 0,
              transition: "clip-path 1600ms cubic-bezier(0.76, 0, 0.24, 1), opacity 800ms ease",
            }}
          >
            {/* Image with gentle scale */}
            <div style={{
              overflow: "hidden",
              marginBottom: "-2cm",
              transform: `scale(${imgScale.toFixed(4)})`,
              transformOrigin: "center center",
              transition: "transform 60ms linear",
              willChange: "transform",
            }}>
              <img
                src={FOUNDER_IMAGE}
                alt="Emma Basic — founder"
                style={{
                  display: "block",
                  width: "100%",
                  height: isMobile ? "110vw" : "55vw",
                  objectFit: "cover",
                  objectPosition: isMobile ? "center center" : "center top",
                  maxWidth: "none",
                  filter: "none",
                }}
              />
            </div>

          </div>
        </div>
      </section>

      {/* ── Founder prose ── */}
      <section style={{
        padding: "clamp(32px, 5vh, 64px) var(--pad-x) clamp(48px, 8vh, 96px)",
        background: "var(--paper)",
      }}>
        <div style={{ maxWidth: 1131, margin: "0 auto" }}>
          <Reveal>
            <p style={{
              fontFamily: "var(--f-body)", fontWeight: 400,
              fontSize: "clamp(22px, 2.4vw, 36px)",
              lineHeight: 1.25, letterSpacing: "-0.01em",
              color: "var(--ink)", margin: "0 0 clamp(32px, 5vh, 52px)",
            }}>
              {FOUNDER_INTRO}
            </p>
          </Reveal>
          <div style={{
            fontFamily: "var(--f-body)", fontSize: "clamp(18px, 1.35vw, 20px)",
            lineHeight: 1.75, color: "var(--ink-90)",
            display: "grid", gap: "1.4em",
          }}>
            {visibleParas.map((text, i) => (
              <Reveal key={i} delay={i * 80}>
                <p style={{ margin: 0 }} dangerouslySetInnerHTML={{ __html: text }} />
              </Reveal>
            ))}
          </div>

          {!hideReadMore && (
            <Reveal delay={120}>
              <div style={{ marginTop: "clamp(32px, 5vh, 52px)", display: "flex", justifyContent: "flex-end" }}>
                <a
                  href="Our Story.html"
                  style={{
                    display: "inline-flex", alignItems: "center", gap: 10,
                    fontFamily: "var(--f-body)", fontSize: 12.5, letterSpacing: "0.14em",
                    textTransform: "uppercase", textDecoration: "none",
                    border: "1px solid var(--ink)",
                    padding: "14px 22px",
                    color: "var(--ink)", background: "transparent",
                    transition: "background 180ms var(--ease-out), color 180ms var(--ease-out)",
                  }}
                  onMouseEnter={e => { e.currentTarget.style.background = "var(--ink)"; e.currentTarget.style.color = "var(--paper)"; }}
                  onMouseLeave={e => { e.currentTarget.style.background = "transparent"; e.currentTarget.style.color = "var(--ink)"; }}
                >
                  <span>Read more</span>
                  <span style={{ fontFamily: "var(--f-mono)", fontSize: 11 }}>→</span>
                </a>
              </div>
            </Reveal>
          )}
        </div>
      </section>
    </>
  );
}

window.FounderNarrative = FounderNarrative;
