/* ============================================================
   ProductRail — horizontal "shelf" row.
   Bottles stand side-by-side. Scroll horizontally (wheel/drag/arrows).
   Click opens the Label Decoder drawer.
   ============================================================ */
function ProductRail({ onOpen }) {
  const railRef = React.useRef(null);
  const [canL, setCanL] = React.useState(false);
  const [canR, setCanR] = React.useState(true);
  const dragRef = React.useRef({ dragging: false, startX: 0, scrollLeft: 0, moved: false });

  const rafRef = React.useRef(null);
  const update = React.useCallback(() => {
    if (rafRef.current) return;
    rafRef.current = requestAnimationFrame(() => {
      rafRef.current = null;
      const el = railRef.current; if (!el) return;
      setCanL(el.scrollLeft > 4);
      setCanR(el.scrollLeft + el.clientWidth < el.scrollWidth - 4);
    });
  }, []);
  React.useEffect(() => {
    update();
    const el = railRef.current; if (!el) return;
    el.addEventListener("scroll", update, { passive: true });
    window.addEventListener("resize", update);
    return () => {
      el.removeEventListener("scroll", update);
      window.removeEventListener("resize", update);
      if (rafRef.current) cancelAnimationFrame(rafRef.current);
    };
  }, [update]);

  const onMouseDown = React.useCallback((e) => {
    const el = railRef.current; if (!el) return;
    dragRef.current = { dragging: true, startX: e.pageX - el.offsetLeft, scrollLeft: el.scrollLeft, moved: false };
    el.style.cursor = "grabbing";
    el.style.userSelect = "none";
  }, []);

  const onMouseMove = React.useCallback((e) => {
    const d = dragRef.current; if (!d.dragging) return;
    const el = railRef.current; if (!el) return;
    const x = e.pageX - el.offsetLeft;
    const walk = (x - d.startX) * 1.2;
    if (Math.abs(walk) > 4) d.moved = true;
    el.scrollLeft = d.scrollLeft - walk;
  }, []);

  const stopDrag = React.useCallback(() => {
    const el = railRef.current; if (!el) return;
    dragRef.current.dragging = false;
    el.style.cursor = "grab";
    el.style.userSelect = "";
  }, []);

  const nudge = (dir) => {
    const el = railRef.current; if (!el) return;
    el.scrollBy({ left: dir * (el.clientWidth * 0.7), behavior: "smooth" });
  };

  return (
    <section id="products" style={{
      padding: "clamp(60px, 9vh, 110px) 0 clamp(40px, 6vh, 80px)",
      background: "var(--paper)",
      position: "relative",
    }}>
      <div style={{
        padding: "0 var(--pad-x)",
        marginBottom: "clamp(48px, 6vh, 80px)",
      }}>
        <Reveal>
          <h2 style={{
            fontFamily: '"Futura", sans-serif', fontWeight: 400,
            fontSize: "clamp(52px, 8vw, 132px)",
            lineHeight: 0.9, letterSpacing: "-0.02em", margin: 0,
          }}>
            Our team's staples.
          </h2>
        </Reveal>
      </div>

      {/* Scroll progress bar + arrows */}
      <div className="eb-rail-arrows-wrap" style={{ display: "flex", alignItems: "center", gap: 16, margin: "0 var(--pad-x)", marginBottom: "clamp(20px, 3vh, 36px)" }}>
        <ArrowButton disabled={!canL} onClick={() => nudge(-1)} dir="left" />
        <div style={{ flex: 1 }}>
          <ScrollTrack railRef={railRef} canL={canL} canR={canR} />
        </div>
        <ArrowButton disabled={!canR} onClick={() => nudge(1)} dir="right" />
      </div>

      {/* Rail */}
      <div
        ref={railRef}
        onMouseDown={onMouseDown}
        onMouseMove={onMouseMove}
        onMouseUp={stopDrag}
        onMouseLeave={stopDrag}
        style={{
          display: "grid",
          gridAutoFlow: "column",
          gridAutoColumns: "clamp(160px, 42vw, 420px)",
          gap: "clamp(12px, 2vw, 32px)",
          overflowX: "auto",
          scrollSnapType: "x mandatory",
          WebkitOverflowScrolling: "touch",
          paddingTop: 0,
          paddingBottom: 40,
          paddingLeft: "clamp(20px, 4vw, 64px)",
          paddingRight: "clamp(20px, 4vw, 64px)",
          margin: "0 var(--pad-x)",
          scrollbarWidth: "none",
          willChange: "scroll-position",
          transform: "translateZ(0)",
          cursor: "grab",
        }}
      >
        {PRODUCTS.map((p, i) => (
          <ShelfTile key={p.id} p={p} index={i} onOpen={() => { if (!dragRef.current.moved) onOpen(p.id); }} />
        ))}
        {/* Terminal tile */}
        <div style={{
          scrollSnapAlign: "start",
          display: "flex", alignItems: "center", justifyContent: "center",
          minWidth: 280,
        }}>
          <a href="#" style={{
            fontFamily: "var(--f-body)", fontSize: 11, letterSpacing: "0.22em",
            textTransform: "uppercase", color: "var(--ink)",
            textDecoration: "none", borderBottom: "1px solid var(--ink)",
            paddingBottom: 2, whiteSpace: "nowrap",
          }}>
            The Full Collection →
          </a>
        </div>
      </div>

      <style>{`
        #products > div::-webkit-scrollbar { display: none; }
        @media (max-width: 600px) {
          .eb-rail-arrows-wrap { display: none !important; }
          #products { padding-top: clamp(80px, 14vh, 140px) !important; }
          .eb-shelf-meta h3 { font-size: 18px !important; }
          .eb-shelf-meta span { font-size: 9px !important; letter-spacing: 0.22em !important; }
        }
      `}</style>
    </section>
  );
}

