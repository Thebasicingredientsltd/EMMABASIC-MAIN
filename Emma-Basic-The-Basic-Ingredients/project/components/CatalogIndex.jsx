/* ============================================================
   CatalogIndex — the Our Products page.
   Category sections separated by hairline rules.
   Rich cards: name, japanese, origin, tagline, pairings, badges.
   ============================================================ */

const ATTRIBUTE_KEYWORDS = [
  "gluten free", "gluten-free", "vegan", "high fibre", "high fiber", "source of fibre",
  "high protein", "source of protein", "low salt", "low sugar", "reduced salt",
  "no msg", "no additives", "unpasteurised", "non-gmo", "organic",
  "batch tested", "physically pressed", "catering", "great taste",
];

function isAttributeSearch(q) {
  return ATTRIBUTE_KEYWORDS.some(kw => kw.includes(q) || q.includes(kw));
}

function matchesSearch(query, product) {
  if (!query) return true;
  const q = query.toLowerCase();
  if (isAttributeSearch(q)) {
    return [
      ...(product.badges || []),
      ...(product.sellingPoints || []),
    ].some(s => s && s.toLowerCase().includes(q));
  }
  return product.name.toLowerCase().includes(q);
}

function CatalogIndex() {
  const [active, setActive] = React.useState(CATALOG[0]?.id);
  const [query, setQuery] = React.useState("");
  const [focused, setFocused] = React.useState(false);
  const [canScrollLeft, setCanScrollLeft] = React.useState(false);
  const [canScrollRight, setCanScrollRight] = React.useState(false);
  const barRef = React.useRef(null);
  const [glutenFree, setGlutenFree] = React.useState(false);
  const [highFibre, setHighFibre] = React.useState(false);
  const [greatTaste, setGreatTaste] = React.useState(false);
  const [vegan, setVegan] = React.useState(false);
  const [highProtein, setHighProtein] = React.useState(false);
  const [cateringSize, setCateringSize] = React.useState(false);
  const [readyToSnack, setReadyToSnack] = React.useState(false);
  const [searchKey, setSearchKey] = React.useState(0);
  const prevQuery = React.useRef("");

  React.useEffect(() => {
    if (query !== prevQuery.current) {
      prevQuery.current = query;
      setSearchKey(k => k + 1);
    }
  }, [query]);

  React.useEffect(() => {
    if (query) return;
    const sections = CATALOG.map(c => document.getElementById(`cat-${c.id}`)).filter(Boolean);
    const io = new IntersectionObserver((entries) => {
      const visible = entries.filter(e => e.isIntersecting).sort((a, b) => a.boundingClientRect.top - b.boundingClientRect.top);
      if (visible[0]) setActive(visible[0].target.id.replace("cat-", ""));
    }, { rootMargin: "-30% 0px -60% 0px", threshold: 0 });
    sections.forEach(s => io.observe(s));
    return () => io.disconnect();
  }, [query]);

  function hasBadge(p, ...terms) {
    return (p.badges || []).some(b => terms.some(t => b.toLowerCase().includes(t)));
  }

  const anyFilter = query || glutenFree || highFibre || greatTaste || vegan || highProtein || cateringSize || readyToSnack;

  const filteredCatalog = anyFilter
    ? CATALOG.map(cat => ({
        ...cat,
        products: cat.products.filter(p =>
          matchesSearch(query, p) &&
          (!glutenFree || hasBadge(p, "gluten free", "gluten-free")) &&
          (!highFibre || hasBadge(p, "high fibre", "high fiber")) &&
          (!greatTaste || hasBadge(p, "great taste")) &&
          (!vegan || hasBadge(p, "vegan")) &&
          (!highProtein || hasBadge(p, "high protein")) &&
          (!cateringSize || hasBadge(p, "catering size", "catering")) &&
          (!readyToSnack || hasBadge(p, "ready to snack"))
        ),
      })).filter(cat => cat.products.length > 0)
    : CATALOG;

  const totalResults = anyFilter ? filteredCatalog.reduce((n, c) => n + c.products.length, 0) : null;

  return (
    <section style={{ background: "var(--paper)" }}>
      {/* Index + search bar */}
      <div className="eb-catalog-index-wrap" style={{
        position: "sticky", top: 72, zIndex: 20,
        background: "rgba(246,246,246,0.92)",
        backdropFilter: "saturate(140%) blur(10px)",
        borderTop: "1px solid var(--rule)",
        borderBottom: "1px solid var(--rule)",
      }}>
        <div className="eb-catalog-index-bar" style={{
          maxWidth: "var(--maxw)", margin: "0 auto",
          padding: "14px var(--pad-x)",
          display: "flex", gap: 28, alignItems: "center",
          overflowX: "auto", scrollbarWidth: "none",
          WebkitOverflowScrolling: "touch",
        }} ref={React.useCallback(el => {
          barRef.current = el;
          if (!el) return;
          const updateArrows = () => {
            setCanScrollLeft(el.scrollLeft > 4);
            setCanScrollRight(el.scrollLeft < el.scrollWidth - el.clientWidth - 4);
          };
          updateArrows();
          el.addEventListener("scroll", updateArrows, { passive: true });
          // Scroll bar horizontally on wheel before allowing page scroll
          const onWheel = e => {
            const atStart = el.scrollLeft === 0;
            const atEnd = el.scrollLeft >= el.scrollWidth - el.clientWidth - 1;
            if ((e.deltaY < 0 && !atStart) || (e.deltaY > 0 && !atEnd)) {
              e.preventDefault();
              el.scrollLeft += e.deltaY;
            }
          };
          el.addEventListener("wheel", onWheel, { passive: false });
          // Mouse drag
          let isDown = false, startX, scrollLeft;
          el.addEventListener("mousedown", e => { isDown = true; el.style.cursor = "grabbing"; startX = e.pageX - el.offsetLeft; scrollLeft = el.scrollLeft; });
          el.addEventListener("mouseleave", () => { isDown = false; el.style.cursor = ""; });
          el.addEventListener("mouseup", () => { isDown = false; el.style.cursor = ""; });
          el.addEventListener("mousemove", e => { if (!isDown) return; e.preventDefault(); el.scrollLeft = scrollLeft - (e.pageX - el.offsetLeft - startX); });
          // Re-check on resize
          const ro = new ResizeObserver(updateArrows);
          ro.observe(el);
        }, [])}>
          {/* Search input */}
          <div style={{ position: "relative", flexShrink: 0, display: "flex", alignItems: "center" }}>
            <span style={{
              fontFamily: "var(--f-body)", fontSize: 15, color: "var(--ink-60)",
              pointerEvents: "none", marginRight: 10,
            }}>⌕</span>
            <input
              type="text"
              placeholder="Search products…"
              value={query}
              onChange={e => setQuery(e.target.value)}
              onFocus={() => setFocused(true)}
              onBlur={() => setFocused(false)}
              style={{
                fontFamily: "var(--f-body)", fontSize: 14, letterSpacing: "0.10em",
                background: "transparent", border: "none", outline: "none",
                borderBottom: `1px solid ${focused || query ? "var(--ink)" : "var(--rule)"}`,
                paddingBottom: 3, width: 240,
                color: "var(--ink)",
                transition: "border-color 200ms var(--ease-out)",
              }}
            />
            {query && (
              <button onClick={() => setQuery("")} style={{
                background: "none", border: "none", cursor: "pointer",
                fontFamily: "var(--f-body)", fontSize: 16, color: "var(--ink-60)",
                padding: "0 0 0 10px", lineHeight: 1,
              }}>×</button>
            )}
          </div>

          <span style={{
            fontFamily: "var(--f-body)", fontSize: 10.5, letterSpacing: "0.22em",
            textTransform: "uppercase", color: "var(--ink-60)", whiteSpace: "nowrap", flexShrink: 0,
          }}>{query && !anyFilter ? `${totalResults} result${totalResults !== 1 ? "s" : ""}` : "Index —"}</span>

          {!query && CATALOG.map((c) => (
            <a key={c.id} href={`#cat-${c.id}`} style={{
              fontFamily: "var(--f-body)", fontSize: 11, letterSpacing: "0.22em",
              textTransform: "uppercase",
              color: active === c.id ? "var(--ink)" : "var(--ink-60)",
              textDecoration: "none",
              borderBottom: `1px solid ${active === c.id ? "var(--ink)" : "transparent"}`,
              paddingBottom: 2, whiteSpace: "nowrap",
              transition: "color 200ms var(--ease-out), border-color 200ms var(--ease-out)",
            }}>
              <span style={{ opacity: 0.55, marginRight: 8 }}>{c.number}</span>
              {c.name}
            </a>
          ))}
        </div>

        {/* Scroll arrows — sit just inside the maxw container, next to the categories */}
        <div style={{
          position: "absolute", top: 0, bottom: 0,
          left: "50%", transform: "translateX(-50%)",
          width: "min(100%, var(--maxw))",
          pointerEvents: "none",
          display: "flex", alignItems: "stretch",
        }}>
          {canScrollLeft && (
            <button onClick={() => barRef.current?.scrollBy({ left: -220, behavior: "smooth" })} style={{
              position: "absolute", left: 8, top: "50%", transform: "translateY(-50%)",
              width: 30, height: 30,
              border: "1px solid var(--ink)", borderRadius: 0,
              cursor: "pointer",
              background: "var(--paper)",
              display: "flex", alignItems: "center", justifyContent: "center",
              color: "var(--ink)", fontSize: 14,
              transition: "background 150ms, color 150ms",
              pointerEvents: "all",
              zIndex: 2,
              flexShrink: 0,
            }} onMouseEnter={e => { e.currentTarget.style.background = "var(--ink)"; e.currentTarget.style.color = "var(--paper)"; }}
               onMouseLeave={e => { e.currentTarget.style.background = "var(--paper)"; e.currentTarget.style.color = "var(--ink)"; }}>
              ←
            </button>
          )}
          {canScrollRight && (
            <button onClick={() => barRef.current?.scrollBy({ left: 220, behavior: "smooth" })} style={{
              position: "absolute", right: 8, top: "50%", transform: "translateY(-50%)",
              width: 30, height: 30,
              border: "1px solid var(--ink)", borderRadius: 0,
              cursor: "pointer",
              background: "var(--paper)",
              display: "flex", alignItems: "center", justifyContent: "center",
              color: "var(--ink)", fontSize: 14,
              transition: "background 150ms, color 150ms",
              pointerEvents: "all",
              zIndex: 2,
              flexShrink: 0,
            }} onMouseEnter={e => { e.currentTarget.style.background = "var(--ink)"; e.currentTarget.style.color = "var(--paper)"; }}
               onMouseLeave={e => { e.currentTarget.style.background = "var(--paper)"; e.currentTarget.style.color = "var(--ink)"; }}>
              →
            </button>
          )}
        </div>

        <style>{`
          .eb-catalog-index-bar::-webkit-scrollbar { display: none; }
          .eb-catalog-index-wrap { position: relative; }
        `}</style>
      </div>

      <style>{`
        @keyframes eb-search-reveal {
          from { opacity: 0; transform: translateY(12px); }
          to   { opacity: 1; transform: translateY(0); }
        }
        .eb-search-results { animation: eb-search-reveal 320ms var(--ease-out) both; }
      `}</style>

      {/* Filter bar */}
      <div style={{
        maxWidth: "var(--maxw)", margin: "0 auto",
        padding: "clamp(28px, 4vh, 40px) var(--pad-x) 0",
        display: "flex", alignItems: "center", gap: 12,
      }}>
        <span style={{
          fontFamily: "var(--f-body)", fontSize: 10.5, letterSpacing: "0.2em",
          textTransform: "uppercase", color: "var(--ink-60)",
        }}>Filter —</span>
        {[
          { label: "Gluten free", active: glutenFree, toggle: () => setGlutenFree(g => !g) },
          { label: "High fibre", active: highFibre, toggle: () => setHighFibre(h => !h) },
          { label: "High protein", active: highProtein, toggle: () => setHighProtein(h => !h) },
          { label: "Vegan", active: vegan, toggle: () => setVegan(v => !v) },
          { label: "Great Taste", active: greatTaste, toggle: () => setGreatTaste(g => !g) },
          { label: "Ready to snack", active: readyToSnack, toggle: () => setReadyToSnack(r => !r) },
          { label: "Catering size", active: cateringSize, toggle: () => setCateringSize(c => !c) },
        ].map(({ label, active, toggle }) => (
          <button
            key={label}
            onClick={toggle}
            style={{
              fontFamily: "var(--f-body)", fontSize: 10.5, letterSpacing: "0.16em",
              textTransform: "uppercase",
              padding: "6px 14px",
              border: `1px solid ${active ? "var(--ink)" : "var(--rule)"}`,
              background: active ? "var(--ink)" : "transparent",
              color: active ? "var(--paper)" : "var(--ink-60)",
              cursor: "pointer",
              transition: "background 180ms var(--ease-out), color 180ms var(--ease-out), border-color 180ms var(--ease-out)",
            }}
            onMouseEnter={e => { if (!active) { e.currentTarget.style.borderColor = "var(--ink)"; e.currentTarget.style.color = "var(--ink)"; }}}
            onMouseLeave={e => { if (!active) { e.currentTarget.style.borderColor = "var(--rule)"; e.currentTarget.style.color = "var(--ink-60)"; }}}
          >{label}</button>
        ))}
        {(glutenFree || highFibre || greatTaste || vegan || highProtein || cateringSize || readyToSnack) && (
          <span style={{
            fontFamily: "var(--f-body)", fontSize: 10.5, letterSpacing: "0.16em",
            textTransform: "uppercase", color: "var(--ink-60)",
          }}>{totalResults} product{totalResults !== 1 ? "s" : ""}</span>
        )}
      </div>

      <div key={searchKey} className={query ? "eb-search-results" : undefined}>
        {filteredCatalog.length === 0 ? (
          <div style={{ padding: "clamp(80px, 12vh, 140px) var(--pad-x)", maxWidth: "var(--maxw)", margin: "0 auto" }}>
            <p style={{ fontFamily: "var(--f-body)", fontSize: 11, letterSpacing: "0.22em", textTransform: "uppercase", color: "var(--ink-60)" }}>
              No products found for "{query}"
            </p>
          </div>
        ) : (
          filteredCatalog.map((cat, ci) => (
            <CategorySection key={cat.id} category={cat} index={ci} />
          ))
        )}
      </div>
    </section>
  );
}

