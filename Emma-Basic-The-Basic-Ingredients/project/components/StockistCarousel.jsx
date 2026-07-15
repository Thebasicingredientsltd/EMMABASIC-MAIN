/* ============================================================
   StockistCarousel — horizontal rail of retailer names/logos.
   Hand-drawn-in-type logos for visual integrity.
   ============================================================ */

const CAROUSEL_RETAILERS = [
  { id: "selfridges",  name: "SELFRIDGES",  city: "London · Oxford St",     style: "uppercase-sans", url: "https://www.google.com/maps/place/Selfridges+Foodhall/@51.5148527,-0.1566824,17z/data=!4m6!3m5!1s0x487605e932cccb71:0x9f1bcf2a610b6def!8m2!3d51.5148527!4d-0.1541075!16s%2Fg%2F11skfvt9j7?entry=ttu&g_ep=EgoyMDI2MDQyMS4wIKXMDSoASAFQAw%3D%3D" },
  { id: "wholefoods",  name: "Whole Foods", city: "London · Kensington",    style: "script", url: "https://www.google.com/maps/search/wholefoods/@51.5148508,-0.174707,14z/data=!3m1!4b1?entry=ttu&g_ep=EgoyMDI2MDQyMS4wIKXMDSoASAFQAw%3D%3D" },
  { id: "harrods",     name: "HARRODS",     city: "London · Knightsbridge", style: "serif-mark", url: "https://www.harrods.com/en-gb/search?term=emma+basic" },
  { id: "souschef",    name: "Sous Chef",   city: "Online · UK",            style: "sans-light", url: "https://www.souschef.co.uk/pages/search-results?q=emma+basic" },
];

const TBI_RETAILERS = [
  { id: "jjfoods", name: "JJ Foods", city: "London · East End",   style: "sans-mark",    url: "https://www.jjfoodservice.com/search?b=EN-MW&page=2&q=emma%20basic&size=12&sortType=search" },
  { id: "mahalo",  name: "Mahalo",   city: "London · Shoreditch", style: "serif-italic", url: "https://mahalosupplies.com/search?type=product%2Carticle%2Cpage&q=emma+basic" },
  { id: "clf",     name: "CLF",      city: "UK Wide",             style: "uppercase-sans", url: "https://www.clfdistribution.com/" },
  { id: "diverse", name: "Diverse Fine Foods", city: "UK Wide",             style: "sans-light",     url: "https://diversefinefood.co.uk/page/1/?s=emma+basic&post_type=product&dgwt_wcas=1" },
];

