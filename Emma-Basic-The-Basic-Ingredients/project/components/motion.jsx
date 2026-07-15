/* ============================================================
   motion.jsx — lightweight scroll hooks used across sections
   ============================================================ */

// useReveal: returns [ref, visible] — flips true once the element scrolls into view
function useReveal(offset = 0.15) {
  const ref = React.useRef(null);
  const [visible, setVisible] = React.useState(false);
  React.useEffect(() => {
    if (!ref.current) return;
    const io = new IntersectionObserver(
      (entries) => {
        entries.forEach((e) => {
          if (e.isIntersecting) {
            setVisible(true);
            io.disconnect();
          }
        });
      },
      { threshold: offset }
    );
    io.observe(ref.current);
    return () => io.disconnect();
  }, [offset]);
  return [ref, visible];
}

// useScrollProgress: returns 0..1 progress of element crossing viewport
// 0 when top of element is at bottom of viewport; 1 when bottom has passed top.
function useScrollProgress() {
  const ref = React.useRef(null);
  const [p, setP] = React.useState(0);
  React.useEffect(() => {
    const onScroll = () => {
      if (!ref.current) return;
      const r = ref.current.getBoundingClientRect();
      const vh = window.innerHeight;
      const total = r.height + vh;
      const scrolled = vh - r.top;
      const next = Math.max(0, Math.min(1, scrolled / total));
      setP(next);
    };
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    window.addEventListener("resize", onScroll);
    return () => {
      window.removeEventListener("scroll", onScroll);
      window.removeEventListener("resize", onScroll);
    };
  }, []);
  return [ref, p];
}

// Reveal: wraps children, fades + lifts when visible
function Reveal({ children, delay = 0, y = 24, as = "div", style }) {
  const [ref, visible] = useReveal(0.12);
  const Tag = as;
  return (
    <Tag
      ref={ref}
      style={{
        opacity: visible ? 1 : 0,
        transform: `translateY(${visible ? 0 : y}px)`,
        transition: `opacity 900ms var(--ease-out) ${delay}ms, transform 900ms var(--ease-out) ${delay}ms`,
        ...style,
      }}
    >
      {children}
    </Tag>
  );
}

// TypeReveal: splits a string by word and reveals each with a stagger
function TypeReveal({ text, delay = 0, stagger = 60, style, as = "span" }) {
  const [ref, visible] = useReveal(0.15);
  const Tag = as;
  const words = String(text).split(" ");
  return (
    <Tag ref={ref} style={{ display: "inline-block", ...style }}>
      {words.map((w, i) => (
        <span key={i} style={{ display: "inline-block", overflow: "hidden", verticalAlign: "bottom", paddingTop: "0.2em", marginTop: "-0.2em", paddingBottom: "0.2em", marginBottom: "-0.2em" }}>
          <span style={{
            display: "inline-block",
            transform: visible ? "translateY(0)" : "translateY(110%)",
            opacity: visible ? 1 : 0,
            transition: `transform 900ms var(--ease-out) ${delay + i * stagger}ms, opacity 700ms var(--ease-out) ${delay + i * stagger}ms`,
          }}>
            {w}{i < words.length - 1 ? "\u00A0" : ""}
          </span>
        </span>
      ))}
    </Tag>
  );
}

window.useReveal = useReveal;
window.useScrollProgress = useScrollProgress;
window.Reveal = Reveal;
window.TypeReveal = TypeReveal;