function CategorySection({ category, index }) {
  return (
    <section id={`cat-${category.id}`} style={{
      padding: "clamp(90px, 12vh, 140px) var(--pad-x) clamp(80px, 10vh, 120px)",
      borderTop: index === 0 ? "none" : "1px solid var(--rule)",
    }}>
      <div style={{ maxWidth: "var(--maxw)", margin: "0 auto" }}>
        {/* Category header */}
        <Reveal>
          <div className="eb-catalog-header" style={{
            display: "grid",
            gridTemplateColumns: "auto 1fr 1fr",
            alignItems: "end",
            gap: "clamp(24px, 4vw, 56px)",
            marginBottom: "clamp(56px, 8vh, 96px)",
          }}>
            <span style={{
              fontFamily: "var(--f-body)", fontSize: 11, letterSpacing: "0.22em",
              textTransform: "uppercase", color: "var(--ink-60)",
              paddingBottom: 14,
            }}>
              {category.number}
            </span>

            <div>
              <div style={{
                fontFamily: "var(--f-display)", fontWeight: 400,
                fontSize: 18, color: "var(--ink-60)",
                marginBottom: 8,
                fontVariationSettings: '"opsz" 24',
              }}>
                {category.japanese}
              </div>
              <h2 style={{
                fontFamily: "var(--f-body)", fontWeight: 500,
                fontSize: "clamp(40px, 6vw, 80px)",
                letterSpacing: "-0.025em", lineHeight: 0.98, margin: 0,
              }}>
                {category.name}.
              </h2>
            </div>

            <p style={{
              fontFamily: "var(--f-display)", fontStyle: "italic",
              fontSize: "clamp(16px, 1.3vw, 19px)", lineHeight: 1.45,
              color: "var(--ink-90)",
              maxWidth: 520, margin: 0, paddingBottom: 14,
              fontVariationSettings: '"opsz" 24, "SOFT" 60',
            }}>
              {category.blurb}
            </p>
          </div>
        </Reveal>

        {/* Product grid — 4 across by default, fewer for very small sets */}
        <div className="eb-catalog-grid" style={{
          display: "grid",
          gridTemplateColumns: category.products.length === 1
            ? "minmax(0, 480px)"
            : "repeat(4, 1fr)",
          gap: "clamp(24px, 3vw, 48px) clamp(16px, 2vw, 32px)",
          alignItems: "start",
          justifyContent: category.products.length === 1 ? "start" : undefined,
        }}>
          {category.products.map((p, i) => (
            <ProductCard key={p.id} product={p} index={i} />
          ))}
        </div>

        {category.meta?.link && (
          <Reveal delay={200}>
            <div style={{ marginTop: "clamp(40px, 6vh, 80px)", display: "flex", justifyContent: "flex-end" }}>
              <a href={category.meta.link.href} style={{
                fontFamily: "var(--f-body)", fontSize: 11, letterSpacing: "0.22em",
                textTransform: "uppercase", color: "var(--ink)",
                textDecoration: "none", borderBottom: "1px solid var(--ink)",
                paddingBottom: 2,
              }}>
                {category.meta.link.label} →
              </a>
            </div>
          </Reveal>
        )}
      </div>
    </section>
  );
}

