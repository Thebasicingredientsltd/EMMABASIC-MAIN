/* ============================================================
   PlacesGallery — photo gallery at the foot of the Find us page.
   Heading, photos and visibility are CMS-managed on
   window.EB_PLACES.gallery. Clicking a photo opens a lightbox.
   ============================================================ */

const PG_PHOTOS = [
  { image: "assets/places-gallery/tasting-stand.jpg",      caption: "Tasting — trade show" },
  { image: "assets/places-gallery/market-shelves.jpg",     caption: "Market stall — the range" },
  { image: "assets/places-gallery/stand-build.jpg",        caption: "Setting up — trade show" },
  { image: "assets/places-gallery/showroom-table.jpg",     caption: "Showroom — tasting table" },
  { image: "assets/places-gallery/festival-sampling.jpg",  caption: "Festival — sampling" },
  { image: "assets/places-gallery/trade-show-shelves.jpg", caption: "Trade show — shelves" },
  { image: "assets/places-gallery/sampling-counter.jpg",   caption: "Sampling counter" },
  { image: "assets/places-gallery/stockist-visit.jpg",     caption: "Stockist visit" },
];

function pgCopy(prop, cmsVal, fallback) {
  if (prop !== undefined && prop !== null) return prop;
  if (cmsVal !== undefined) return cmsVal;
  return fallback;
}

function PlacesGallery({ photos, heading, headingItalic, intro, hideHeading }) {
  const cms = (typeof window !== "undefined" && window.EB_PLACES && window.EB_PLACES.gallery) || {};
  const fromCms = heading === undefined;
  const [openIndex, setOpenIndex] = React.useState(-1);

  // An empty list in the CMS means the owner cleared the album, so the
  // built-in photos only stand in when the page loads without any gallery data.
  const cmsPhotos = Array.isArray(cms.photos) ? cms.photos : null;
  const list = (photos || cmsPhotos || PG_PHOTOS).filter(p => p && p.image);
  const _hideHeading = hideHeading === true || (fromCms && cms.hideHeading === true);
  const _heading = pgCopy(heading, cms.heading, "Out in the");
  const _headingItalic = pgCopy(headingItalic, cms.headingItalic, "wild.");
  const _intro = pgCopy(intro, cms.intro, "Markets, trade shows and shop floors — where our shelves and our jars actually meet people.");
  const showHeading = !_hideHeading && (_heading || _headingItalic);

  if (fromCms && cms.visible === false) return null;
  if (!list.length) return null;

  function cmsProps(field) {
    if (!fromCms) return {};
    return { "data-cms-key": "places", "data-cms-path": "gallery." + field };
  }

  return (
    <section style={{
      background: "var(--paper)",
      borderTop: "1px solid var(--rule)",
      padding: "var(--section-y) var(--pad-x)",
    }}>
      <div style={{ maxWidth: "var(--maxw)", margin: "0 auto" }}>
        {(showHeading || _intro) && (
          <div className="eb-pg-head" style={{
            display: "grid", gridTemplateColumns: "1fr 1fr",
            gap: "clamp(32px, 8vw, 120px)", alignItems: "end",
            marginBottom: "clamp(40px, 6vh, 64px)",
          }}>
            {showHeading ? (
              <Reveal>
                <h2 style={{
                  fontFamily: "var(--f-display)", fontWeight: 400,
                  fontSize: "clamp(40px, 5vw, 80px)",
                  letterSpacing: "-0.035em", lineHeight: 1.0, margin: 0,
                  fontVariationSettings: '"opsz" 144, "SOFT" 30',
                }}>
                  {_heading ? <span {...cmsProps("heading")}>{_heading}</span> : null}
                  {_heading && _headingItalic ? <br/> : null}
                  {_headingItalic ? (
                    <em {...cmsProps("headingItalic")} style={{ fontStyle: "normal", fontFamily: "var(--f-body)", fontWeight: 400, letterSpacing: "-0.02em" }}>
                      {_headingItalic}
                    </em>
                  ) : null}
                </h2>
              </Reveal>
            ) : <div />}
            {_intro ? (
              <Reveal delay={80}>
                <p {...cmsProps("intro")} style={{
                  fontFamily: "var(--f-body)", fontSize: "clamp(16px, 1.3vw, 18px)",
                  lineHeight: 1.72, margin: 0, color: "var(--ink-60)",
                  paddingBottom: 8,
                }}>{_intro}</p>
              </Reveal>
            ) : null}
          </div>
        )}

        <div className="eb-pg-grid" style={{
          columns: "3 300px", columnGap: "clamp(10px, 1.2vw, 16px)",
        }}>
          {list.map((photo, i) => (
            <PlacesGalleryThumb
              key={photo.image + i}
              photo={photo}
              index={i}
              onOpen={() => setOpenIndex(i)}
            />
          ))}
        </div>
      </div>

      <PlacesGalleryLightbox
        photos={list}
        index={openIndex}
        onClose={() => setOpenIndex(-1)}
        onStep={step => setOpenIndex((openIndex + step + list.length) % list.length)}
      />

      <style>{`
        @keyframes eb-pg-fade { from { opacity: 0; } to { opacity: 1; } }
        @media (max-width: 768px) {
          .eb-pg-head { grid-template-columns: 1fr !important; }
        }
        @media (max-width: 560px) {
          .eb-pg-grid { columns: 2 !important; }
        }
      `}</style>
    </section>
  );
}