function ShelfTile({ p, index, onOpen }) {
  const [hover, setHover] = React.useState(false);
  const [ref, visible] = useReveal(0.12);
  return (
    <button
      ref={ref}
      onClick={onOpen}
      onMouseEnter={() => setHover(true)}
      onMouseLeave={() => setHover(false)}
      style={{
        scrollSnapAlign: "start",
        textAlign: "left", padding: 0, border: 0, background: "transparent",
        cursor: "pointer", fontFamily: "inherit", color: "inherit",
        display: "grid", gap: 20,
        opacity: visible ? 1 : 0,
        transform: `translateY(${visible ? 0 : 10}px)`,
        transition: `opacity 600ms var(--ease-out) ${index * 20}ms, transform 600ms var(--ease-out) ${index * 20}ms`,
      }}
    >
      {/* Bottle on pedestal */}
      <div style={{
        position: "relative",
        aspectRatio: "3/4",
        background: "var(--paper-shade)",
        border: "1px solid var(--rule)",
        overflow: "hidden",
      }}>
        <div style={{
          position: "absolute", inset: 0,
          transition: "transform 700ms var(--ease-out)",
          transform: hover ? "scale(1.04)" : "scale(1)",
        }}>
          {p.image ? (
            <img src={p.image} alt={p.name} style={{ width: "100%", height: "100%", objectFit: "cover", objectPosition: p.imagePosition || "center center", display: "block", transform: p.imageZoom ? `scale(${p.imageZoom})` : "none", transformOrigin: p.imagePosition || "center center" }} />
          ) : (
            <Placeholder label={`${p.name.toUpperCase()}`} tone={p.tone} />
          )}
        </div>
        {p.pill && (
          <div style={{ position: "absolute", top: 16, left: 16 }}>
            <Pill label={p.pill} />
          </div>
        )}
        <div style={{
          position: "absolute", left: 0, right: 0, bottom: 0,
          padding: 16,
          background: "linear-gradient(180deg, transparent 0%, rgba(10,10,10,0.75) 100%)",
          color: "var(--paper)",
          transform: hover ? "translateY(0)" : "translateY(12px)",
          opacity: hover ? 1 : 0,
          transition: "all 300ms var(--ease-out)",
          display: "flex", justifyContent: "space-between", alignItems: "end",
        }}>
          <span style={{ fontFamily: "var(--f-body)", fontSize: 10.5, letterSpacing: "0.22em", textTransform: "uppercase" }}>
            Read the Label
          </span>
          <span style={{ fontFamily: "var(--f-mono)", fontSize: 14 }}>→</span>
        </div>
      </div>
      <div style={{ display: "grid", gap: 6 }} className="eb-shelf-meta">
        <h3 style={{
          fontFamily: '"Minerva Modern", serif', fontWeight: 400,
          fontSize: 26, letterSpacing: "0", margin: 0,
          lineHeight: 1.05, textAlign: "left",
        }}>
          {p.name}
        </h3>
        <span style={{
          fontFamily: "var(--f-body)", fontWeight: 400, fontSize: 10.5, letterSpacing: "0.22em",
          textTransform: "uppercase", color: "var(--ink-60)", textAlign: "left",
        }}>
          {p.origin}
        </span>
      </div>
    </button>
  );
}

