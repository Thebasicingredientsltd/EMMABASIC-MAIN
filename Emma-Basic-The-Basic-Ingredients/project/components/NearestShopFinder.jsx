/* ============================================================
   NearestShopFinder — "Find your nearest shop" modal.
   Supports browser Geolocation or manual UK postcode entry.
   ============================================================ */

const FINDER_STORES = [
  { name: "Selfridges",       city: "London",       address: "400 Oxford St, London W1A 1AB",                          lat: 51.5143, lng: -0.1530 },
  { name: "Harrods",          city: "London",       address: "87–135 Brompton Rd, London SW1X 7XL",                    lat: 51.4994, lng: -0.1632 },
  { name: "Wholefoods",       city: "London",       address: "120 King's Rd, London SW3 4TR",                          lat: 51.4878, lng: -0.1616 },
  { name: "Corner Shop 180",  city: "London",       address: "7 Arundel St, London WC2R 3DA",                          lat: 51.5114, lng: -0.1134 },
  { name: "Trude's Grocery",  city: "London",       address: "10 The Pavement, London SW4 0HY",                        lat: 51.4600, lng: -0.1485 },
  { name: "Bayley & Sage",    city: "London",       address: "33–34 Marylebone High Street W1U 4QD",                   lat: 51.5200, lng: -0.1527 },
  { name: "Jones of Brockley",city: "London",       address: "354 Brockley Rd, London SE4 2BY",                        lat: 51.4593, lng: -0.0352 },
  { name: "Life of Fish",     city: "London",       address: "50 Abbeville Rd, London SW4 9NF",                        lat: 51.4538, lng: -0.1430 },
  { name: "Oseyo",            city: "London",       address: "Centre Court Shopping Centre, Wimbledon SW19 8YE",       lat: 51.4222, lng: -0.2067 },
  { name: "H Mart",           city: "London",       address: "Leigh Close, New Malden KT3 3NW",                        lat: 51.4010, lng: -0.2540 },
  { name: "Blukoo",           city: "London",       address: "Barningham Way, Kingsbury, London NW9 8AU",              lat: 51.5833, lng: -0.2631 },
  { name: "Toast Rack",       city: "London",       address: "314 Trinity Rd, London SW18 3RG",                        lat: 51.4470, lng: -0.1888 },
  { name: "Selfridges",       city: "Manchester",   address: "60 The Trafford Centre, Stretford M17 8DA",              lat: 53.4670, lng: -2.3490 },
  { name: "General Store",    city: "Manchester",   address: "9 Owen Street, Deansgate Square M15 4YB",                lat: 53.4726, lng: -2.2498 },
  { name: "Block & Bottle",   city: "Newcastle",    address: "188 Heaton Road, Newcastle upon Tyne NE6 5HP",           lat: 54.9779, lng: -1.5780 },
  { name: "C. Sinclair",      city: "Scotland",     address: "182 High Street, Burntisland KY3 9AP",                   lat: 56.0570, lng: -3.2330 },
  { name: "Quince & Cook",    city: "Scotland",     address: "Perth, Scotland",                                        lat: 56.3950, lng: -3.4310 },
  { name: "Chefslocker HQ",   city: "West Midlands",address: "22 Parade Centre, St. Mary's Place, Shrewsbury SY1 1DL",lat: 52.7085, lng: -2.7530 },
  { name: "Shop Kaizen",      city: "West Midlands",address: "22 Parade Centre, St. Mary's Place, Shrewsbury SY1 1DL",lat: 52.7085, lng: -2.7525 },
  { name: "Frankie's Studio", city: "Suffolk",      address: "14 High Street, Hadleigh IP7 5AP",                      lat: 52.0550, lng: 0.9620 },
  { name: "The Kitchen Table",city: "Dorset",       address: "1a Bell Street, Shaftesbury SP7 8AR",                   lat: 51.0048, lng: -2.1943 },
  { name: "Best Health Food", city: "East Sussex",  address: "Uckfield, East Sussex",                                  lat: 50.9690, lng: 0.0990 },
  { name: "Best Health Food", city: "West Sussex",  address: "Shoreham-by-Sea, West Sussex",                           lat: 50.8335, lng: -0.2730 },
  { name: "Hampshire Pantry", city: "Hampshire",    address: "Badger Farm Road, Winchester SO23 9RZ",                  lat: 51.0472, lng: -1.3290 },
  { name: "The Basic Ingredients B.V.", city: "Rotterdam", address: "Westplein 12–14, 3016BM Rotterdam",              lat: 51.9083, lng: 4.4640 },
];

