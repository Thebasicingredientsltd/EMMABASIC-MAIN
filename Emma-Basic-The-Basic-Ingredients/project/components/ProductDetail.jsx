/* ============================================================
   ProductDetail — individual product page component.
   ============================================================ */

function ProductDetail() {
  const id = new URLSearchParams(window.location.search).get("id");
  const product = window.CATALOG_FLAT ? window.CATALOG_FLAT.find(p => p.id === id) : null;

  if (!product) {
    return (
      <div style={{ padding: "200px var(--pad-x)", fontFamily: "var(--f-body)", fontSize: 12, letterSpacing: "0.22em", textTransform: "uppercase", color: "var(--ink-60)" }}>
        Product not found. <a href="Our Products.html" style={{ color: "var(--ink)", borderBottom: "1px solid var(--ink)", textDecoration: "none" }}>Back to products →</a>
      </div>
    );
  }

  return (
    <>
      <TopNav hasHero={false} />
      <main>
        <ProductHero product={product} />
        {product.heroImage && <ProductHeroImage product={product} />}
        {product.ingredients && <ProductInfo product={product} />}
        {product.sellingPoints && product.sellingPoints.length > 0 && <SellingPoints product={product} />}
        {product.education && <ProductEducation product={product} />}
        {product.extraImages && product.extraImages.length > 0 && <ProductExtraImages images={product.extraImages} gapBetween={!!product.extraImagesGap} />}
      </main>
      <SiteFooter />
    </>
  );
}