function ArrowButton({ disabled, onClick, dir }) {
  const [hover, setHover] = React.useState(false);
  return (
    <button onClick={onClick} disabled={disabled}
      onMouseEnter={() => setHover(true)}
      onMouseLeave={() => setHover(false)}
      style={{
        width: 48, height: 48, borderRadius: 0,
        border: "1px solid var(--ink)",
        background: hover && !disabled ? "var(--ink)" : "transparent",
        color: hover && !disabled ? "var(--paper)" : "var(--ink)",
        opacity: disabled ? 0.25 : 1,
        cursor: disabled ? "default" : "pointer",
        display: "flex", alignItems: "center", justifyContent: "center",
        fontFamily: "var(--f-mono)", fontSize: 16,
        transition: "all 180ms var(--ease-out)",
      }}>
      {dir === "left" ? "←" : "→"}
    </button>
  );
}

function ScrollTrack({ railRef }) {
  const [progress, setProgress] = React.useState(0);
  const trackRef = React.useRef(null);
  const dragging = React.useRef(false);

  React.useEffect(() => {
    const el = railRef.current;
    if (!el) return;
    const update = () => {
      const max = el.scrollWidth - el.clientWidth;
      setProgress(max > 0 ? el.scrollLeft / max : 0);
    };
    update();
    el.addEventListener("scroll", update, { passive: true });
    window.addEventListener("resize", update);
    return () => {
      el.removeEventListener("scroll", update);
      window.removeEventListener("resize", update);
    };
  }, [railRef]);

  const seekTo = React.useCallback((clientX) => {
    const track = trackRef.current;
    const el = railRef.current;
    if (!track || !el) return;
    const rect = track.getBoundingClientRect();
    const trackWidth = rect.width - 110; // exclude the "Drag to scroll" label zone
    const ratio = Math.max(0, Math.min(1, (clientX - rect.left) / trackWidth));
    const max = el.scrollWidth - el.clientWidth;
    el.scrollLeft = ratio * max;
  }, [railRef]);

  const onMouseDown = (e) => {
    dragging.current = true;
    seekTo(e.clientX);
    e.preventDefault();
  };
  const onMouseMove = React.useCallback((e) => {
    if (dragging.current) seekTo(e.clientX);
  }, [seekTo]);
  const onMouseUp = React.useCallback(() => { dragging.current = false; }, []);

  React.useEffect(() => {
    window.addEventListener("mousemove", onMouseMove);
    window.addEventListener("mouseup", onMouseUp);
    return () => {
      window.removeEventListener("mousemove", onMouseMove);
      window.removeEventListener("mouseup", onMouseUp);
    };
  }, [onMouseMove, onMouseUp]);

  const LABEL_RESERVE = 110; // px reserved for "Drag to scroll" label
  const THUMB_RATIO = 0.3;   // thumb is 30% of the bar zone

  return (
    <div
      ref={trackRef}
      onMouseDown={onMouseDown}
      style={{
        height: 24,
        display: "flex", alignItems: "center",
        cursor: "grab",
        position: "relative",
        flex: 1,
      }}
    >
      {/* Scroll hint label */}
      <span style={{
        position: "absolute", right: 0, top: "50%",
        transform: "translateY(-50%)",
        fontFamily: "var(--f-body)", fontSize: 9.5, letterSpacing: "0.22em",
        textTransform: "uppercase", color: "var(--ink-40)",
        pointerEvents: "none", whiteSpace: "nowrap",
      }}>Drag to scroll</span>

      {/* Track background — stays within bar zone */}
      <div style={{
        position: "absolute", left: 0, right: LABEL_RESERVE,
        height: 2, background: "var(--rule)",
        borderRadius: 2,
      }} />
      {/* Thumb — sized and positioned relative to bar zone via calc() */}
      <div style={{
        position: "absolute",
        top: "50%",
        left: `calc((100% - ${LABEL_RESERVE}px) * ${progress * (1 - THUMB_RATIO)})`,
        transform: "translateY(-50%)",
        width: `calc((100% - ${LABEL_RESERVE}px) * ${THUMB_RATIO})`,
        height: 2,
        background: "var(--ink)",
        borderRadius: 2,
        transition: "left 80ms cubic-bezier(0.25, 1, 0.5, 1)",
      }} />
    </div>
  );
}

window.ProductRail = ProductRail;
