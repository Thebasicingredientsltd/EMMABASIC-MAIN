/* ============================================================
   Hero — Full-bleed photo with type overlaid.
   Uses double-RAF to guarantee initial frame paints before the
   reveal transition starts. Class-based toggle avoids race where
   React commits both states in one paint.
   ============================================================ */
function Hero() {
  const [imgRef, p] = useScrollProgress();
  const [loaded, setLoaded] = React.useState(false);
  React.useLayoutEffect(() => {
    // Wait two frames so the initial (hidden) style definitely paints,
    // THEN flip to loaded and let the transition run.
    let raf2;
    const raf1 = requestAnimationFrame(() => {
      raf2 = requestAnimationFrame(() => setLoaded(true));
    });
    return () => { cancelAnimationFrame(raf1); cancelAnimationFrame(raf2); };
  }, []);

  // Apple-style expand: starts as inset rounded card, expands to full-bleed
  const expandP = Math.min(1, p * 2.5); // completes at ~40% scroll
  const inset = (1 - expandP) * 5;       // 5vw → 0
  const radius = (1 - expandP) * 20;     // 20px → 0
  const innerScale = 1.04 + p * 0.06;
  const ty = (0.5 - p) * 30;
  const overlayOpacity = 0.22 + p * 0.18;

  return (
    <section ref={imgRef} className={`eb-hero ${loaded ? "eb-hero--in" : ""}`} style={{
      position: "relative",
      height: "100vh", minHeight: 720,
      color: "var(--paper)",
      background: "var(--paper)",
    }}>
      {/* Expanding container */}
      <div style={{
        position: "absolute",
        top: `${inset * 0.6}vh`, bottom: `${inset * 0.6}vh`,
        left: `${inset}vw`, right: `${inset}vw`,
        borderRadius: radius,
        overflow: "hidden",
        transition: "top 20ms linear, bottom 20ms linear, left 20ms linear, right 20ms linear, border-radius 20ms linear",
      }}>
      {/* Photo plate */}
      <div style={{
        position: "absolute", inset: 0,
        transform: `scale(${innerScale}) translate3d(0, ${ty}px, 0)`,
        transformOrigin: "center",
        transition: "transform 40ms linear",
      }}>
        <img
          src="assets/Hero-Home-Page-Running.png"
          alt="Sport trainers on grit"
          style={{
            width: "100%", height: "100%",
            objectFit: "cover", objectPosition: "center",
            display: "block",
          }}
        />
      </div>

      <div style={{
        position: "absolute", inset: 0,
        background: `linear-gradient(180deg, rgba(10,10,10,0.35) 0%, rgba(10,10,10,${overlayOpacity}) 45%, rgba(10,10,10,0.6) 100%)`,
      }}/>

      {/* Type */}
      <div className="eb-hero__type-pad" style={{
        position: "absolute", inset: 0,
        display: "flex", flexDirection: "column",
        justifyContent: "center",
        padding: "120px var(--pad-x) 80px",
      }}>
        <div style={{ maxWidth: 1280, width: "100%", display: "grid", gap: "clamp(24px, 4vh, 48px)" }}>
          <h1 style={{
            margin: 0,
            fontSize: "clamp(56px, 10vw, 160px)",
            letterSpacing: "-0.035em",
            lineHeight: 0.9,
            fontFamily: "var(--f-display)",
            fontWeight: 400,
          }}>
            <span className="eb-hero__mask">
              <span className="eb-hero__slide eb-hero__slide--1">Recovery,</span>
            </span>
            <br/>
            <span className="eb-hero__mask">
              <em className="eb-hero__slide eb-hero__slide--2" style={{ fontStyle: "italic" }}>uncompromised.</em>
            </span>
          </h1>

          <div className="eb-hero__body">
            <p style={{
              fontFamily: "var(--f-body)",
              fontSize: "clamp(18px, 1.6vw, 24px)", lineHeight: 1.35,
              maxWidth: 640, margin: 0,
              fontWeight: 400,
            }}>
              Pure ingredients for pure effort<br/>for the run, the kitchen, and everything between.
            </p>
            <div className="eb-hero__buttons" style={{ display: "flex", gap: 12, flexWrap: "wrap", alignSelf: "end" }}>
              <HeroButton label="Browse the Collection" href="Our Products.html" primary />
              <HeroButton label="Read Our Story" href="People%20%26%20Places.html" />
            </div>
          </div>
        </div>
      </div>

      <div className="eb-hero__scroll" style={{
        position: "absolute", left: "50%", bottom: 24,
        transform: "translateX(-50%)",
        fontFamily: "var(--f-body)", fontSize: 10, letterSpacing: "0.22em",
        textTransform: "uppercase",
        display: "flex", flexDirection: "column", alignItems: "center", gap: 10,
      }}>
        <span>Scroll</span>
        <span style={{
          width: 1, height: 36,
          background: "var(--paper)",
          animation: "ebDrop 2.2s var(--ease-out) infinite",
          transformOrigin: "top",
        }}/>
      </div>

      </div>{/* end expanding container */}

      {/* Letterbox bars — retract on load */}
      <div className="eb-hero__bar eb-hero__bar--top" />
      <div className="eb-hero__bar eb-hero__bar--bot" />

      <style>{`
        @keyframes ebDrop { 0%{transform:scaleY(0);opacity:0} 40%{transform:scaleY(1);opacity:1} 100%{transform:scaleY(1) translateY(30px);opacity:0} }

        /* Letterbox bars */
        .eb-hero__bar {
          position: absolute; left: 0; right: 0;
          background: var(--ink);
          z-index: 2;
          transition: height 1400ms cubic-bezier(0.76, 0, 0.24, 1);
        }
        .eb-hero__bar--top { top: 0; height: 50%; }
        .eb-hero__bar--bot { bottom: 0; height: 50%; }
        .eb-hero--in .eb-hero__bar--top { height: 0; }
        .eb-hero--in .eb-hero__bar--bot { height: 0; }

        .eb-hero__mask { display: inline-block; overflow: hidden; vertical-align: bottom; line-height: 0.9; padding-bottom: 0.2em; margin-bottom: -0.16em; }
        .eb-hero__slide {
          display: inline-block;
          transform: translateY(110%);
          transition: transform 1200ms cubic-bezier(0.22, 1, 0.36, 1);
        }
        .eb-hero--in .eb-hero__slide--1 { transform: translateY(0); transition-delay: 1300ms; }
        .eb-hero--in .eb-hero__slide--2 { transform: translateY(0); transition-delay: 1500ms; }

        .eb-hero__body {
          display: grid; grid-template-columns: minmax(0, 320px) 1fr; gap: 48px; align-items: end;
          opacity: 0; transform: translateY(20px);
          transition: opacity 900ms cubic-bezier(0.22, 1, 0.36, 1) 2000ms,
                      transform 900ms cubic-bezier(0.22, 1, 0.36, 1) 2000ms;
        }
        .eb-hero--in .eb-hero__body { opacity: 1; transform: translateY(0); }

        .eb-hero__scroll {
          opacity: 0;
          transition: opacity 600ms var(--ease-out) 2600ms;
        }
        .eb-hero--in .eb-hero__scroll { opacity: 0.7; }

        @media (max-width: 820px) {
          .eb-hero__body { grid-template-columns: 1fr; gap: 24px; }
        }
        @media (max-width: 768px) {
          .eb-hero__type-pad { padding-top: 80px !important; padding-bottom: 56px !important; }
        }
        @media (max-width: 600px) {
          .eb-hero__buttons { flex-direction: column; align-items: flex-start; }
          .eb-hero__buttons a { width: 100%; justify-content: center; }
        }
      `}</style>
    </section>
  );
}

function HeroButton({ label, href = "#", primary }) {
  const [hover, setHover] = React.useState(false);
  return (
    <a href={href} onMouseEnter={() => setHover(true)} onMouseLeave={() => setHover(false)} style={{
      display: "inline-flex", alignItems: "center", gap: 10,
      padding: "14px 22px", whiteSpace: "nowrap",
      fontFamily: "var(--f-body)", fontSize: 12.5, letterSpacing: "0.14em",
      textTransform: "uppercase", textDecoration: "none",
      border: `1px solid ${primary ? "var(--paper)" : "rgba(246,246,246,0.6)"}`,
      background: primary ? (hover ? "transparent" : "var(--paper)") : (hover ? "var(--paper)" : "transparent"),
      color: primary ? (hover ? "var(--paper)" : "var(--ink)") : (hover ? "var(--ink)" : "var(--paper)"),
      transition: "background 180ms var(--ease-out), color 180ms var(--ease-out)",
    }}>
      <span>{label}</span>
      <span style={{ fontFamily: "var(--f-mono)", fontSize: 11 }}>→</span>
    </a>
  );
}

window.Hero = Hero;