/* ── Product Hero ─────────────────────────────────────────── */
function ProductHero({ product }) {
  const images = product.images && product.images.length > 1 ? product.images : null;
  // Total slots = images + optional video at the end
  const hasVideo = !!product.video;
  const totalSlots = (images ? images.length : 1) + (hasVideo ? 1 : 0);
  const videoIndex = hasVideo ? totalSlots - 1 : -1;

  const isPhoto = product.displayMode === "photo";
  const [activeImg, setActiveImg] = React.useState(0);
  const [loaded, setLoaded] = React.useState(false);
  const isVideoActive = hasVideo && activeImg === videoIndex;
  const displayImg = isVideoActive ? null : (images ? images[activeImg] : product.image);
  const isFirstImg = activeImg === 0;
  const imgRotation = product.imageRotations ? (product.imageRotations[activeImg] || 0) : 0;
  const isBackOfPack = displayImg && displayImg.includes("back-of-pack");
  const bopScale = product.imageScales?.[activeImg] ?? (isBackOfPack ? 2 : 1);
  const bopOffX = product.imageOffsets?.[activeImg]?.x ?? 0;
  const bopOffY = product.imageOffsets?.[activeImg]?.y ?? 0;

  /* Click-to-zoom */
  const pedestalRef = React.useRef(null);
  const ZOOM_STEPS = [1, 1.8, 3]; // cycle: normal → 1.8× → 3×
  const [zoomLevel, setZoomLevel] = React.useState(0); // index into ZOOM_STEPS
  const [zoomOrigin, setZoomOrigin] = React.useState({ x: 50, y: 50 }); // percent

  /* Image display params for first image */
  const isPhotoFirst = isPhoto && isFirstImg;
  const imgScale = isFirstImg ? (isPhoto ? 1 : (product.pdpImageScale ?? 3)) : 1;
  const imgOffX  = isFirstImg && !isPhoto ? (product.imageOffset?.x ?? 0) : 0;
  const imgOffY  = isFirstImg && !isPhoto ? (product.imageOffset?.y ?? 0) : 0;

  /* Reset zoom when switching images */
  React.useEffect(() => { setZoomLevel(0); }, [activeImg]);

  function handlePedestalClick(e) {
    const rect = pedestalRef.current.getBoundingClientRect();
    // Click position as fraction of the pedestal (0–1)
    const cx = (e.clientX - rect.left) / rect.width;
    const cy = (e.clientY - rect.top)  / rect.height;

    const nextLevel = (zoomLevel + 1) % ZOOM_STEPS.length;

    if (nextLevel === 0) {
      // Resetting — origin doesn't matter
      setZoomLevel(0);
      return;
    }

    // When already zoomed, the click lands on a scaled+shifted image.
    // We need the origin in the *original* (pre-zoom) coordinate space so
    // that CSS transformOrigin places the zoom correctly.
    // Reverse the current transform: orig = origin + (click - origin) / currentZoom
    if (zoomLevel > 0) {
      const ox = zoomOrigin.x / 100;
      const oy = zoomOrigin.y / 100;
      const curZoom = ZOOM_STEPS[zoomLevel];
      const origX = ox + (cx - ox) / curZoom;
      const origY = oy + (cy - oy) / curZoom;
      setZoomOrigin({ x: origX * 100, y: origY * 100 });
    } else {
      setZoomOrigin({ x: cx * 100, y: cy * 100 });
    }

    setZoomLevel(nextLevel);
  }

  const activeZoom = ZOOM_STEPS[zoomLevel];
  const isZoomed = zoomLevel > 0;

  const [pedestalRect, setPedestalRect] = React.useState(null);
  React.useEffect(() => {
    if (!pedestalRef.current) return;
    const obs = new ResizeObserver(() => {
      setPedestalRect(pedestalRef.current.getBoundingClientRect());
    });
    obs.observe(pedestalRef.current);
    setPedestalRect(pedestalRef.current.getBoundingClientRect());
    return () => obs.disconnect();
  }, []);

  /* Base transform for first image only */
  const firstImgTransform = `translate(${imgOffX}px, ${imgOffY}px) scale(${imgScale})`;

  return (
    <section style={{
      background: "var(--paper)",
      padding: "160px var(--pad-x) clamp(80px, 12vh, 140px)",
    }}>
      <div className="eb-pdp-hero-grid" style={{
        maxWidth: "var(--maxw)", margin: "0 auto",
        display: "grid",
        gridTemplateColumns: "minmax(0, 58%) minmax(0, 42%)",
        gap: "clamp(48px, 8vw, 120px)",
        alignItems: "start",
      }}>

        {/* Image pedestal + optional gallery strip */}
        <div>
          <div
            ref={pedestalRef}
            onClick={isVideoActive ? undefined : handlePedestalClick}
            style={{
              aspectRatio: isPhoto ? (product.pdpAspect || "1/1") : "4/5",
              background: "var(--paper-shade)",
              border: "1px solid var(--rule)",
              boxShadow: "0 8px 64px rgba(10,10,10,0.08), 0 2px 12px rgba(10,10,10,0.04)",
              overflow: "hidden",
              display: "flex", alignItems: "center", justifyContent: "center",
              padding: isVideoActive ? 0 : (isPhotoFirst ? 0 : (isFirstImg && product.pdpPadding !== undefined ? product.pdpPadding : "10%")),
              position: "relative",
              cursor: isVideoActive ? "default" : (isZoomed ? (zoomLevel === ZOOM_STEPS.length - 1 ? "zoom-out" : "zoom-in") : "zoom-in"),
              userSelect: "none",
            }}
          >
            {isVideoActive ? (
              <video
                key="product-video"
                src={product.video}
                controls
                autoPlay
                style={{ width: "100%", height: "100%", objectFit: "contain", display: "block" }}
              />
            ) : (
              <>
                <img
                  key={displayImg}
                  src={displayImg}
                  alt={product.name}
                  onLoad={() => { setLoaded(true); setPedestalRect(pedestalRef.current?.getBoundingClientRect()); }}
                  style={{
                    width: "100%", height: "100%",
                    objectFit: "contain",
                    opacity: loaded ? 1 : 0,
                    transition: "opacity 500ms var(--ease-out), transform 400ms var(--ease-out)",
                    transform: [
                      isFirstImg ? firstImgTransform : "",
                      (bopScale !== 1 || bopOffX || bopOffY) ? `translate(${bopOffX}px, ${bopOffY}px) scale(${bopScale})` : "",
                      imgRotation ? `rotate(${imgRotation}deg)` : "",
                      isZoomed ? `scale(${activeZoom})` : "",
                    ].filter(Boolean).join(" "),
                    transformOrigin: isZoomed ? `${zoomOrigin.x}% ${zoomOrigin.y}%` : "center center",
                  }}
                />
                {/* Zoom hint */}
                <div style={{
                  position: "absolute", bottom: 10, right: 12,
                  fontFamily: "var(--f-body)", fontSize: 9, letterSpacing: "0.22em",
                  textTransform: "uppercase", color: "var(--ink-40)",
                  pointerEvents: "none",
                  transition: "opacity 300ms",
                }}>
                  {isZoomed ? (zoomLevel === ZOOM_STEPS.length - 1 ? "Click to reset" : "Click to zoom more") : "Click to zoom"}
                </div>
              </>
            )}
          </div>

          {/* Thumbnail strip */}
          {images && (
            <div style={{
              display: "flex", flexWrap: "wrap", gap: 10, marginTop: 14,
            }}>
              {images.map((src, i) => (
                <button
                  key={i}
                  onClick={() => { setLoaded(false); setActiveImg(i); }}
                  style={{
                    flex: "0 0 auto",
                    width: 72, height: 72,
                    padding: 0, border: "none", cursor: "pointer",
                    background: "var(--paper-shade)",
                    outline: activeImg === i ? "2px solid var(--ink)" : "1px solid var(--rule)",
                    outlineOffset: activeImg === i ? 2 : 0,
                    overflow: "hidden",
                    transition: "outline 160ms var(--ease-out)",
                  }}
                >
                  <img src={src} alt="" style={{ width: "100%", height: "100%", objectFit: "contain", padding: 6, transform: [`scale(${product.imageScales?.[i] ?? (src.includes("back-of-pack") ? 2 : 1)})`, product.imageRotations?.[i] ? `rotate(${product.imageRotations[i]}deg)` : ""].filter(Boolean).join(" ") }} />
                </button>
              ))}
              {hasVideo && (
                <button
                  key="video-thumb"
                  onClick={() => { setActiveImg(videoIndex); }}
                  style={{
                    flex: "0 0 auto",
                    width: 72, height: 72,
                    padding: 0, border: "none", cursor: "pointer",
                    background: "var(--ink)",
                    outline: activeImg === videoIndex ? "2px solid var(--ink)" : "1px solid var(--rule)",
                    outlineOffset: activeImg === videoIndex ? 2 : 0,
                    overflow: "hidden",
                    transition: "outline 160ms var(--ease-out)",
                    display: "flex", alignItems: "center", justifyContent: "center",
                  }}
                >
                  <span style={{ fontSize: 22, color: "var(--paper)", lineHeight: 1 }}>&#9654;</span>
                </button>
              )}
            </div>
          )}
        </div>

        {/* Sticky product info */}
        <div className="eb-pdp-sidebar" style={{ position: "sticky", top: 108 }}>
          <Reveal>
            <a href="Our Products.html" style={{
              fontFamily: "var(--f-body)", fontSize: 10.5, letterSpacing: "0.22em",
              textTransform: "uppercase", color: "var(--ink-60)",
              textDecoration: "none", display: "inline-flex", alignItems: "center", gap: 8,
              marginBottom: 36,
            }}>
              ← {product.categoryNumber} — {product.category}
            </a>
          </Reveal>

          <Reveal delay={80}>
            <h1 style={{
              fontFamily: "var(--f-display)", fontWeight: 200,
              fontSize: "clamp(24px, 2.8vw, 46px)",
              letterSpacing: "-0.022em", lineHeight: 1.0, margin: "0 0 12px",
            }}>
              {product.name}
            </h1>
          </Reveal>

          <Reveal delay={140}>
            <div style={{
              fontFamily: "var(--f-display)",
              fontSize: "clamp(16px, 1.4vw, 20px)", color: "var(--ink-60)",
              marginBottom: 28,
            }}>
              {product.japanese}
            </div>
          </Reveal>

          <Reveal delay={180}>
            <div style={{ borderTop: "1px solid var(--rule)", marginBottom: 28 }} />
          </Reveal>

          <Reveal delay={220}>
            <div style={{
              fontFamily: "var(--f-body)", fontSize: 10.5, letterSpacing: "0.22em",
              textTransform: "uppercase", color: "var(--ink-60)",
              marginBottom: 20,
            }}>
              {product.origin}
            </div>
          </Reveal>

          <Reveal delay={260}>
            <p style={{
              fontFamily: "var(--f-body)",
              fontSize: "clamp(17px, 1.5vw, 20px)", lineHeight: 1.5,
              color: "var(--ink-90)", margin: "0 0 32px", maxWidth: 480,
            }}>
              {product.tagline}
            </p>
          </Reveal>

          {product.availableSizes && (
            <Reveal delay={220}>
              <p style={{
                fontFamily: "var(--f-body)", fontSize: 11, letterSpacing: "0.18em",
                textTransform: "uppercase", color: "var(--ink-60)",
                margin: "-16px 0 28px",
              }}>
                {product.availableSizes}
              </p>
            </Reveal>
          )}

          <Reveal delay={300}>
            <div style={{ display: "flex", flexWrap: "wrap", gap: 6, marginBottom: 32 }}>
              {product.badges.map((b, i) => <PDPBadge key={i} label={b} />)}
            </div>
          </Reveal>

          {/* Amazon buy button */}
          {product.amazon && (
            <Reveal delay={400}>
              <a
                href={product.amazon}
                target="_blank"
                rel="noopener noreferrer"
                style={{
                  display: "inline-flex", alignItems: "center", gap: 10,
                  padding: "16px 28px",
                  background: "var(--ink)", color: "var(--paper)",
                  fontFamily: "var(--f-body)", fontSize: 12.5, letterSpacing: "0.14em",
                  textTransform: "uppercase", textDecoration: "none",
                  border: "1px solid var(--ink)",
                  transition: "background 180ms var(--ease-out), color 180ms var(--ease-out)",
                  width: "100%", justifyContent: "center",
                }}
                onMouseEnter={e => { e.currentTarget.style.background = "transparent"; e.currentTarget.style.color = "var(--ink)"; }}
                onMouseLeave={e => { e.currentTarget.style.background = "var(--ink)"; e.currentTarget.style.color = "var(--paper)"; }}
              >
                <span>Order Now</span>
                <span style={{ fontFamily: "var(--f-mono)", fontSize: 12 }}>→</span>
              </a>
            </Reveal>
          )}
        </div>
      </div>
    </section>
  );
}