function haversineKm(lat1, lng1, lat2, lng2) {
  const R = 6371;
  const dLat = (lat2 - lat1) * Math.PI / 180;
  const dLng = (lng2 - lng1) * Math.PI / 180;
  const a = Math.sin(dLat / 2) ** 2 + Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) * Math.sin(dLng / 2) ** 2;
  return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
}

function sortByPos(lat, lng) {
  return FINDER_STORES
    .map(s => ({ ...s, km: haversineKm(lat, lng, s.lat, s.lng) }))
    .sort((a, b) => a.km - b.km);
}

function NearestShopFinder() {
  const [open, setOpen] = React.useState(false);
  // status: "input" | "locating" | "ready" | "error"
  const [status, setStatus] = React.useState("input");
  const [errorMsg, setErrorMsg] = React.useState("");
  const [results, setResults] = React.useState([]);
  const [userPos, setUserPos] = React.useState(null);
  const [postcode, setPostcode] = React.useState("");
  const [postcodeError, setPostcodeError] = React.useState("");
  const mapRef = React.useRef(null);
  const mapInstance = React.useRef(null);

  const handleOpen = () => {
    setOpen(true);
    setStatus("input");
    setResults([]);
    setUserPos(null);
    setPostcode("");
    setPostcodeError("");
    setErrorMsg("");
  };

  const handleClose = () => {
    setOpen(false);
    if (mapInstance.current) { mapInstance.current.remove(); mapInstance.current = null; }
  };

  const resolveWithPos = (lat, lng) => {
    setUserPos({ lat, lng });
    setResults(sortByPos(lat, lng));
    setStatus("ready");
  };

  const handleUseLocation = () => {
    setStatus("locating");
    setErrorMsg("");
    if (!navigator.geolocation) {
      setStatus("error");
      setErrorMsg("Your browser doesn't support location sharing.");
      return;
    }
    navigator.geolocation.getCurrentPosition(
      (pos) => resolveWithPos(pos.coords.latitude, pos.coords.longitude),
      (err) => {
        setStatus("error");
        setErrorMsg(
          err.code === 1 ? "Location access was denied. Please allow location in your browser, or enter your postcode instead." :
          err.code === 2 ? "Couldn't determine your location. Try entering your postcode instead." :
          "Location request timed out. Try entering your postcode instead."
        );
      },
      { timeout: 12000 }
    );
  };

  const handlePostcodeSubmit = async (e) => {
    e && e.preventDefault();
    const pc = postcode.trim().toUpperCase().replace(/\s+/g, "");
    if (!pc) { setPostcodeError("Please enter a postcode."); return; }
    setPostcodeError("");
    setStatus("locating");
    try {
      const res = await fetch(`https://api.postcodes.io/postcodes/${encodeURIComponent(pc)}`);
      const data = await res.json();
      if (data.status === 200 && data.result) {
        resolveWithPos(data.result.latitude, data.result.longitude);
      } else {
        setStatus("input");
        setPostcodeError("Postcode not found. Please check and try again.");
      }
    } catch {
      setStatus("input");
      setPostcodeError("Couldn't look up that postcode. Please check your connection and try again.");
    }
  };

  // Build / refresh map when results land
  React.useEffect(() => {
    if (!open || status !== "ready" || !mapRef.current) return;
    if (mapInstance.current) { mapInstance.current.remove(); mapInstance.current = null; }

    const nearest = results[0];
    const map = L.map(mapRef.current, {
      center: [nearest.lat, nearest.lng],
      zoom: 13,
      zoomControl: true,
      scrollWheelZoom: false,
      attributionControl: false,
    });
    mapInstance.current = map;

    L.tileLayer("https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}", { maxZoom: 19 }).addTo(map);
    L.tileLayer("https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}", { maxZoom: 19, opacity: 0.85 }).addTo(map);

    // User pin
    const userSvg = `<svg width="28" height="28" viewBox="0 0 28 28" fill="none" xmlns="http://www.w3.org/2000/svg">
      <circle cx="14" cy="14" r="12" fill="#0A0A0A" stroke="white" stroke-width="2.5"/>
      <circle cx="14" cy="14" r="5" fill="white"/>
    </svg>`;
    L.marker([userPos.lat, userPos.lng], {
      icon: L.divIcon({ html: userSvg, iconSize: [28, 28], iconAnchor: [14, 14], className: "" })
    }).addTo(map).bindPopup("You are here");

    // Top 5 store pins
    results.slice(0, 5).forEach((s, i) => {
      const isPrimary = i === 0;
      const w = isPrimary ? 44 : 32, h = isPrimary ? 54 : 40;
      const pinSvg = `<svg width="${w}" height="${h}" viewBox="0 0 44 54" fill="none" xmlns="http://www.w3.org/2000/svg">
        <ellipse cx="22" cy="52" rx="7" ry="2.5" fill="rgba(0,0,0,0.2)"/>
        <path d="M22 2C13 2 6 9 6 18C6 29 22 52 22 52C22 52 38 29 38 18C38 9 31 2 22 2Z" fill="${isPrimary ? "#0A0A0A" : "white"}" stroke="#0A0A0A" stroke-width="1.5"/>
        <circle cx="22" cy="18" r="9" fill="${isPrimary ? "white" : "#0A0A0A"}" stroke="#0A0A0A" stroke-width="1.2"/>
        <text x="22" y="22" text-anchor="middle" font-family="'JetBrains Mono', monospace" font-size="8" font-weight="500" letter-spacing="0.5" fill="${isPrimary ? "#0A0A0A" : "white"}">${i + 1}</text>
      </svg>`;
      const icon = L.divIcon({ html: pinSvg, iconSize: [w, h], iconAnchor: [w / 2, h - 2], className: "" });
      const marker = L.marker([s.lat, s.lng], { icon }).addTo(map);
      marker.bindPopup(`<strong>${s.name}</strong><br/>${s.address}<br/><em>${s.km < 1 ? (s.km * 1000).toFixed(0) + "m away" : s.km.toFixed(1) + " km away"}</em>`);
      if (isPrimary) marker.openPopup();
    });

    const points = [[userPos.lat, userPos.lng], ...results.slice(0, 5).map(s => [s.lat, s.lng])];
    map.fitBounds(points, { padding: [40, 40], maxZoom: 15 });

    return () => {
      if (mapInstance.current) { mapInstance.current.remove(); mapInstance.current = null; }
    };
  }, [open, status]);

  const fmtDist = (km) => km < 1 ? `${(km * 1000).toFixed(0)} m` : `${km.toFixed(1)} km`;

  return (
    <>
      <FinderButton onClick={handleOpen} />

      {open && (
        <div style={{
          position: "fixed", inset: 0, zIndex: 9000,
          background: "rgba(10,10,10,0.72)",
          display: "flex", alignItems: "center", justifyContent: "center",
          padding: "clamp(16px, 4vw, 40px)",
          backdropFilter: "blur(6px)",
        }} onClick={(e) => { if (e.target === e.currentTarget) handleClose(); }}>
          <div style={{
            background: "var(--paper)", color: "var(--ink)",
            width: "100%", maxWidth: 900,
            maxHeight: "90vh",
            display: "flex", flexDirection: "column",
            border: "1px solid var(--rule)",
            overflow: "hidden",
          }}>
            {/* Header */}
            <div style={{
              padding: "24px 32px",
              borderBottom: "1px solid var(--rule)",
              display: "flex", justifyContent: "space-between", alignItems: "center",
              flexShrink: 0,
            }}>
              <div>
                <div style={{ fontFamily: "var(--f-body)", fontSize: 10, letterSpacing: "0.24em", textTransform: "uppercase", color: "var(--ink-60)", marginBottom: 6 }}>
                  Emma Basic
                </div>
                <h2 style={{
                  fontFamily: "var(--f-display)", fontWeight: 400,
                  fontSize: "clamp(22px, 2.5vw, 32px)",
                  letterSpacing: "-0.025em", lineHeight: 1, margin: 0,
                  fontVariationSettings: '"opsz" 144, "SOFT" 30',
                }}>
                  Find your nearest shop.
                </h2>
              </div>
              <button onClick={handleClose} style={{
                width: 40, height: 40, border: "1px solid var(--rule)",
                background: "transparent", cursor: "pointer",
                display: "flex", alignItems: "center", justifyContent: "center",
                fontSize: 18, color: "var(--ink)", flexShrink: 0,
              }}>×</button>
            </div>

            {/* Body */}
            <div style={{ flex: 1, overflow: "auto", display: "flex", flexDirection: "column" }}>

              {/* Input screen */}
              {status === "input" && (
                <div style={{
                  flex: 1, display: "flex", flexDirection: "column",
                  alignItems: "center", justifyContent: "center",
                  padding: "clamp(40px, 6vw, 64px) clamp(24px, 5vw, 64px)",
                  gap: 0,
                }}>
                  {/* Use location — primary CTA */}
                  <UseLocationButton onClick={handleUseLocation} />

                  <div style={{
                    display: "flex", alignItems: "center", gap: 16,
                    width: "100%", maxWidth: 400, margin: "28px 0",
                  }}>
                    <div style={{ flex: 1, height: 1, background: "var(--rule)" }} />
                    <span style={{ fontFamily: "var(--f-body)", fontSize: 10, letterSpacing: "0.2em", textTransform: "uppercase", color: "var(--ink-60)" }}>or enter a postcode</span>
                    <div style={{ flex: 1, height: 1, background: "var(--rule)" }} />
                  </div>

                  {/* Postcode form */}
                  <form onSubmit={handlePostcodeSubmit} style={{
                    display: "flex", gap: 0, width: "100%", maxWidth: 400,
                    marginBottom: 8,
                  }}>
                    <input
                      type="text"
                      value={postcode}
                      onChange={(e) => { setPostcode(e.target.value); setPostcodeError(""); }}
                      placeholder="e.g. SE1 2BB"
                      maxLength={8}
                      style={{
                        flex: 1,
                        border: postcodeError ? "1px solid #c0392b" : "1px solid var(--rule)",
                        borderRight: "none",
                        padding: "14px 16px",
                        fontFamily: "var(--f-body)", fontSize: 14,
                        letterSpacing: "0.06em", textTransform: "uppercase",
                        color: "var(--ink)", background: "var(--paper)",
                        outline: "none",
                      }}
                      onFocus={e => e.target.style.borderColor = "var(--ink)"}
                      onBlur={e => e.target.style.borderColor = postcodeError ? "#c0392b" : "var(--rule)"}
                    />
                    <PostcodeSubmitButton />
                  </form>
                  {postcodeError ? (
                    <p style={{ fontFamily: "var(--f-body)", fontSize: 12, color: "#c0392b", margin: "0", letterSpacing: "0.04em", width: "100%", maxWidth: 400 }}>
                      {postcodeError}
                    </p>
                  ) : (
                    <p style={{ fontFamily: "var(--f-body)", fontSize: 12, color: "var(--ink-60)", margin: "0", letterSpacing: "0.04em", width: "100%", maxWidth: 400 }}>
                      UK postcodes only
                    </p>
                  )}
                </div>
              )}

              {/* Locating spinner */}
              {status === "locating" && (
                <div style={{
                  flex: 1, display: "flex", flexDirection: "column",
                  alignItems: "center", justifyContent: "center",
                  padding: 80, gap: 24,
                }}>
                  <LocatingSpinner />
                  <p style={{ fontFamily: "var(--f-body)", fontSize: 16, color: "var(--ink-60)", margin: 0, letterSpacing: "0.02em" }}>
                    Finding your location…
                  </p>
                </div>
              )}

              {/* Error */}
              {status === "error" && (
                <div style={{
                  flex: 1, display: "flex", flexDirection: "column",
                  alignItems: "center", justifyContent: "center",
                  padding: 80, gap: 20, textAlign: "center",
                }}>
                  <div style={{ fontFamily: "var(--f-display)", fontStyle: "italic", fontSize: 36, fontVariationSettings: '"opsz" 48, "SOFT" 60' }}>
                    Oh dear.
                  </div>
                  <p style={{ fontFamily: "var(--f-body)", fontSize: 15, color: "var(--ink-60)", margin: 0, maxWidth: 380, lineHeight: 1.7 }}>
                    {errorMsg}
                  </p>
                  <button onClick={() => setStatus("input")} style={{
                    marginTop: 8, border: "1px solid var(--rule)", background: "transparent",
                    cursor: "pointer", padding: "12px 24px",
                    fontFamily: "var(--f-body)", fontSize: 11, letterSpacing: "0.18em",
                    textTransform: "uppercase", color: "var(--ink)",
                  }}>
                    Try again
                  </button>
                </div>
              )}

              {/* Results */}
              {status === "ready" && (
                <div style={{ display: "flex", flexDirection: "column", flex: 1, overflow: "auto" }}>

                  {/* Nearest store — hero card */}
                  {(() => {
                    const s = results[0];
                    const mapsUrl = "https://www.google.com/maps/search/" + encodeURIComponent(s.name + " " + s.address);
                    return (
                      <div style={{ background: "var(--ink)", color: "var(--paper)", padding: "28px 32px 24px", flexShrink: 0 }}>
                        <div style={{ fontFamily: "var(--f-body)", fontSize: 9.5, letterSpacing: "0.26em", textTransform: "uppercase", color: "rgba(246,246,246,0.45)", marginBottom: 10 }}>
                          Nearest to you
                        </div>
                        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 16, flexWrap: "wrap" }}>
                          <div>
                            <div style={{
                              fontFamily: "var(--f-display)", fontWeight: 400,
                              fontSize: "clamp(26px, 3vw, 38px)", letterSpacing: "-0.025em", lineHeight: 1.05,
                              fontVariationSettings: '"opsz" 144, "SOFT" 30', marginBottom: 8,
                            }}>{s.name}</div>
                            <div style={{ fontFamily: "var(--f-body)", fontSize: 11, letterSpacing: "0.14em", textTransform: "uppercase", color: "rgba(246,246,246,0.55)", lineHeight: 1.6 }}>
                              {s.address}
                            </div>
                          </div>
                          <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-end", gap: 10, flexShrink: 0 }}>
                            <div style={{ fontFamily: "var(--f-display)", fontStyle: "italic", fontSize: "clamp(28px, 3vw, 40px)", letterSpacing: "-0.02em", fontVariationSettings: '"opsz" 48, "SOFT" 60', lineHeight: 1 }}>
                              {fmtDist(s.km)}
                            </div>
                            <a href={mapsUrl} target="_blank" rel="noopener noreferrer" style={{
                              display: "inline-flex", alignItems: "center", gap: 8,
                              padding: "10px 18px",
                              border: "1px solid rgba(246,246,246,0.35)",
                              color: "var(--paper)", textDecoration: "none",
                              fontFamily: "var(--f-body)", fontSize: 10, letterSpacing: "0.2em", textTransform: "uppercase",
                              transition: "border-color 160ms, background 160ms",
                            }}
                              onMouseEnter={e => { e.currentTarget.style.borderColor = "rgba(246,246,246,0.9)"; e.currentTarget.style.background = "rgba(246,246,246,0.08)"; }}
                              onMouseLeave={e => { e.currentTarget.style.borderColor = "rgba(246,246,246,0.35)"; e.currentTarget.style.background = "transparent"; }}
                            >
                              Get directions →
                            </a>
                          </div>
                        </div>
                      </div>
                    );
                  })()}

                  {/* Map */}
                  <div ref={mapRef} style={{ width: "100%", height: 260, flexShrink: 0, borderBottom: "1px solid var(--rule)" }} />

                  {/* Other nearby stores */}
                  <div style={{ padding: "0 0 16px" }}>
                    <div style={{
                      padding: "16px 32px 12px",
                      borderBottom: "1px solid var(--rule)",
                      fontFamily: "var(--f-body)", fontSize: 9.5, letterSpacing: "0.26em",
                      textTransform: "uppercase", color: "var(--ink-60)",
                    }}>
                      Also nearby
                    </div>
                    {results.slice(1, 6).map((s, i) => {
                      const mapsUrl = "https://www.google.com/maps/search/" + encodeURIComponent(s.name + " " + s.address);
                      return (
                        <a key={i} href={mapsUrl} target="_blank" rel="noopener noreferrer" style={{
                          display: "grid", gridTemplateColumns: "1fr auto",
                          alignItems: "center", gap: 16,
                          padding: "14px 32px",
                          borderBottom: i < 4 ? "1px solid var(--rule)" : "none",
                          textDecoration: "none", color: "inherit",
                          transition: "background 160ms",
                        }}
                          onMouseEnter={e => e.currentTarget.style.background = "rgba(10,10,10,0.03)"}
                          onMouseLeave={e => e.currentTarget.style.background = "transparent"}
                        >
                          <div>
                            <div style={{
                              fontFamily: "var(--f-display)", fontWeight: 400,
                              fontSize: "clamp(15px, 1.5vw, 18px)", letterSpacing: "-0.015em",
                              color: "var(--ink)", fontVariationSettings: '"opsz" 144, "SOFT" 20',
                              marginBottom: 2,
                            }}>{s.name}</div>
                            <div style={{ fontFamily: "var(--f-body)", fontSize: 10, letterSpacing: "0.16em", textTransform: "uppercase", color: "var(--ink-60)" }}>
                              {s.address}
                            </div>
                          </div>
                          <div style={{ fontFamily: "var(--f-body)", fontSize: 11, letterSpacing: "0.1em", color: "var(--ink-60)", whiteSpace: "nowrap" }}>
                            {fmtDist(s.km)} →
                          </div>
                        </a>
                      );
                    })}
                  </div>

                  {/* Search again */}
                  <div style={{ padding: "4px 32px 20px", borderTop: "1px solid var(--rule)", display: "flex", justifyContent: "center" }}>
                    <button onClick={() => { setStatus("input"); if (mapInstance.current) { mapInstance.current.remove(); mapInstance.current = null; } }} style={{
                      border: "none", background: "none", cursor: "pointer",
                      fontFamily: "var(--f-body)", fontSize: 11, letterSpacing: "0.18em",
                      textTransform: "uppercase", color: "var(--ink-60)",
                      textDecoration: "underline", padding: "12px 0",
                    }}>
                      Search a different postcode
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      <style>{`
        .eb-finder-body { display: flex; flex-direction: column; }
        .eb-finder-map-wrap { height: 340px; }
        @media (max-width: 600px) { .eb-finder-map-wrap { height: 220px; } }
        .eb-map-wrap .leaflet-control-attribution { display: none; }
      `}</style>
    </>
  );
}

function FinderButton({ onClick }) {
  const [hover, setHover] = React.useState(false);
  return (
    <div style={{ display: "flex", justifyContent: "center", padding: "clamp(40px, 6vh, 64px) var(--pad-x)" }}>
      <button
        onClick={onClick}
        onMouseEnter={() => setHover(true)}
        onMouseLeave={() => setHover(false)}
        style={{
          display: "inline-flex", alignItems: "center", gap: 14,
          padding: "18px 36px",
          border: "1px solid var(--ink)",
          background: hover ? "var(--ink)" : "transparent",
          color: hover ? "var(--paper)" : "var(--ink)",
          cursor: "pointer",
          transition: "background 180ms var(--ease-out), color 180ms var(--ease-out)",
          fontFamily: "var(--f-body)", fontSize: 11, letterSpacing: "0.22em",
          textTransform: "uppercase",
        }}
      >
        <svg width="14" height="14" viewBox="0 0 14 14" fill="none" xmlns="http://www.w3.org/2000/svg" style={{ flexShrink: 0 }}>
          <circle cx="7" cy="7" r="6" stroke="currentColor" strokeWidth="1.4"/>
          <circle cx="7" cy="7" r="2.2" fill="currentColor"/>
          <line x1="7" y1="0" x2="7" y2="3" stroke="currentColor" strokeWidth="1.4"/>
          <line x1="7" y1="11" x2="7" y2="14" stroke="currentColor" strokeWidth="1.4"/>
          <line x1="0" y1="7" x2="3" y2="7" stroke="currentColor" strokeWidth="1.4"/>
          <line x1="11" y1="7" x2="14" y2="7" stroke="currentColor" strokeWidth="1.4"/>
        </svg>
        Find your nearest shop
      </button>
    </div>
  );
}

function PostcodeSubmitButton() {
  const [hover, setHover] = React.useState(false);
  return (
    <button
      type="submit"
      onMouseEnter={() => setHover(true)}
      onMouseLeave={() => setHover(false)}
      style={{
        padding: "14px 20px",
        border: "1px solid var(--ink)",
        background: hover ? "var(--ink)" : "var(--paper)",
        color: hover ? "var(--paper)" : "var(--ink)",
        cursor: "pointer",
        fontFamily: "var(--f-body)", fontSize: 11, letterSpacing: "0.18em",
        textTransform: "uppercase", whiteSpace: "nowrap",
        transition: "background 160ms var(--ease-out), color 160ms var(--ease-out)",
        flexShrink: 0,
      }}
    >
      Search
    </button>
  );
}

function UseLocationButton({ onClick }) {
  const [hover, setHover] = React.useState(false);
  return (
    <button
      onClick={onClick}
      onMouseEnter={() => setHover(true)}
      onMouseLeave={() => setHover(false)}
      style={{
        display: "inline-flex", alignItems: "center", gap: 10,
        padding: "16px 28px",
        border: "1px solid var(--ink)",
        background: hover ? "rgba(10,10,10,0.85)" : "var(--ink)",
        color: "var(--paper)",
        cursor: "pointer",
        transition: "background 160ms var(--ease-out)",
        fontFamily: "var(--f-body)", fontSize: 11, letterSpacing: "0.18em",
        textTransform: "uppercase",
        width: "100%", maxWidth: 400, justifyContent: "center",
      }}
    >
      <svg width="14" height="14" viewBox="0 0 14 14" fill="none" xmlns="http://www.w3.org/2000/svg">
        <circle cx="7" cy="7" r="6" stroke="currentColor" strokeWidth="1.3"/>
        <circle cx="7" cy="7" r="2" fill="currentColor"/>
        <line x1="7" y1="0" x2="7" y2="2.5" stroke="currentColor" strokeWidth="1.3"/>
        <line x1="7" y1="11.5" x2="7" y2="14" stroke="currentColor" strokeWidth="1.3"/>
        <line x1="0" y1="7" x2="2.5" y2="7" stroke="currentColor" strokeWidth="1.3"/>
        <line x1="11.5" y1="7" x2="14" y2="7" stroke="currentColor" strokeWidth="1.3"/>
      </svg>
      Use my current location
    </button>
  );
}

function LocatingSpinner() {
  const [angle, setAngle] = React.useState(0);
  React.useEffect(() => {
    const id = setInterval(() => setAngle(a => (a + 6) % 360), 16);
    return () => clearInterval(id);
  }, []);
  return (
    <svg width="40" height="40" viewBox="0 0 40 40" fill="none" xmlns="http://www.w3.org/2000/svg"
      style={{ transform: `rotate(${angle}deg)` }}>
      <circle cx="20" cy="20" r="16" stroke="var(--rule)" strokeWidth="2"/>
      <path d="M20 4 A16 16 0 0 1 36 20" stroke="var(--ink)" strokeWidth="2" strokeLinecap="round"/>
    </svg>
  );
}

window.NearestShopFinder = NearestShopFinder;