function ProductCard({ product, index }) {
  const [ref, visible] = useReveal(0.12);
  const [hover, setHover] = React.useState(false);
  const isMobile = window.innerWidth <= 768;
  const isPhoto = product.displayMode === "photo";
  const activeOffset = isPhoto
    ? null
    : (isMobile
      ? (product.mobileImageOffset ?? product.catalogImageOffset ?? product.imageOffset)
      : (product.catalogImageOffset ?? product.imageOffset));
  const activeScale = isPhoto
    ? 1
    : (isMobile
      ? (product.mobileImageScale ?? product.imageScale ?? 2)
      : (product.imageScale ?? 2));
  return (
    <a
      ref={ref}
      href={`product.html?id=${product.id}`}
      onMouseEnter={() => setHover(true)}
      onMouseLeave={() => setHover(false)}
      style={{
        display: "grid", gap: 20,
        textDecoration: "none", color: "inherit",
        cursor: "pointer",
        opacity: visible ? 1 : 0,
        transform: `translateY(${visible ? 0 : 24}px)`,
        transition: `opacity 900ms var(--ease-out) ${index * 80}ms, transform 900ms var(--ease-out) ${index * 80}ms`,
      }}
    >
      {/* Image pedestal — uniform 1:1 square across all cards */}
      <div style={{
        position: "relative",
        aspectRatio: "1 / 1",
        background: "var(--paper-shade)",
        overflow: "hidden",
        border: "1px solid var(--rule)",
        boxShadow: "0 4px 32px rgba(10,10,10,0.06), 0 1px 4px rgba(10,10,10,0.03)",
        display: "flex", alignItems: "center", justifyContent: "center",
      }}>
        {/* White rectangle behind the product image */}
        {!product.noWhiteBg && !isPhoto && (
          <div style={{
            position: "absolute",
            inset: "6%",
            background: "#ffffff",
            borderRadius: 4,
            boxShadow: "0 2px 12px rgba(10,10,10,0.06)",
          }} />
        )}
        <img
          src={product.image}
          alt={product.name}
          loading="lazy"
          style={{
            position: "absolute", inset: 0,
            width: "100%", height: "100%",
            objectFit: "contain",
            padding: isPhoto ? 0 : (product.noWhiteBg ? "clamp(12px, 4%, 28px)" : "4%"),
            transform: `translate(${activeOffset?.x ?? 0}px, ${activeOffset?.y ?? 0}px) scale(${hover ? activeScale * 1.04 : activeScale})`,
            transition: "transform 800ms var(--ease-out)",
            zIndex: 1,
          }}
        />

        {/* Hover CTA — bottom */}
        <div style={{
          position: "absolute", left: 0, right: 0, bottom: 0,
          padding: "20px 20px 18px",
          display: "flex", justifyContent: "space-between", alignItems: "center",
          background: "linear-gradient(180deg, transparent 0%, rgba(10,10,10,0.7) 100%)",
          color: "var(--paper)",
          opacity: hover ? 1 : 0,
          transform: `translateY(${hover ? 0 : 8}px)`,
          transition: "opacity 260ms var(--ease-out), transform 260ms var(--ease-out)",
        }}>
          <span style={{ fontFamily: "var(--f-body)", fontSize: 10.5, letterSpacing: "0.22em", textTransform: "uppercase" }}>
            Read the label
          </span>
          <span style={{ fontFamily: "var(--f-mono)", fontSize: 14 }}>→</span>
        </div>
      </div>

      {/* Meta — left-aligned, editorial */}
      <div style={{ display: "grid", gap: 12 }}>
        <div style={{
          display: "flex", justifyContent: "space-between", alignItems: "center", gap: 12,
          height: 24, overflow: "hidden",
        }}>
          <span style={{
            fontFamily: "var(--f-body)", fontWeight: 400, fontSize: 10, letterSpacing: "0.22em",
            textTransform: "uppercase", color: "var(--ink-60)",
            whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis",
            lineHeight: 1,
          }}>
            {product.origin}
          </span>
          <span style={{
            fontFamily: "var(--f-display)", fontSize: 13, color: "var(--ink-60)",
            fontStyle: "italic", whiteSpace: "nowrap", flexShrink: 0,
          }}>
            {product.japanese}
          </span>
        </div>

        <h3 style={{
          fontFamily: "var(--f-display)", fontWeight: 400,
          fontSize: "clamp(18px, 1.6vw, 24px)",
          letterSpacing: "-0.018em", margin: 0, lineHeight: 1.05,
          fontVariationSettings: '"opsz" 144, "SOFT" 30',
        }}>
          <span style={{
            backgroundImage: "linear-gradient(var(--ink), var(--ink))",
            backgroundRepeat: "no-repeat",
            backgroundSize: hover ? "100% 1px" : "0% 1px",
            backgroundPosition: "0 100%",
            paddingBottom: 2,
            transition: "background-size 420ms var(--ease-out)",
          }}>
            {product.name}
          </span>
        </h3>

        <p style={{
          fontFamily: "var(--f-body)",
          fontSize: 13, lineHeight: 1.45, margin: 0,
          color: "var(--ink-90)", maxWidth: 420,
        }}>
          {product.tagline}
        </p>

        {/* Badges */}
        <div style={{ display: "flex", flexWrap: "wrap", gap: 6, paddingTop: 4 }}>
          {product.badges.map((b, i) => (
            <Badge key={i} label={b} />
          ))}
        </div>
      </div>
    </a>
  );
}

function Badge({ label }) {
  const isGreatTaste = /great taste/i.test(label);
  return (
    <span style={{
      fontFamily: "var(--f-body)", fontSize: 9.5, letterSpacing: "0.22em",
      padding: "5px 9px",
      border: "1px solid var(--ink)",
      background: isGreatTaste ? "var(--ink)" : "transparent",
      color: isGreatTaste ? "var(--paper-bright)" : "var(--ink)",
      textTransform: "uppercase",
      whiteSpace: "nowrap",
    }}>
      {label}
    </span>
  );
}

const _catalogStyle = document.createElement("style");
_catalogStyle.textContent = `
  @media (max-width: 768px) {
    .eb-catalog-header { grid-template-columns: 1fr !important; }
    .eb-catalog-header > span:first-child { display: none; }
  }
  @media (max-width: 600px) {
    .eb-catalog-grid { grid-template-columns: repeat(2, 1fr) !important; }
  }
  @media (max-width: 480px) {
    .eb-catalog-grid { grid-template-columns: repeat(2, 1fr) !important; }
  }
`;
document.head.appendChild(_catalogStyle);

window.CatalogIndex = CatalogIndex;