/* ── Full-bleed hero image (e.g. matcha lifestyle) ────────── */
function ProductHeroImage({ product }) {
  return (
    <div style={{
      width: "100%",
      height: "clamp(480px, 60vw, 860px)",
      overflow: "hidden",
      position: "relative",
    }}>
      <img
        src={product.heroImage}
        alt=""
        style={{
          width: "100%", height: "100%",
          objectFit: "cover",
          objectPosition: "center 30%",
          display: "block",
        }}
      />
      <div style={{
        position: "absolute", inset: 0,
        background: "linear-gradient(180deg, rgba(10,10,10,0.08) 0%, rgba(10,10,10,0.32) 100%)",
      }} />
    </div>
  );
}

/* ── Selling Points ───────────────────────────────────────── */
function SellingPoints({ product }) {
  const extra = product.extraSellingPoints;
  const [open, setOpen] = React.useState(false);
  const [extraOpen, setExtraOpen] = React.useState(false);

  function PointsGrid({ points, startIndex }) {
    return (
      <div className="eb-selling-grid" style={{
        display: "grid",
        gridTemplateColumns: "repeat(2, 1fr)",
        gap: "clamp(20px, 3vw, 40px) clamp(32px, 5vw, 80px)",
        marginTop: 28,
      }}>
        {points.map((point, i) => (
          <div key={i} style={{ display: "flex", gap: 14, alignItems: "start" }}>
            <span style={{
              fontFamily: "var(--f-mono)", fontSize: 10, letterSpacing: "0.1em",
              color: "var(--ink-40)", marginTop: 3, flexShrink: 0,
            }}>
              {String((startIndex || 0) + i + 1).padStart(2, "0")}
            </span>
            <p style={{
              fontFamily: "var(--f-body)", fontSize: "clamp(17px, 1.5vw, 21px)", lineHeight: 1.7,
              color: "var(--ink-90)", margin: 0,
            }}>
              {point}
            </p>
          </div>
        ))}
      </div>
    );
  }

  const qa = product.qa && product.qa.length > 0 ? product.qa : null;

  return (
    <section style={{
      background: "var(--paper-shade)",
      borderTop: "2px solid var(--ink)",
    }}>
      <div style={{
        maxWidth: "var(--maxw)", margin: "0 auto",
        padding: "0 var(--pad-x)",
        display: "grid",
        gridTemplateColumns: qa ? "1fr 1fr" : "1fr",
        gap: "0 clamp(40px, 6vw, 100px)",
        alignItems: "start",
      }} className="eb-selling-qa-grid">

        {/* Left column — accordions */}
        <div>
        {/* Why it's worth it — accordion */}
        <div style={{ borderBottom: "1px solid var(--rule)" }}>
          <button
            onClick={() => setOpen(o => !o)}
            style={{
              width: "100%", display: "flex", justifyContent: "space-between",
              alignItems: "center", gap: 24,
              padding: "clamp(28px, 4vh, 44px) 0",
              background: "none", border: "none", cursor: "pointer", textAlign: "left",
            }}
          >
            <span style={{
              fontFamily: "var(--f-body)", fontSize: 14, letterSpacing: "0.22em",
              textTransform: "uppercase", color: "var(--ink)",
            }}>Why it's worth it</span>
            <span style={{
              fontFamily: "var(--f-mono)", fontSize: 18, color: "var(--ink-60)",
              flexShrink: 0, display: "inline-block",
              transform: open ? "rotate(45deg)" : "rotate(0deg)",
              transition: "transform 300ms var(--ease-out)",
            }}>+</span>
          </button>
          <div style={{
            overflow: "hidden",
            maxHeight: open ? "2000px" : "0",
            transition: "max-height 500ms var(--ease-out)",
          }}>
            <div style={{ paddingBottom: "clamp(40px, 6vh, 64px)" }}>
              <PointsGrid points={product.sellingPoints} startIndex={0} />
            </div>
          </div>
        </div>

        {/* Also worth knowing — accordion */}
        {extra && extra.length > 0 && (
          <div style={{ borderBottom: "1px solid var(--rule)" }}>
            <button
              onClick={() => setExtraOpen(o => !o)}
              style={{
                width: "100%", display: "flex", justifyContent: "space-between",
                alignItems: "center", gap: 24,
                padding: "clamp(28px, 4vh, 44px) 0",
                background: "none", border: "none", cursor: "pointer", textAlign: "left",
              }}
            >
              <span style={{
                fontFamily: "var(--f-body)", fontSize: 10.5, letterSpacing: "0.22em",
                textTransform: "uppercase", color: "var(--ink)",
              }}>Also worth knowing</span>
              <span style={{
                fontFamily: "var(--f-mono)", fontSize: 18, color: "var(--ink-60)",
                flexShrink: 0, display: "inline-block",
                transform: extraOpen ? "rotate(45deg)" : "rotate(0deg)",
                transition: "transform 300ms var(--ease-out)",
              }}>+</span>
            </button>
            <div style={{
              overflow: "hidden",
              maxHeight: extraOpen ? "2000px" : "0",
              transition: "max-height 500ms var(--ease-out)",
            }}>
              <div style={{ paddingBottom: "clamp(40px, 6vh, 64px)" }}>
                <PointsGrid points={extra} startIndex={0} />
              </div>
            </div>
          </div>
        )}
        </div>{/* end left column */}

        {/* Right column — Q&A */}
        {qa && (
          <div style={{ borderLeft: "1px solid var(--rule)", paddingLeft: "clamp(32px, 5vw, 64px)" }} className="eb-qa-col">
            <InlineQA qa={qa} />
          </div>
        )}

      </div>
    </section>
  );
}

