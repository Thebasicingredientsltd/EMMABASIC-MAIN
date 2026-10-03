/* ============================================================
   SupplierMap — "Where to find us. Stocked across the UK."
   A UK map with a pin per stockist, plus a searchable list.
   Heading comes from window.EB_PLACES.directory and the pins from
   window.EB_PLACES.shops (CRM → Where to find our products).
   Needs Leaflet (loaded in Places.html).
   ============================================================ */

const SM_TILE_BASE = "https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Light_Gray_Base/MapServer/tile/{z}/{y}/{x}";
const SM_TILE_LABELS = "https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Light_Gray_Reference/MapServer/tile/{z}/{y}/{x}";
const SM_UK_BOUNDS = [[49.9, -8.2], [58.7, 1.8]];

function cmsCopy(prop, cmsVal, fallback) {
  if (prop !== undefined && prop !== null) return prop;
  if (cmsVal !== undefined) return cmsVal;
  return fallback;
}

function smHasPin(s) {
  return typeof s.lat === "number" && typeof s.lng === "number";
}

function smSafeUrl(url) {
  const u = String(url || "").trim();
  if (!u) return "";
  if (/^https?:\/\//i.test(u)) return u;
  if (/^[\w-]+(\.[\w-]+)+/.test(u)) return "https://" + u;
  return "";
}

function smDirectionsUrl(s) {
  return "https://www.google.com/maps/search/?api=1&query=" +
    encodeURIComponent([s.name, s.address, s.postcode].filter(Boolean).join(", "));
}

function smAddressLine(s) {
  const address = s.address || "";
  if (s.postcode && address.toUpperCase().indexOf(String(s.postcode).toUpperCase()) === -1) {
    return address ? address + " " + s.postcode : s.postcode;
  }
  return address || s.city || "";
}

function smPopupNode(s) {
  const root = document.createElement("div");
  root.className = "eb-sm-popup";
  const add = (tag, cls, text) => {
    const el = document.createElement(tag);
    el.className = cls;
    if (text) el.textContent = text;
    root.appendChild(el);
    return el;
  };
  if (s.city) add("div", "eb-sm-popup-city", s.city);
  add("div", "eb-sm-popup-name", s.name);
  const address = smAddressLine(s);
  if (address) add("div", "eb-sm-popup-address", address);
  if (s.phone) {
    const tel = add("a", "eb-sm-popup-phone", s.phone);
    tel.href = "tel:" + String(s.phone).replace(/[^\d+]/g, "");
  }
  const links = add("div", "eb-sm-popup-links");
  const site = smSafeUrl(s.url);
  if (site) {
    const a = document.createElement("a");
    a.href = site; a.target = "_blank"; a.rel = "noopener noreferrer";
    a.textContent = "Visit website →";
    links.appendChild(a);
  }
  const dir = document.createElement("a");
  dir.href = smDirectionsUrl(s); dir.target = "_blank"; dir.rel = "noopener noreferrer";
  dir.textContent = "Directions →";
  links.appendChild(dir);
  return root;
}

function smMatches(s, q) {
  if (!q) return true;
  const hay = [s.name, s.city, s.address, s.postcode, s.region].filter(Boolean).join(" ").toLowerCase();
  return q.toLowerCase().split(/\s+/).filter(Boolean).every(word => hay.indexOf(word) !== -1);
}

function SupplierMap({ heading, headingItalic, hideHeading }) {
  const cms = (typeof window !== "undefined" && window.EB_PLACES && window.EB_PLACES.directory) || {};
  const fromCms = heading === undefined;
  const _hideHeading = hideHeading === true || (fromCms && cms.hideHeading === true);
  const _heading = cmsCopy(heading, cms.heading, "Where to find us.");
  const _headingItalic = cmsCopy(headingItalic, cms.headingItalic, "Stocked across the UK.");
  const showHeading = !_hideHeading && (_heading || _headingItalic);

  const shops = React.useMemo(() => {
    const list = (window.EB_PLACES && window.EB_PLACES.shops) || [];
    return list
      .filter(s => s && s.name)
      .map((s, i) => ({ ...s, _id: i }))
      .sort((a, b) => String(a.city || "").localeCompare(String(b.city || "")) || String(a.name).localeCompare(String(b.name)));
  }, []);

  const [query, setQuery] = React.useState("");
  const [activeId, setActiveId] = React.useState(null);
  const [showAll, setShowAll] = React.useState(false);
  const [hint, setHint] = React.useState("");
  const [isNarrow, setIsNarrow] = React.useState(() => window.matchMedia("(max-width: 768px)").matches);
  const mapEl = React.useRef(null);
  const wrapEl = React.useRef(null);
  const mapRef = React.useRef(null);
  const markersRef = React.useRef({});
  const hintTimer = React.useRef(null);

  const visible = shops.filter(s => smMatches(s, query.trim()));
  const pinned = shops.filter(smHasPin);

  React.useEffect(() => {
    const mq = window.matchMedia("(max-width: 768px)");
    const onChange = () => setIsNarrow(mq.matches);
    mq.addEventListener ? mq.addEventListener("change", onChange) : mq.addListener(onChange);
    return () => { mq.removeEventListener ? mq.removeEventListener("change", onChange) : mq.removeListener(onChange); };
  }, []);

  const flashHint = (text) => {
    setHint(text);
    window.clearTimeout(hintTimer.current);
    hintTimer.current = window.setTimeout(() => setHint(""), 1600);
  };

  React.useEffect(() => {
    if (!mapEl.current || mapRef.current || typeof L === "undefined") return;
    const touch = window.matchMedia("(pointer: coarse)").matches;
    const map = L.map(mapEl.current, {
      zoomControl: true,
      scrollWheelZoom: false,
      dragging: !touch,
      touchZoom: !touch,
      tap: true,
      attributionControl: true,
      minZoom: 4,
      maxZoom: 18,
    });
    map.attributionControl.setPrefix(false);
    mapRef.current = map;
    L.tileLayer(SM_TILE_BASE, { maxNativeZoom: 16, maxZoom: 18, attribution: "Tiles &copy; Esri" }).addTo(map);
    L.tileLayer(SM_TILE_LABELS, { maxNativeZoom: 16, maxZoom: 18 }).addTo(map);

    pinned.forEach(s => {
      const icon = L.divIcon({ html: "<span></span>", className: "eb-sm-pin", iconSize: [18, 18], iconAnchor: [9, 9], popupAnchor: [0, -8] });
      const marker = L.marker([s.lat, s.lng], { icon, title: s.name, alt: s.name, riseOnHover: true }).addTo(map);
      marker.bindPopup(() => smPopupNode(s), { maxWidth: 280, minWidth: 200, closeButton: true, autoPanPadding: [24, 24] });
      marker.on("popupopen", () => setActiveId(s._id));
      marker.on("popupclose", () => setActiveId(id => (id === s._id ? null : id)));
      markersRef.current[s._id] = marker;
    });

    if (pinned.length) {
      map.fitBounds(L.latLngBounds(pinned.map(s => [s.lat, s.lng])), { padding: [36, 36], maxZoom: 9 });
    } else {
      map.fitBounds(SM_UK_BOUNDS);
    }

    const container = map.getContainer();
    if (touch) container.style.touchAction = "pan-y";
    const onClick = () => { if (!touch) map.scrollWheelZoom.enable(); };
    const onLeave = () => map.scrollWheelZoom.disable();
    const onWheel = () => { if (!touch && !map.scrollWheelZoom.enabled()) flashHint("Click the map, then scroll to zoom"); };
    container.addEventListener("click", onClick);
    container.addEventListener("mouseleave", onLeave);
    container.addEventListener("wheel", onWheel, { passive: true });

    return () => {
      container.removeEventListener("click", onClick);
      container.removeEventListener("mouseleave", onLeave);
      container.removeEventListener("wheel", onWheel);
      window.clearTimeout(hintTimer.current);
      map.remove();
      mapRef.current = null;
      markersRef.current = {};
    };
  }, []);

  // Show only the pins that match the search, and frame them.
  React.useEffect(() => {
    const map = mapRef.current;
    if (!map) return;
    const q = query.trim();
    const hits = [];
    pinned.forEach(s => {
      const marker = markersRef.current[s._id];
      if (!marker) return;
      const match = smMatches(s, q);
      if (match && !map.hasLayer(marker)) marker.addTo(map);
      if (!match && map.hasLayer(marker)) map.removeLayer(marker);
      if (match) hits.push([s.lat, s.lng]);
    });
    if (q && hits.length) map.fitBounds(L.latLngBounds(hits), { padding: [48, 48], maxZoom: 13 });
    else if (!q && hits.length) map.fitBounds(L.latLngBounds(hits), { padding: [36, 36], maxZoom: 9 });
  }, [query]);

  React.useEffect(() => {
    Object.keys(markersRef.current).forEach(id => {
      const el = markersRef.current[id].getElement && markersRef.current[id].getElement();
      if (el) el.classList.toggle("is-active", String(activeId) === id);
    });
  }, [activeId]);

  const focusShop = (s) => {
    const map = mapRef.current;
    const marker = markersRef.current[s._id];
    if (!map || !marker) return;
    if (!map.hasLayer(marker)) marker.addTo(map);
    map.flyTo([s.lat, s.lng], Math.max(map.getZoom(), 14), { duration: 0.6 });
    map.once("moveend", () => marker.openPopup());
    if (isNarrow && wrapEl.current) wrapEl.current.scrollIntoView({ behavior: "smooth", block: "center" });
  };

  const listLimit = isNarrow && !showAll && !query.trim() ? 6 : visible.length;
  const listed = visible.slice(0, listLimit);

  return (
    <section id="stockist-map" style={{
      padding: "var(--section-y) var(--pad-x)",
      background: "var(--paper)",
      color: "var(--ink)",
    }}>
      <div style={{ maxWidth: "var(--maxw)", margin: "0 auto" }}>

        <Reveal>
          <div className="eb-sm-head" style={{
            display: "grid", gridTemplateColumns: "1fr auto",
            alignItems: "end", gap: 32,
            marginBottom: "clamp(40px, 6vh, 80px)",
          }}>
            {showHeading ? (
            <h2 style={{
              fontFamily: "var(--f-display)", fontWeight: 400,
              fontSize: "clamp(44px, 6vw, 92px)",
              letterSpacing: "-0.03em", lineHeight: 0.92, margin: 0,
              fontVariationSettings: '"opsz" 144, "SOFT" 30',
            }}>
              {_heading ? <span style={{ whiteSpace: "nowrap" }}>{_heading}</span> : null}
              {_heading && _headingItalic ? <br/> : null}
              {_headingItalic ? (
              <em style={{ fontStyle: "normal", fontFamily: "var(--f-body)", fontWeight: 400, letterSpacing: "-0.02em" }}>
                {_headingItalic}
              </em>
              ) : null}
            </h2>
            ) : <div />}
            <div className="eb-sm-head-count" style={{ paddingBottom: 10, textAlign: "right" }}>
              <span style={{
                fontFamily: "var(--f-body)", fontSize: 10.5, letterSpacing: "0.22em",
                textTransform: "uppercase", color: "var(--ink-60)", display: "block",
              }}>
                {shops.length} {shops.length === 1 ? "stockist" : "stockists"}
              </span>
              <span style={{
                fontFamily: "var(--f-display)", fontStyle: "italic",
                fontSize: "clamp(18px, 1.4vw, 24px)", color: "var(--ink)",
                fontVariationSettings: '"opsz" 48, "SOFT" 60',
                display: "block", marginTop: 8,
              }}>
                that we're aware of.
              </span>
            </div>
          </div>
        </Reveal>

        <div className="eb-sm-layout">
          <div className="eb-sm-mapwrap" ref={wrapEl}>
            <div ref={mapEl} className="eb-sm-map" role="region" aria-label="Map of shops that stock Emma Basic" />
            <div className={"eb-sm-hint" + (hint ? " is-on" : "")} aria-hidden="true">{hint}</div>
          </div>

          <div className="eb-sm-list">
            <div className="eb-sm-search">
              <label htmlFor="eb-sm-q" className="eb-sm-label">Search shops</label>
              <input
                id="eb-sm-q" type="search" value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Town, postcode or shop name"
                autoComplete="off"
              />
              <div className="eb-sm-count" aria-live="polite">
                {query.trim() ? `${visible.length} of ${shops.length} shops` : `${shops.length} shops`}
              </div>
            </div>
            <ul className="eb-sm-items">
              {listed.map(s => (
                <li key={s._id}>
                  <button
                    type="button"
                    className={"eb-sm-item" + (activeId === s._id ? " is-active" : "")}
                    onClick={() => focusShop(s)}
                    disabled={!smHasPin(s)}
                  >
                    <span className="eb-sm-item-name">{s.name}</span>
                    <span className="eb-sm-item-city">{s.city}</span>
                    <span className="eb-sm-item-address">{smAddressLine(s)}</span>
                  </button>
                </li>
              ))}
              {!visible.length ? (
                <li className="eb-sm-empty">No shops match “{query}”. Try a town or the first part of a postcode.</li>
              ) : null}
            </ul>
            {listLimit < visible.length ? (
              <button type="button" className="eb-sm-more" onClick={() => setShowAll(true)}>
                Show all {visible.length} shops
              </button>
            ) : null}
          </div>
        </div>
      </div>

      <style>{`
        .eb-sm-layout {
          display: grid; grid-template-columns: minmax(0, 1.75fr) minmax(280px, 1fr);
          border: 1px solid var(--rule); background: var(--paper-bright);
        }
        .eb-sm-mapwrap { position: relative; border-right: 1px solid var(--rule); }
        .eb-sm-map { width: 100%; height: clamp(440px, 64vh, 640px); background: #E9E9E6; }
        .eb-sm-list { display: flex; flex-direction: column; height: clamp(440px, 64vh, 640px); min-width: 0; }
        .eb-sm-search { padding: 20px 22px 14px; border-bottom: 1px solid var(--rule); }
        .eb-sm-label {
          display: block; font-family: var(--f-mono); font-size: 9.5px; letter-spacing: 0.22em;
          text-transform: uppercase; color: var(--ink-60); margin-bottom: 8px;
        }
        .eb-sm-search input {
          width: 100%; border: 1px solid var(--rule-strong); background: var(--paper);
          padding: 12px 14px; font-family: var(--f-body); font-size: 16px; color: var(--ink);
          border-radius: 0; outline: none; -webkit-appearance: none; appearance: none;
        }
        .eb-sm-search input:focus { border-color: var(--ink); }
        .eb-sm-count {
          margin-top: 10px; font-family: var(--f-mono); font-size: 9.5px; letter-spacing: 0.18em;
          text-transform: uppercase; color: var(--ink-60);
        }
        .eb-sm-items { list-style: none; margin: 0; padding: 0; overflow-y: auto; flex: 1; overscroll-behavior: contain; }
        .eb-sm-item {
          display: grid; grid-template-columns: 1fr auto; gap: 2px 12px; width: 100%;
          text-align: left; background: transparent; border: 0; border-bottom: 1px solid var(--rule);
          padding: 14px 22px; cursor: pointer; color: var(--ink);
          transition: background 160ms var(--ease-out);
        }
        .eb-sm-item:disabled { cursor: default; opacity: 0.6; }
        .eb-sm-item.is-active { background: var(--ink); color: var(--paper); }
        .eb-sm-item:focus-visible { outline: 2px solid var(--ink); outline-offset: -2px; }
        .eb-sm-item-name {
          font-family: var(--f-display); font-size: 19px; letter-spacing: -0.015em; line-height: 1.2;
          font-variation-settings: "opsz" 144, "SOFT" 20;
        }
        .eb-sm-item-city {
          font-family: var(--f-mono); font-size: 9.5px; letter-spacing: 0.18em; text-transform: uppercase;
          color: inherit; opacity: 0.55; align-self: center; white-space: nowrap;
        }
        .eb-sm-item-address {
          grid-column: 1 / -1; font-family: var(--f-body); font-size: 12px; letter-spacing: 0.02em;
          color: inherit; opacity: 0.6;
        }
        .eb-sm-empty { padding: 22px; font-family: var(--f-body); font-size: 14px; color: var(--ink-60); }
        .eb-sm-more {
          border: 0; border-top: 1px solid var(--rule); background: transparent; padding: 16px 22px;
          font-family: var(--f-mono); font-size: 10px; letter-spacing: 0.2em; text-transform: uppercase;
          cursor: pointer; color: var(--ink); text-align: left;
        }
        .eb-sm-hint {
          position: absolute; inset: 0; z-index: 900; display: flex; align-items: center; justify-content: center;
          background: rgba(10,10,10,0.42); color: #fff; font-family: var(--f-mono); font-size: 11px;
          letter-spacing: 0.16em; text-transform: uppercase; text-align: center; padding: 24px;
          opacity: 0; pointer-events: none; transition: opacity 200ms var(--ease-out);
        }
        .eb-sm-hint.is-on { opacity: 1; }
        .eb-sm-pin { background: none; border: 0; }
        .eb-sm-pin span {
          display: block; width: 14px; height: 14px; margin: 2px; border-radius: 50%;
          background: #0A0A0A; border: 2px solid #fff; box-shadow: 0 1px 6px rgba(0,0,0,0.35);
          transition: transform 160ms var(--ease-out);
        }
        .eb-sm-pin:hover span, .eb-sm-pin.is-active span { transform: scale(1.35); }
        .eb-sm-pin.is-active span { background: #fff; border-color: #0A0A0A; }
        .eb-sm-mapwrap .leaflet-container { font-family: var(--f-body); }
        .eb-sm-mapwrap .leaflet-control-zoom {
          border: 1px solid rgba(10,10,10,0.15) !important; box-shadow: 0 2px 12px rgba(0,0,0,0.12) !important; border-radius: 0 !important;
        }
        .eb-sm-mapwrap .leaflet-control-zoom a {
          font-family: var(--f-mono) !important; color: #0A0A0A !important; border-radius: 0 !important;
          border-color: rgba(10,10,10,0.15) !important;
        }
        .eb-sm-mapwrap .leaflet-control-attribution {
          font-family: var(--f-mono); font-size: 9px; letter-spacing: 0.06em;
          background: rgba(255,255,255,0.7); color: var(--ink-60);
        }
        .eb-sm-mapwrap .leaflet-popup-content-wrapper {
          border-radius: 0; box-shadow: 0 6px 28px rgba(0,0,0,0.18); border: 1px solid rgba(10,10,10,0.12);
        }
        .eb-sm-mapwrap .leaflet-popup-tip { box-shadow: none; border: 1px solid rgba(10,10,10,0.12); }
        .eb-sm-mapwrap .leaflet-popup-content { margin: 16px 18px; }
        .eb-sm-popup-city {
          font-family: var(--f-mono); font-size: 9px; letter-spacing: 0.22em; text-transform: uppercase;
          color: rgba(10,10,10,0.5); margin-bottom: 6px;
        }
        .eb-sm-popup-name {
          font-family: var(--f-display); font-size: 21px; line-height: 1.1; letter-spacing: -0.015em;
          color: #0A0A0A; margin-bottom: 6px;
        }
        .eb-sm-popup-address { font-family: var(--f-body); font-size: 12.5px; line-height: 1.5; color: rgba(10,10,10,0.7); }
        .eb-sm-popup-phone { display: block; margin-top: 4px; font-family: var(--f-body); font-size: 12.5px; color: #0A0A0A; }
        .eb-sm-popup-links { display: flex; gap: 16px; flex-wrap: wrap; margin-top: 12px; padding-top: 10px; border-top: 1px solid rgba(10,10,10,0.1); }
        .eb-sm-popup-links a {
          font-family: var(--f-mono); font-size: 10px; letter-spacing: 0.16em; text-transform: uppercase;
          color: #0A0A0A; text-decoration: none; border-bottom: 1px solid rgba(10,10,10,0.3); padding-bottom: 2px;
        }
        @media (pointer: coarse) {
          .eb-sm-mapwrap .leaflet-container { touch-action: pan-y !important; }
        }
        @media (max-width: 768px) {
          .eb-sm-head { grid-template-columns: 1fr !important; gap: 12px !important; }
          .eb-sm-head-count { text-align: left !important; padding-bottom: 0 !important; }
          .eb-sm-head h2 span { white-space: normal !important; }
          .eb-sm-layout { grid-template-columns: 1fr; }
          .eb-sm-mapwrap { border-right: 0; border-bottom: 1px solid var(--rule); }
          .eb-sm-map { height: min(68vh, 420px); }
          .eb-sm-list { height: auto; }
          .eb-sm-items { overflow: visible; }
          .eb-sm-search { padding: 16px; }
          .eb-sm-item { padding: 14px 16px; }
        }
      `}</style>
    </section>
  );
}

window.SupplierMap = SupplierMap;
