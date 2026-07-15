/* ============================================================
   Placeholder — monospace-labeled striped SVG image slot.
   In production, replace <Placeholder /> usages with <Image />.
   ============================================================ */
function Placeholder({ label = "IMAGE", tone = "warm", ratio, className, style, children, rounded = 0 }) {
  // tone: "warm" (paper), "cool" (mist), "ink" (dark). Strict B&W.
  const palettes = {
    warm: { a: "#EDEAE2", b: "#E2DED3", text: "#6B6355" },
    cool: { a: "#E8E8E6", b: "#DADAD6", text: "#5F5F5C" },
    ink:  { a: "#161616", b: "#0C0C0C", text: "#8A8A86" },
  };
  const p = palettes[tone] || palettes.warm;

  const inner = (
    <div
      aria-label={label}
      style={{
        position: "absolute", inset: 0,
        background: `repeating-linear-gradient(135deg, ${p.a} 0 14px, ${p.b} 14px 28px)`,
        display: "flex", alignItems: "center", justifyContent: "center",
        color: p.text,
        fontFamily: "var(--f-mono)",
        fontSize: 11, letterSpacing: "0.22em", textTransform: "uppercase",
        ...style,
      }}
    >
      <div style={{
        padding: "6px 10px",
        border: `1px solid ${p.text}33`,
        background: `${p.a}cc`,
        backdropFilter: "blur(2px)",
      }}>
        {children || label}
      </div>
    </div>
  );

  if (ratio) {
    return (
      <div className={className} style={{ position: "relative", width: "100%", aspectRatio: ratio, borderRadius: rounded, overflow: "hidden" }}>
        {inner}
      </div>
    );
  }
  return (
    <div className={className} style={{ position: "relative", width: "100%", height: "100%", borderRadius: rounded, overflow: "hidden" }}>
      {inner}
    </div>
  );
}

window.Placeholder = Placeholder;
