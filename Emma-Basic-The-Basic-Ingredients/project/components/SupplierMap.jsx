/* ============================================================
   SupplierMap — "Where to find us. Stocked across the UK."
   A UK map with a pin per stockist, plus one search.
   Type a shop name to filter the list and pins. Type a UK
   postcode, or a town the geocoder can place, and the map
   moves to the nearest shops. Heading comes from
   window.EB_PLACES.directory and the pins from
   window.EB_PLACES.shops. A shop with highlight: true uses
   a larger accent pin. Needs Leaflet (loaded in Places.html).
   ============================================================ */

const SM_TILE_BASE = "https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Light_Gray_Base/MapServer/tile/{z}/{y}/{x}";
const SM_TILE_LABELS = "https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Light_Gray_Reference/MapServer/tile/{z}/{y}/{x}";
const SM_UK_BOUNDS = [[49.9, -8.2], [58.7, 1.8]];
const SM_NEAR_LIMIT = 5;

function cmsCopy(prop, cmsVal, fallback) {
  if (prop !== undefined && prop !== null) return prop;
  if (cmsVal !== undefined) return cmsVal;
  return fallback;
}

function smHasPin(s) {
  return typeof s.lat === "number" && typeof s.lng === "number";
}

function smHighlighted(s) {
  return !!(s && s.highlight === true);
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

function smHaversineKm(lat1, lng1, lat2, lng2) {
  const R = 6371;
  const dLat = (lat2 - lat1) * Math.PI / 180;
  const dLng = (lng2 - lng1) * Math.PI / 180;
  const a = Math.sin(dLat / 2) ** 2 +
    Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) * Math.sin(dLng / 2) ** 2;
  return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
}

function smFmtKm(km) {
  if (km < 1) return Math.round(km * 1000) + " m";
  return (Math.round(km * 10) / 10).toFixed(1) + " km";
}

function smCompactPostcode(raw) {
  return String(raw || "").trim().toUpperCase().replace(/\s+/g, "");
}

function smPostcodeKind(raw) {
  const compact = smCompactPostcode(raw);
  if (/^[A-Z]{1,2}\d[A-Z\d]?\d[A-Z]{2}$/.test(compact)) return "full";
  if (/^[A-Z]{1,2}\d[A-Z\d]?$/.test(compact)) return "outcode";
  return "";
}

function smPartialPostcode(raw) {
  const compact = smCompactPostcode(raw);
  if (!compact || smPostcodeKind(raw)) return false;
  return /^[A-Z]{1,2}\d[A-Z0-9]*$/.test(compact) && compact.length < 7;
}

async function smGeocodePostcode(raw, kind) {
  const compact = smCompactPostcode(raw);
  const url = kind === "full"
    ? "https://api.postcodes.io/postcodes/" + encodeURIComponent(compact)
    : "https://api.postcodes.io/outcodes/" + encodeURIComponent(compact);
  const res = await fetch(url);
  const data = await res.json();
  const result = data && data.result;
  if (data && data.status === 200 && result && typeof result.latitude === "number" && typeof result.longitude === "number") {
    return {
      lat: result.latitude,
      lng: result.longitude,
      label: result.postcode || result.outcode || compact,
    };
  }
  return null;
}

async function smGeocodePlace(raw) {
  const q = String(raw || "").trim();
  const res = await fetch("https://api.postcodes.io/places?q=" + encodeURIComponent(q) + "&limit=10");
  const data = await res.json();
  const places = (data && data.result) || [];
  const norm = q.toLowerCase();
  const hit = places.find(p => {
    const name = String(p.name_1 || "").toLowerCase();
    return name === norm || name.indexOf(norm) === 0 || norm.indexOf(name) === 0;
  });
  if (!hit || typeof hit.latitude !== "number" || typeof hit.longitude !== "number") return null;
  return { lat: hit.latitude, lng: hit.longitude, label: hit.name_1 || q };
}

function smNearest(pinned, origin, limit) {
  return pinned
    .map(s => ({ ...s, km: smHaversineKm(origin.lat, origin.lng, s.lat, s.lng) }))
    .sort((a, b) => a.km - b.km)
    .slice(0, limit);
}

function smPinIcon(highlighted) {
  const size = highlighted ? 22 : 18;
  return L.divIcon({
    html: "<span></span>",
    className: "eb-sm-pin" + (highlighted ? " is-highlight" : ""),
    iconSize: [size, size],
    iconAnchor: [size / 2, size / 2],
    popupAnchor: [0, -10],
  });
}