/* ── Inline Q&A (used inside SellingPoints two-col layout) ── */
function InlineQA({ qa }) {
  const [open, setOpen] = React.useState(null);
  return (
    <div style={{ padding: "clamp(28px, 4vh, 44px) 0" }}>
      <span style={{
        fontFamily: "var(--f-body)", fontSize: 10.5, letterSpacing: "0.22em",
        textTransform: "uppercase", color: "var(--ink)",
        display: "block", marginBottom: "clamp(20px, 3vh, 32px)",
      }}>Questions & Answers</span>
      {qa.map((item, i) => (
        <div key={i} style={{ borderBottom: "1px solid var(--rule)" }}>
          <button
            onClick={() => setOpen(open === i ? null : i)}
            style={{
              width: "100%", display: "flex", justifyContent: "space-between",
              alignItems: "center", gap: 24,
              padding: "18px 0", background: "none", border: "none",
              cursor: "pointer", textAlign: "left",
            }}
          >
            <span style={{
              fontFamily: "var(--f-body)", fontWeight: 500,
              fontSize: "clamp(16px, 1.3vw, 18px)", color: "var(--ink)",
              lineHeight: 1.4,
            }}>
              {item.q}
            </span>
            <span style={{
              fontFamily: "var(--f-mono)", fontSize: 16,
              color: "var(--ink-60)", flexShrink: 0,
              transform: open === i ? "rotate(45deg)" : "rotate(0deg)",
              transition: "transform 300ms var(--ease-out)",
              display: "inline-block",
            }}>+</span>
          </button>
          <div style={{
            overflow: "hidden",
            maxHeight: open === i ? 400 : 0,
            transition: "max-height 400ms var(--ease-out)",
          }}>
            <p style={{
              fontFamily: "var(--f-display)", fontStyle: "italic",
              fontSize: "clamp(16px, 1.3vw, 18px)", lineHeight: 1.65,
              color: "var(--ink-90)", margin: "0 0 20px",
            }}>
              {item.a}
            </p>
          </div>
        </div>
      ))}
    </div>
  );
}

