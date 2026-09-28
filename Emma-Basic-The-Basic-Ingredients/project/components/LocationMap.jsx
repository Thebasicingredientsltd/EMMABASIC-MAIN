/* ============================================================
   LocationMap — London HQ satellite map.
   Copy and coordinates come from window.EB_PLACES.hq (CRM →
   Where to find our products). Rendered at the bottom of People.
   ============================================================ */
function LocationMap() {
  const mapRef = React.useRef(null);
  const instanceRef = React.useRef(null);
  const hq = (window.EB_PLACES && window.EB_PLACES.hq) || {};
  const LAT = hq.lat || 51.5016;
  const LNG = hq.lng || -0.0710;
  const hqLabel = hq.label || "London HQ";
  const line1 = hq.addressLine1 || "4 New Concordia Wharf";
  const line2 = hq.addressLine2 || "Mill Street, London SE1 2BB";

  React.useEffect(() => {
    if (!mapRef.current || instanceRef.current) return;
    if (typeof L === "undefined") return;
    const isMobile = window.matchMedia("(max-width: 768px)").matches;
    const map = L.map(mapRef.current, {
      center: [LAT, LNG], zoom: 17, zoomControl: true,
      scrollWheelZoom: false, dragging: !isMobile, attributionControl: false,
    });
    instanceRef.current = map;
    L.tileLayer("https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}", { maxZoom: 19 }).addTo(map);
    L.tileLayer("https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}", { maxZoom: 19, opacity: 0.85 }).addTo(map);
    const pinSvg = `<svg width="52" height="64" viewBox="0 0 52 64" fill="none" xmlns="http://www.w3.org/2000/svg">
      <ellipse cx="26" cy="61" rx="9" ry="3" fill="rgba(0,0,0,0.25)"/>
      <path d="M26 2C15.5 2 7 10.5 7 21C7 34 26 60 26 60C26 60 45 34 45 21C45 10.5 36.5 2 26 2Z" fill="white" stroke="#0A0A0A" stroke-width="1.5"/>
      <circle cx="26" cy="21" r="12" fill="white" stroke="#0A0A0A" stroke-width="1.2"/>
      <text x="26" y="25.5" text-anchor="middle" font-family="'JetBrains Mono', monospace" font-size="9.5" font-weight="500" letter-spacing="1" fill="#0A0A0A">HQ</text>
    </svg>`;
    const icon = L.divIcon({ html: pinSvg, iconSize: [52, 64], iconAnchor: [26, 62], className: "" });
    L.marker([LAT, LNG], { icon }).addTo(map);
    return () => { map.remove(); instanceRef.current = null; };
  }, [LAT, LNG]);

  return (
    <section id="london-hq" style={{ background: "var(--paper)", padding: "clamp(40px, 6vh, 72px) 0 clamp(48px, 7vh, 88px)" }}>
      <div style={{ maxWidth: "var(--maxw)", margin: "0 auto", padding: "0 var(--pad-x)" }}>
        <div style={{
          display: "flex", justifyContent: "space-between", alignItems: "baseline",
          flexWrap: "wrap", gap: 16,
          paddingBottom: "clamp(24px, 3vh, 36px)",
          borderBottom: "1px solid var(--rule)",
          marginBottom: "clamp(24px, 3vh, 36px)",
        }}>
          <span style={{ fontFamily: "var(--f-mono)", fontSize: 10.5, letterSpacing: "0.24em", textTransform: "uppercase", color: "var(--ink-60)" }}>{hqLabel}</span>
          <address style={{ fontStyle: "normal", fontFamily: "var(--f-mono)", fontSize: 10.5, letterSpacing: "0.14em", color: "var(--ink-60)", textAlign: "right" }}>
            {line1} &middot; {line2}
          </address>
        </div>
        <div className="eb-map-wrap" style={{ width: "100%", height: "clamp(360px, 50vw, 580px)", border: "1px solid var(--rule)", position: "relative" }}>
          <div ref={mapRef} style={{ width: "100%", height: "100%" }} />
          <div style={{ position: "absolute", bottom: 20, left: 20, zIndex: 1000, background: "white", border: "1px solid rgba(10,10,10,0.12)", padding: "14px 18px", boxShadow: "0 2px 16px rgba(0,0,0,0.14)", pointerEvents: "none", minWidth: 220 }}>
            <div style={{ fontFamily: "var(--f-mono)", fontSize: 9, letterSpacing: "0.22em", textTransform: "uppercase", color: "rgba(10,10,10,0.45)", marginBottom: 8 }}>{hqLabel}</div>
            <div style={{ fontFamily: "var(--f-mono)", fontSize: 10.5, letterSpacing: "0.1em", color: "#0A0A0A", lineHeight: 1.6, marginBottom: 14 }}>
              {line1}<br/>{line2}
            </div>
            <div style={{ borderTop: "1px solid rgba(10,10,10,0.1)", paddingTop: 10, display: "grid", gap: 6 }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", gap: 16 }}>
                <span style={{ fontFamily: "var(--f-mono)", fontSize: 9, letterSpacing: "0.18em", textTransform: "uppercase", color: "rgba(10,10,10,0.45)" }}>London Bridge</span>
                <span style={{ fontFamily: "var(--f-mono)", fontSize: 10, letterSpacing: "0.1em", color: "#0A0A0A" }}>18 min walk</span>
              </div>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", gap: 16 }}>
                <span style={{ fontFamily: "var(--f-mono)", fontSize: 9, letterSpacing: "0.18em", textTransform: "uppercase", color: "rgba(10,10,10,0.45)" }}>Bermondsey</span>
                <span style={{ fontFamily: "var(--f-mono)", fontSize: 10, letterSpacing: "0.1em", color: "#0A0A0A" }}>12 min walk</span>
              </div>
            </div>
          </div>
        </div>
      </div>
      <style>{`
        .eb-map-wrap .leaflet-control-attribution { display: none; }
        .eb-map-wrap .leaflet-control-zoom a {
          font-family: 'JetBrains Mono', monospace !important;
          color: #0A0A0A !important;
          border-color: rgba(10,10,10,0.15) !important;
        }
        .eb-map-wrap .leaflet-control-zoom {
          border: 1px solid rgba(10,10,10,0.15) !important;
          box-shadow: 0 2px 12px rgba(0,0,0,0.12) !important;
        }
      `}</style>
    </section>
  );
}
window.LocationMap = LocationMap;