function StockistCarousel({ retailers, eyebrow, heading, headingItalic }) {
  const list = retailers || CAROUSEL_RETAILERS;
  const _eyebrow = eyebrow || "Where to find us";
  const _heading = heading || "Listed at a";
  const _headingItalic = headingItalic || "few good places.";
  const railRef = React.useRef(null);
  const [canL, setCanL] = React.useState(false);
  const [canR, setCanR] = React.useState(true);
  const dragRef = React.useRef({ active: false, startX: 0, scrollLeft: 0, moved: false });

  const update = () => {
    const el = railRef.current; if (!el) return;
    setCanL(el.scrollLeft > 4);
    setCanR(el.scrollLeft + el.clientWidth < el.scrollWidth - 4);
  };
  React.useEffect(() => {
    update();
    const el = railRef.current; if (!el) return;
    el.addEventListener("scroll", update, { passive: true });
    window.addEventListener("resize", update);
    const onWheel = (e) => {
      if (Math.abs(e.deltaX) > Math.abs(e.deltaY)) return;
      e.preventDefault();
      el.scrollBy({ left: e.deltaY * 2, behavior: "auto" });
    };
    el.addEventListener("wheel", onWheel, { passive: false });

    const onMouseDown = (e) => {
      dragRef.current = { active: true, startX: e.pageX - el.offsetLeft, scrollLeft: el.scrollLeft, moved: false };
      el.style.cursor = "grabbing";
      el.style.userSelect = "none";
    };
    const onMouseMove = (e) => {
      if (!dragRef.current.active) return;
      const x = e.pageX - el.offsetLeft;
      const delta = x - dragRef.current.startX;
      if (Math.abs(delta) > 4) dragRef.current.moved = true;
      el.scrollLeft = dragRef.current.scrollLeft - delta;
    };
    const onMouseUp = (e) => {
      if (!dragRef.current.active) return;
      dragRef.current.active = false;
      el.style.cursor = "grab";
      el.style.userSelect = "";
      if (dragRef.current.moved) {
        window._carouselDragged = true;
      }
    };
    const onMouseLeave = () => {
      if (dragRef.current.active) {
        dragRef.current.active = false;
        el.style.cursor = "grab";
        el.style.userSelect = "";
      }
    };

    el.style.cursor = "grab";
    el.addEventListener("mousedown", onMouseDown);
    el.addEventListener("mousemove", onMouseMove);
    el.addEventListener("mouseup", onMouseUp);
    el.addEventListener("mouseleave", onMouseLeave);

    return () => {
      el.removeEventListener("scroll", update);
      window.removeEventListener("resize", update);
      el.removeEventListener("wheel", onWheel);
      el.removeEventListener("mousedown", onMouseDown);
      el.removeEventListener("mousemove", onMouseMove);
      el.removeEventListener("mouseup", onMouseUp);
      el.removeEventListener("mouseleave", onMouseLeave);
    };
  }, []);

  const nudge = (dir) => {
    const el = railRef.current; if (!el) return;
    el.scrollBy({ left: dir * el.clientWidth * 0.8, behavior: "smooth" });
  };

  return (
    <section style={{
      padding: "clamp(40px, 6vh, 72px) 0",
      background: "var(--ink)",
      color: "var(--paper)",
    }}>
      <div style={{
        padding: "0 var(--pad-x)",
        display: "grid", gridTemplateColumns: "1fr auto", alignItems: "end",
        gap: 32, marginBottom: "clamp(40px, 6vh, 72px)",
      }}>
        <Reveal>
          <div>
            <span style={{
              fontFamily: "var(--f-body)", fontSize: 10.5, letterSpacing: "0.22em",
              textTransform: "uppercase", color: "rgba(246,246,246,0.55)",
              display: "block", marginBottom: 20,
            }}>{_eyebrow}</span>
            <h2 style={{
              fontFamily: "var(--f-display)", fontWeight: 400,
              fontSize: "clamp(44px, 6vw, 92px)",
              letterSpacing: "-0.03em", lineHeight: 0.92, margin: 0,
              fontVariationSettings: '"opsz" 144, "SOFT" 30',
            }}>
              {_heading}
              {_headingItalic && <><br/><em style={{ fontStyle: "normal", fontFamily: "var(--f-body)", fontWeight: 400, letterSpacing: "-0.02em" }}>{_headingItalic}</em></>}
            </h2>
          </div>
        </Reveal>
        <Reveal delay={160}>
          <div style={{ display: "flex", gap: 12, paddingBottom: 10 }}>
            <CarouselArrow disabled={!canL} onClick={() => nudge(-1)} dir="left" />
            <CarouselArrow disabled={!canR} onClick={() => nudge(1)} dir="right" />
          </div>
        </Reveal>
      </div>

      <div
        ref={railRef}
        style={{
          display: "grid", gridAutoFlow: "column",
          gridAutoColumns: "clamp(200px, 56vw, 380px)",
          gap: 0,
          overflowX: "auto",
          scrollSnapType: "x mandatory",
          padding: "0 var(--pad-x)",
          scrollbarWidth: "none",
        }}
        className="eb-stockist-rail"
      >
        {list.map((s, i) => (
          <StockistTile key={s.id} s={s} index={i} total={list.length} />
        ))}
      </div>

      <style>{`.eb-stockist-rail::-webkit-scrollbar { display: none; }`}</style>
    </section>
  );
}