/* ── Product Info: Ingredients + Allergens ────────────────── */
function ProductInfo({ product }) {
  if (!product.ingredients) return null;
  return (
    <section style={{
      background: "var(--paper)",
      borderTop: "1px solid var(--rule)",
    }}>
      <div style={{
        maxWidth: "var(--maxw)", margin: "0 auto",
        padding: "clamp(72px, 10vh, 120px) var(--pad-x)",
        display: "grid",
        gridTemplateColumns: "1fr 1fr",
        gap: "0 clamp(48px, 8vw, 120px)",
        alignItems: "start",
      }} className="eb-prodinfo-grid">

        {/* Left — ingredients */}
        <div>
          <Reveal>
            <SectionLabel>Ingredients</SectionLabel>
          </Reveal>
          <Reveal delay={80}>
            <p style={{
              fontFamily: "var(--f-body)", fontStyle: "normal",
              fontSize: "clamp(17px, 1.5vw, 21px)", lineHeight: 1.7,
              color: "var(--ink-90)", margin: 0,
            }}>
              {product.ingredients}
            </p>
          </Reveal>
        </div>

        {/* Right — allergens + pairings as labelled rows */}
        <div style={{ display: "flex", flexDirection: "column", gap: 0 }}>
          {product.allergens && (
            <Reveal delay={120}>
              <div style={{
                borderTop: "1px solid var(--rule)",
                padding: "clamp(20px, 2.5vh, 28px) 0",
                display: "grid", gridTemplateColumns: "120px 1fr", gap: "0 24px", alignItems: "baseline",
              }}>
                <span style={{
                  fontFamily: "var(--f-body)", fontSize: 9.5, letterSpacing: "0.22em",
                  textTransform: "uppercase", color: "var(--ink)",
                }}>Allergens</span>
                <p style={{
                  fontFamily: "var(--f-body)", fontSize: "clamp(14px, 1.1vw, 16px)", lineHeight: 1.6,
                  color: "var(--ink-90)", margin: 0,
                }}>
                  {product.allergens}
                </p>
              </div>
            </Reveal>
          )}
          {product.warning && (
            <Reveal delay={150}>
              <div style={{
                borderTop: "1px solid var(--rule)",
                padding: "clamp(20px, 2.5vh, 28px) 0",
                display: "grid", gridTemplateColumns: "120px 1fr", gap: "0 24px", alignItems: "baseline",
              }}>
                <span style={{
                  fontFamily: "var(--f-body)", fontSize: 9.5, letterSpacing: "0.22em",
                  textTransform: "uppercase", color: "var(--ink)",
                }}>Advisory</span>
                <p style={{
                  fontFamily: "var(--f-body)", fontSize: "clamp(14px, 1.1vw, 16px)", lineHeight: 1.6,
                  color: "var(--ink)", margin: 0, fontWeight: 500,
                }}>
                  {product.warning}
                </p>
              </div>
            </Reveal>
          )}
          {product.pairings && product.pairings.length > 0 && (
            <Reveal delay={180}>
              <div style={{
                borderTop: "1px solid var(--rule)",
                padding: "clamp(20px, 2.5vh, 28px) 0",
                display: "grid", gridTemplateColumns: "120px 1fr", gap: "0 24px", alignItems: "baseline",
              }}>
                <span style={{
                  fontFamily: "var(--f-body)", fontSize: 9.5, letterSpacing: "0.22em",
                  textTransform: "uppercase", color: "var(--ink)",
                }}>Pairs with</span>
                <p style={{
                  fontFamily: "var(--f-body)", fontSize: "clamp(14px, 1.1vw, 16px)", lineHeight: 1.6,
                  color: "var(--ink)", margin: 0,
                }}>
                  {product.pairings.join(" · ")}
                </p>
              </div>
            </Reveal>
          )}
        </div>
      </div>
      <style>{`
        @media (max-width: 640px) {
          .eb-prodinfo-grid { grid-template-columns: 1fr !important; }
        }
      `}</style>
    </section>
  );
}