function PlacesGalleryThumb({ photo, index, onOpen }) {
  const [ref, visible] = useReveal(0.05);
  const [hover, setHover] = React.useState(false);
  return (
    <button
      ref={ref}
      type="button"
      onClick={onOpen}
      onMouseEnter={() => setHover(true)}
      onMouseLeave={() => setHover(false)}
      aria-label={photo.caption ? "Open photo: " + photo.caption : "Open photo"}
      style={{
        breakInside: "avoid",
        display: "block", width: "100%", padding: 0,
        marginBottom: "clamp(10px, 1.2vw, 16px)",
        background: "transparent", border: 0, cursor: "zoom-in",
        textAlign: "left",
        opacity: visible ? 1 : 0,
        transform: `translateY(${visible ? 0 : 20}px)`,
        transition: `opacity 700ms var(--ease-out) ${(index % 3) * 60}ms, transform 700ms var(--ease-out) ${(index % 3) * 60}ms`,
      }}
    >
      <div style={{ position: "relative", overflow: "hidden" }}>
        <img
          src={photo.image}
          alt={photo.caption || ""}
          loading="lazy"
          decoding="async"
          style={{
            width: "100%", display: "block",
            transform: hover ? "scale(1.04)" : "scale(1)",
            transition: "transform 900ms var(--ease-out)",
          }}
        />
        {photo.caption ? (
          <span style={{
            position: "absolute", left: 0, right: 0, bottom: 0,
            padding: "28px 14px 12px",
            background: "linear-gradient(to top, rgba(10,10,10,0.55), rgba(10,10,10,0))",
            fontFamily: "var(--f-body)", fontSize: 10.5, letterSpacing: "0.18em",
            textTransform: "uppercase", color: "var(--paper)",
            opacity: hover ? 1 : 0,
            transition: "opacity var(--dur-hover) var(--ease-out)",
          }}>{photo.caption}</span>
        ) : null}
      </div>
    </button>
  );
}

function PlacesGalleryLightbox({ photos, index, onClose, onStep }) {
  const open = index >= 0 && index < photos.length;
  React.useEffect(() => {
    if (!open) return;
    const onKey = (e) => {
      if (e.key === "Escape") onClose();
      else if (e.key === "ArrowRight") onStep(1);
      else if (e.key === "ArrowLeft") onStep(-1);
    };
    window.addEventListener("keydown", onKey);
    document.body.style.overflow = "hidden";
    return () => {
      window.removeEventListener("keydown", onKey);
      document.body.style.overflow = "";
    };
  }, [open, onClose, onStep]);

  if (!open) return null;
  const photo = photos[index];
  const arrow = {
    background: "transparent", border: 0, cursor: "pointer",
    fontFamily: "var(--f-body)", fontSize: 24, lineHeight: 1,
    color: "var(--paper)", padding: "12px 16px",
  };

  return (
    <div
      role="dialog"
      aria-modal="true"
      onClick={onClose}
      style={{
        position: "fixed", inset: 0, zIndex: 80,
        background: "rgba(10,10,10,0.97)",
        display: "flex", flexDirection: "column",
        animation: "eb-pg-fade 240ms var(--ease-out)",
      }}
    >
      <div style={{
        display: "flex", justifyContent: "space-between", alignItems: "center",
        padding: "18px clamp(16px, 4vw, 40px)", flexShrink: 0,
      }}>
        <span style={{
          fontFamily: "var(--f-body)", fontSize: 10.5, letterSpacing: "0.22em",
          textTransform: "uppercase", color: "rgba(246,246,246,0.55)",
        }}>{String(index + 1).padStart(2, "0")} / {String(photos.length).padStart(2, "0")}</span>
        <button type="button" onClick={onClose} style={{
          ...arrow, fontSize: 11, letterSpacing: "0.22em", textTransform: "uppercase",
          display: "flex", alignItems: "center", gap: 10, padding: 0,
        }}>Close <span style={{ fontSize: 18 }}>×</span></button>
      </div>

      <div
        onClick={e => e.stopPropagation()}
        style={{
          flex: 1, minHeight: 0,
          display: "grid", gridTemplateColumns: "auto 1fr auto", alignItems: "center",
          gap: "clamp(4px, 2vw, 24px)", padding: "0 clamp(8px, 3vw, 32px)",
        }}
      >
        <button type="button" onClick={() => onStep(-1)} aria-label="Previous photo" style={arrow}>←</button>
        <figure style={{
          margin: 0, height: "100%", minHeight: 0,
          display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", gap: 16,
        }}>
          <img
            src={photo.image}
            alt={photo.caption || ""}
            style={{ maxWidth: "100%", maxHeight: "calc(100% - 40px)", objectFit: "contain" }}
          />
          {photo.caption ? (
            <figcaption style={{
              fontFamily: "var(--f-body)", fontSize: 10.5, letterSpacing: "0.22em",
              textTransform: "uppercase", color: "rgba(246,246,246,0.7)", textAlign: "center",
            }}>{photo.caption}</figcaption>
          ) : null}
        </figure>
        <button type="button" onClick={() => onStep(1)} aria-label="Next photo" style={arrow}>→</button>
      </div>

      <div style={{ height: "clamp(16px, 4vh, 40px)", flexShrink: 0 }} />
    </div>
  );
}

window.PlacesGallery = PlacesGallery;
