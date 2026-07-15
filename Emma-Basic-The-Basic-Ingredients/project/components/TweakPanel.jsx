function TweakPanel({ open, state, setState }) {
  if (!open) return null;
  const K = ({ label, children }) => (
    <div style={{ display: "grid", gap: 8, paddingBottom: 14, borderBottom: "1px solid rgba(246,246,246,0.14)" }}>
      <span style={{ fontFamily: "var(--f-mono)", fontSize: 10, letterSpacing: "0.22em", textTransform: "uppercase", color: "rgba(246,246,246,0.55)" }}>{label}</span>
      {children}
    </div>
  );
  const B = ({ active, onClick, children }) => (
    <button onClick={onClick} style={{
      padding: "6px 10px",
      fontFamily: "var(--f-mono)", fontSize: 10.5, letterSpacing: "0.14em", textTransform: "uppercase",
      border: `1px solid ${active ? "#F6F6F6" : "rgba(246,246,246,0.3)"}`,
      background: active ? "#F6F6F6" : "transparent",
      color: active ? "#0A0A0A" : "#F6F6F6",
      cursor: "pointer",
    }}>{children}</button>
  );
  return (
    <div style={{
      position: "fixed", right: 20, bottom: 20, zIndex: 90,
      width: 260, padding: 18,
      background: "#0A0A0A", color: "#F6F6F6",
      fontFamily: "var(--f-body)", display: "grid", gap: 14,
    }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline" }}>
        <span style={{ fontFamily: "var(--f-display)", fontSize: 20, fontVariationSettings: '"opsz" 24, "SOFT" 40' }}>Tweaks</span>
        <span style={{ fontFamily: "var(--f-mono)", fontSize: 9.5, letterSpacing: "0.22em", color: "rgba(246,246,246,0.55)" }}>MG · v2</span>
      </div>
      <K label="Serif">
        <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
          <B active={state.serif === "fraunces"} onClick={() => setState({ serif: "fraunces" })}>Fraunces</B>
          <B active={state.serif === "playfair"} onClick={() => setState({ serif: "playfair" })}>Playfair</B>
          <B active={state.serif === "dmserif"} onClick={() => setState({ serif: "dmserif" })}>DM Serif</B>
        </div>
      </K>
      <K label="Paper Tone">
        <div style={{ display: "flex", gap: 6 }}>
          <B active={state.paper === "warm"} onClick={() => setState({ paper: "warm" })}>Warm</B>
          <B active={state.paper === "cool"} onClick={() => setState({ paper: "cool" })}>Cool</B>
          <B active={state.paper === "bright"} onClick={() => setState({ paper: "bright" })}>Bright</B>
        </div>
      </K>
    </div>
  );
}
window.TweakPanel = TweakPanel;