/* ── Extra Images (full-bleed lifestyle shots below education) */
function ProductExtraImages({ images, gapBetween }) {
  return (
    <div>
      {images.map((src, i) => (
        <ExtraImageRow key={i} src={src} gap={gapBetween && i > 0} />
      ))}
    </div>
  );
}

function ExtraImageRow({ src, gap }) {
  return (
    <div style={{ width: "100%", borderTop: gap ? "2px solid var(--paper, #F6F6F6)" : "none" }}>
      <img src={src} alt="" style={{ width: "100%", height: "auto", display: "block" }} />
    </div>
  );
}

/* ── Education Section ────────────────────────────────────── */
function ProductEducation({ product }) {
  const ed = product.education;
  return (
    <section style={{ background: "var(--ink)", color: "var(--paper)" }}>
      <div style={{
        maxWidth: 1200, margin: "0 auto",
        padding: "clamp(96px, 14vh, 160px) var(--pad-x)",
      }}>
        <Reveal>
          <div style={{
            fontFamily: "var(--f-body)", fontSize: 10.5, letterSpacing: "0.22em",
            textTransform: "uppercase", color: "rgba(246,246,246,0.5)",
            marginBottom: 32,
          }}>
            Know Your Ingredients
          </div>
        </Reveal>
        <Reveal delay={100}>
          <h2 style={{
            fontFamily: "var(--f-display)", fontWeight: 400,
            fontSize: "clamp(36px, 5vw, 68px)",
            letterSpacing: "-0.022em", lineHeight: 1.05,
            color: "var(--paper)", margin: "0 0 clamp(40px, 7vh, 72px)",
            maxWidth: 900,
          }}>
            {ed.title}
          </h2>
        </Reveal>
        <Reveal delay={200}>
          <div className="eb-education-grid" style={{
            display: "grid",
            gridTemplateColumns: "repeat(2, 1fr)",
            gap: "clamp(32px, 5vw, 80px)",
          }}>
            {ed.body.map((para, i) => (
              <p key={i} style={{
                fontFamily: "var(--f-display)", fontStyle: "italic",
                fontSize: "clamp(16px, 1.4vw, 19px)", lineHeight: 1.7,
                color: "rgba(246,246,246,0.85)", margin: 0,
              }}>
                {para}
              </p>
            ))}
          </div>
        </Reveal>
      </div>
    </section>
  );
}