function smPopupNode(s, km) {
  const root = document.createElement("div");
  root.className = "eb-sm-popup" + (smHighlighted(s) ? " is-highlight" : "");
  const add = (tag, cls, text) => {
    const el = document.createElement(tag);
    el.className = cls;
    if (text) el.textContent = text;
    root.appendChild(el);
    return el;
  };
  if (s.city) add("div", "eb-sm-popup-city", s.city);
  add("div", "eb-sm-popup-name", s.name);
  if (typeof km === "number") add("div", "eb-sm-popup-dist", smFmtKm(km) + " away");
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
  const [origin, setOrigin] = React.useState(null);
  const [lookup, setLookup] = React.useState("idle");
  const mapEl = React.useRef(null);
  const wrapEl = React.useRef(null);
  const mapRef = React.useRef(null);
  const markersRef = React.useRef({});
  const hintTimer = React.useRef(null);

  const pinned = shops.filter(smHasPin);
  const q = query.trim();
  const postcodeKind = smPostcodeKind(q);
  const partialPostcode = smPartialPostcode(q);
  const textHits = shops.filter(s => smMatches(s, q));
  const seekingPlace = !postcodeKind && !partialPostcode && q.length >= 3 && textHits.length === 0;
  const originForQuery = origin && origin.q === q ? origin : null;
  const useNear = !!(originForQuery && (postcodeKind || textHits.length === 0));
  const nearest = useNear ? smNearest(pinned, originForQuery, SM_NEAR_LIMIT) : null;

  let mode = "all";
  if (!q) mode = "all";
  else if (useNear) mode = "near";
  else if ((postcodeKind || seekingPlace) && !originForQuery && lookup !== "miss") mode = "looking";
  else mode = "text";

  const visible = mode === "near" ? nearest : mode === "text" ? textHits : mode === "looking" ? [] : shops;

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
      const highlighted = smHighlighted(s);
      const marker = L.marker([s.lat, s.lng], {
        icon: smPinIcon(highlighted),
        title: s.name,
        alt: s.name,
        riseOnHover: true,
        zIndexOffset: highlighted ? 500 : 0,
      }).addTo(map);
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

  React.useEffect(() => {
    const text = query.trim();
    if (!text) {
      setOrigin(null);
      setLookup("idle");
      return undefined;
    }
    const kind = smPostcodeKind(text);
    const hits = shops.filter(s => smMatches(s, text));
    const partial = smPartialPostcode(text);
    const seekPlace = !kind && !partial && text.length >= 3 && hits.length === 0;
    if (!kind && !seekPlace) {
      setOrigin(null);
      setLookup("idle");
      return undefined;
    }
    let cancelled = false;
    setOrigin(null);
    setLookup("looking");
    const timer = window.setTimeout(async () => {
      try {
        const place = kind ? await smGeocodePostcode(text, kind) : await smGeocodePlace(text);
        if (cancelled) return;
        if (place) {
          setOrigin({ lat: place.lat, lng: place.lng, label: place.label, q: text });
          setLookup("idle");
        } else {
          setOrigin(null);
          setLookup("miss");
        }
      } catch (err) {
        if (cancelled) return;
        setOrigin(null);
        setLookup("miss");
      }
    }, 420);
    return () => {
      cancelled = true;
      window.clearTimeout(timer);
    };
  }, [query, shops]);

  React.useEffect(() => {
    const map = mapRef.current;
    if (!map || mode === "looking") return;
    const shown = mode === "all" ? pinned : (visible || []).filter(smHasPin);
    const shownIds = {};
    shown.forEach((s, i) => { shownIds[s._id] = { km: s.km, rank: i }; });
    const hits = [];
    pinned.forEach(s => {
      const marker = markersRef.current[s._id];
      if (!marker) return;
      const info = shownIds[s._id];
      const match = !!info;
      if (match && !map.hasLayer(marker)) marker.addTo(map);
      if (!match && map.hasLayer(marker)) {
        if (marker.isPopupOpen && marker.isPopupOpen()) marker.closePopup();
        map.removeLayer(marker);
      }
      if (match) hits.push([s.lat, s.lng]);
      if (marker.getPopup()) marker.setPopupContent(smPopupNode(s, info && info.km));
      const el = marker.getElement && marker.getElement();
      if (el) {
        el.classList.toggle("is-highlight", smHighlighted(s));
        el.classList.toggle("is-near", mode === "near" && match);
        el.classList.toggle("is-nearest", mode === "near" && match && info.rank === 0);
      }
    });
    if (!hits.length) return;
    const padding = mode === "all" ? [36, 36] : [48, 48];
    const maxZoom = mode === "all" ? 9 : 13;
    map.fitBounds(L.latLngBounds(hits), { padding: padding, maxZoom: maxZoom });
  }, [query, origin, lookup]);

  React.useEffect(() => {
    Object.keys(markersRef.current).forEach(id => {
      const el = markersRef.current[id].getElement && markersRef.current[id].getElement();
      if (el) el.classList.toggle("is-active", String(activeId) === id);
    });
  }, [activeId]);

  React.useEffect(() => {
    if (activeId == null || mode === "looking") return;
    if (!visible.some(s => s._id === activeId)) setActiveId(null);
  }, [query, origin, lookup]);

  const focusShop = (s) => {
    const map = mapRef.current;
    const marker = markersRef.current[s._id];
    if (!map || !marker) return;
    if (!map.hasLayer(marker)) marker.addTo(map);
    map.flyTo([s.lat, s.lng], Math.max(map.getZoom(), 14), { duration: 0.6 });
    map.once("moveend", () => marker.openPopup());
    if (isNarrow && wrapEl.current) wrapEl.current.scrollIntoView({ behavior: "smooth", block: "center" });
  };

  const listLimit = isNarrow && !showAll && !q ? 6 : visible.length;
  const listed = visible.slice(0, listLimit);
  let countText = shops.length + (shops.length === 1 ? " shop" : " shops");
  if (mode === "looking") countText = "Looking up…";
  else if (mode === "near") countText = nearest.length + " nearest to " + origin.label;
  else if (q) countText = visible.length + " of " + shops.length + " shops";

  let emptyText = "";
  if (mode === "looking") emptyText = "Looking up that place…";
  else if (q && !visible.length && partialPostcode) emptyText = "Keep typing the postcode.";
  else if (q && !visible.length && lookup === "miss" && postcodeKind) emptyText = "We couldn't find that postcode. Check it and try again.";
  else if (q && !visible.length) emptyText = "No shops match “" + q + "”. Try a shop name, town or postcode.";

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
                placeholder="Search by shop, town or postcode"
                autoComplete="off"
              />
              <div className="eb-sm-count" aria-live="polite">
                {countText}
              </div>
            </div>
            <ul className="eb-sm-items">
              {listed.map(s => (
                <li key={s._id}>
                  <button
                    type="button"
                    className={"eb-sm-item" + (activeId === s._id ? " is-active" : "") + (smHighlighted(s) ? " is-highlight" : "")}
                    onClick={() => focusShop(s)}
                    disabled={!smHasPin(s)}
                  >
                    <span className="eb-sm-item-name">
                      {s.name}
                      {smHighlighted(s) ? <span className="eb-sm-highlight-tag">Highlighted</span> : null}
                    </span>
                    <span className="eb-sm-item-city">{s.km != null ? smFmtKm(s.km) : s.city}</span>
                    <span className="eb-sm-item-address">{smAddressLine(s)}</span>
                  </button>
                </li>
              ))}
              {emptyText ? (
                <li className="eb-sm-empty">{emptyText}</li>
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
        .eb-sm-item.is-highlight .eb-sm-item-name { color: #8A6A2F; }
        .eb-sm-highlight-tag {
          display: block; margin-top: 4px; font-family: var(--f-mono); font-size: 9px;
          letter-spacing: 0.18em; text-transform: uppercase; color: #8A6A2F;
          font-variation-settings: normal;
        }
        .eb-sm-item.is-active.is-highlight .eb-sm-item-name,
        .eb-sm-item.is-active .eb-sm-highlight-tag { color: #E4C56A; }
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
        .eb-sm-pin.is-highlight span {
          width: 18px; height: 18px; margin: 2px; background: #C4A15A;
          box-shadow: 0 0 0 1.5px #0A0A0A, 0 2px 8px rgba(0,0,0,0.35);
        }
        .eb-sm-pin:hover span, .eb-sm-pin.is-active span, .eb-sm-pin.is-nearest span { transform: scale(1.35); }
        .eb-sm-pin.is-active span { background: #fff; border-color: #0A0A0A; }
        .eb-sm-pin.is-highlight.is-active span,
        .eb-sm-pin.is-highlight.is-nearest span,
        .eb-sm-pin.is-highlight:hover span {
          background: #C4A15A; border-color: #fff; transform: scale(1.2);
        }
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
        .eb-sm-popup.is-highlight .eb-sm-popup-name { color: #8A6A2F; }
        .eb-sm-popup-dist {
          font-family: var(--f-mono); font-size: 10px; letter-spacing: 0.14em; text-transform: uppercase;
          color: rgba(10,10,10,0.55); margin: -2px 0 8px;
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