function StockistTile({ s, index, total }) {
  const [ref, visible] = useReveal(0.1);
  const [hover, setHover] = React.useState(false);
  const Tag = s.url ? "a" : "div";
  return (
    <Tag
      ref={ref}
      href={s.url || undefined}
      target={s.url ? "_blank" : undefined}
      rel={s.url ? "noopener noreferrer" : undefined}
      onClick={(e) => { if (window._carouselDragged) { e.preventDefault(); window._carouselDragged = false; } }}
      onMouseEnter={() => setHover(true)}
      onMouseLeave={() => setHover(false)}
      style={{
        textDecoration: "none",
        scrollSnapAlign: "start",
        padding: "48px 40px",
        borderLeft: "1px solid rgba(246,246,246,0.14)",
        borderRight: index === CAROUSEL_RETAILERS.length - 1 ? "1px solid rgba(246,246,246,0.14)" : "none",
        minHeight: 280,
        display: "flex", flexDirection: "column", justifyContent: "space-between",
        background: hover ? "rgba(246,246,246,0.04)" : "transparent",
        transition: "background 260ms var(--ease-out)",
        opacity: visible ? 1 : 0,
        transform: `translateY(${visible ? 0 : 24}px)`,
        transitionProperty: "opacity, transform, background",
        transitionDuration: "700ms, 700ms, 260ms",
        transitionTimingFunction: "var(--ease-out)",
        transitionDelay: `${index * 80}ms, ${index * 80}ms, 0ms`,
      }}>
      <span style={{
        fontFamily: "var(--f-body)", fontSize: 10, letterSpacing: "0.22em",
        textTransform: "uppercase", color: "rgba(246,246,246,0.55)",
      }}>
        {String(index + 1).padStart(2, "0")} / {String(total).padStart(2, "0")}
      </span>

      <StockistLogo s={s} />

      <div style={{
        display: "flex", justifyContent: "space-between", alignItems: "end",
        paddingTop: 28, borderTop: "1px solid rgba(246,246,246,0.14)",
      }}>
        <span style={{
          fontFamily: "var(--f-body)", fontSize: 10.5, letterSpacing: "0.22em",
          textTransform: "uppercase", color: "rgba(246,246,246,0.7)",
        }}>{s.city}</span>
        <span style={{
          fontFamily: "var(--f-body)", fontSize: 10.5, letterSpacing: "0.22em",
          textTransform: "uppercase", color: "var(--paper)",
          opacity: hover ? 1 : 0.4,
          transition: "opacity 220ms var(--ease-out)",
        }}>Visit →</span>
      </div>
    </Tag>
  );
}

function StockistLogo({ s }) {
  const base = {
    color: "var(--paper)", textAlign: "left", display: "block",
    padding: "24px 0",
  };
  switch (s.style) {
    case "uppercase-sans":
      return <div style={{ ...base, fontFamily: "var(--f-body)", fontWeight: 600, letterSpacing: "0.3em", fontSize: "clamp(18px, 1.6vw, 22px)" }}>{s.name}</div>;
    case "script":
      return <div style={{ ...base, fontFamily: "var(--f-display)", fontStyle: "italic", fontSize: "clamp(36px, 4vw, 54px)", fontVariationSettings: '"opsz" 144, "SOFT" 100, "WONK" 1', letterSpacing: "-0.01em" }}>{s.name}</div>;
    case "serif-mark":
      return <div style={{ ...base, fontFamily: "var(--f-display)", fontWeight: 400, letterSpacing: "0.22em", fontSize: "clamp(22px, 2vw, 28px)", fontVariationSettings: '"opsz" 144, "SOFT" 20' }}>{s.name}</div>;
    case "sans-mark":
      return <div style={{ ...base, fontFamily: "var(--f-body)", fontWeight: 500, fontSize: "clamp(34px, 3.5vw, 48px)", letterSpacing: "-0.02em" }}>{s.name}</div>;
    case "serif-italic":
      return <div style={{ ...base, fontFamily: "var(--f-display)", fontStyle: "italic", fontSize: "clamp(40px, 4vw, 56px)", fontVariationSettings: '"opsz" 144, "SOFT" 80', letterSpacing: "-0.025em" }}>{s.name}</div>;
    case "sans-light":
      return <div style={{ ...base, fontFamily: "var(--f-body)", fontWeight: 400, fontSize: "clamp(28px, 2.8vw, 38px)", letterSpacing: "-0.01em" }}>{s.name}</div>;
    default:
      return <div style={{ ...base, fontFamily: "var(--f-display)", fontSize: 32 }}>{s.name}</div>;
  }
}

function CarouselArrow({ disabled, onClick, dir }) {
  const [hover, setHover] = React.useState(false);
  return (
    <button onClick={onClick} disabled={disabled}
      onMouseEnter={() => setHover(true)}
      onMouseLeave={() => setHover(false)}
      style={{
        width: 48, height: 48,
        border: "1px solid rgba(246,246,246,0.5)",
        background: hover && !disabled ? "var(--paper)" : "transparent",
        color: hover && !disabled ? "var(--ink)" : "var(--paper)",
        opacity: disabled ? 0.3 : 1,
        cursor: disabled ? "default" : "pointer",
        display: "flex", alignItems: "center", justifyContent: "center",
        fontFamily: "var(--f-mono)", fontSize: 16,
        transition: "all 180ms var(--ease-out)",
      }}>{dir === "left" ? "←" : "→"}</button>
  );
}

function TBIStockistCarousel() {
  return <StockistCarousel retailers={TBI_RETAILERS} eyebrow="Trade & Wholesale" heading="Order through" headingItalic="our distributors." />;
}

window.StockistCarousel = StockistCarousel;
window.TBIStockistCarousel = TBIStockistCarousel;