/* ── Q&A Section ──────────────────────────────────────────── */
function ProductQA({ product }) {
  const [open, setOpen] = React.useState(null);
  return (
    <section style={{
      background: "var(--paper)",
      borderTop: "1px solid var(--rule)",
    }}>
      <div style={{
        maxWidth: 900, margin: "0 auto",
        padding: "clamp(72px, 10vh, 120px) var(--pad-x)",
      }}>
        <Reveal>
          <SectionLabel>Questions & Answers</SectionLabel>
        </Reveal>
        <div style={{ marginTop: 36 }}>
          {product.qa.map((item, i) => (
            <Reveal key={i} delay={i * 60}>
              <div style={{ borderBottom: "1px solid var(--rule)" }}>
                <button
                  onClick={() => setOpen(open === i ? null : i)}
                  style={{
                    width: "100%", display: "flex", justifyContent: "space-between",
                    alignItems: "center", gap: 24,
                    padding: "22px 0", background: "none", border: "none",
                    cursor: "pointer", textAlign: "left",
                  }}
                >
                  <span style={{
                    fontFamily: "var(--f-body)", fontWeight: 500,
                    fontSize: "clamp(17px, 1.4vw, 19px)", color: "var(--ink)",
                    lineHeight: 1.4,
                  }}>
                    {item.q}
                  </span>
                  <span style={{
                    fontFamily: "var(--f-mono)", fontSize: 16,
                    color: "var(--ink-60)", flexShrink: 0,
                    transform: open === i ? "rotate(45deg)" : "rotate(0deg)",
                    transition: "transform 300ms var(--ease-out)",
                    display: "inline-block",
                  }}>
                    +
                  </span>
                </button>
                <div style={{
                  overflow: "hidden",
                  maxHeight: open === i ? 400 : 0,
                  transition: "max-height 400ms var(--ease-out)",
                }}>
                  <p style={{
                    fontFamily: "var(--f-display)", fontStyle: "italic",
                    fontSize: "clamp(17px, 1.4vw, 19px)", lineHeight: 1.65,
                    color: "var(--ink-90)", margin: "0 0 24px",
                    maxWidth: 720,
                  }}>
                    {item.a}
                  </p>
                </div>
              </div>
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  );
}

/* ── Shared small components ──────────────────────────────── */
function SectionLabel({ children }) {
  return (
    <div style={{
      fontFamily: "var(--f-body)", fontSize: 10.5, letterSpacing: "0.22em",
      textTransform: "uppercase", color: "var(--ink)",
      borderBottom: "1px solid var(--ink)",
      paddingBottom: 14, marginBottom: 28,
      display: "inline-block",
    }}>
      {children}
    </div>
  );
}

function PDPBadge({ label }) {
  const isGreatTaste = /great taste/i.test(label);
  return (
    <span style={{
      fontFamily: "var(--f-body)", fontSize: 9.5, letterSpacing: "0.22em",
      padding: "5px 9px",
      border: "1px solid var(--ink)",
      background: isGreatTaste ? "var(--ink)" : "transparent",
      color: isGreatTaste ? "var(--paper-bright)" : "var(--ink)",
      textTransform: "uppercase", whiteSpace: "nowrap",
    }}>
      {label}
    </span>
  );
}

/* Responsive styles injected once */
const _pdpStyle = document.createElement("style");
_pdpStyle.textContent = `
  @media (max-width: 768px) {
    .eb-pdp-hero-grid { grid-template-columns: 1fr !important; }
    .eb-pdp-sidebar { position: static !important; }
    .eb-selling-grid { grid-template-columns: 1fr !important; }
    .eb-info-grid { grid-template-columns: 1fr !important; }
    .eb-education-grid { grid-template-columns: 1fr !important; }
    .eb-selling-qa-grid { grid-template-columns: 1fr !important; }
    .eb-qa-col { border-left: none !important; padding-left: 0 !important; border-top: 1px solid var(--rule); }
  }
  @media (max-width: 480px) {
    .eb-selling-grid { grid-template-columns: 1fr !important; }
  }
`;
document.head.appendChild(_pdpStyle);

window.ProductDetail = ProductDetail;
