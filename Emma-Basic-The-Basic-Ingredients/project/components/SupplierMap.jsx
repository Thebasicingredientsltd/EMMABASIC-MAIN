/* ============================================================
   StockistDirectory — Clean numbered list + detail panel.
   No SVG map. Premium editorial layout.
   ============================================================ */

const STOCKISTS = [
  {
    id: "london",
    name: "London",
    region: "England",
    count: "12 locations",
    stores: [
      { name: "Selfridges", address: "400 Oxford St, London W1A 1AB" },
      { name: "Harrods", address: "87–135 Brompton Rd, London SW1X 7XL" },
      { name: "Wholefoods", address: "120 King's Rd, London SW3 4TR" },
      { name: "Corner Shop 180", address: "7 Arundel St, London WC2R 3DA" },
      { name: "Trude's Grocery", address: "10 The Pavement, London SW4 0HY" },
      { name: "Bayley & Sage", address: "33–34 Marylebone High Street W1U 4QD" },
      { name: "Jones of Brockley", address: "354 Brockley Rd, London SE4 2BY" },
      { name: "Life of Fish", address: "50 Abbeville Rd, London SW4 9NF" },
      { name: "Oseyo", address: "Centre Court Shopping Centre, Wimbledon SW19 8YE" },
      { name: "H Mart", address: "Unit 1, Leigh Close, New Malden KT3 3NW" },
      { name: "Blukoo", address: "Unit 10, Kingsbury Trading Est, Barningham Way, Kingsbury, London NW9 8AU" },
      { name: "Toast Rack", address: "314 Trinity Rd, London SW18 3RG" },
    ],
  },
  {
    id: "manchester",
    name: "Manchester",
    region: "England",
    count: "2 locations",
    stores: [
      { name: "Selfridges", address: "60 The Trafford Centre, Stretford M17 8DA" },
      { name: "General Store", address: "9 Owen Street, Deansgate Square M15 4YB" },
    ],
  },
  {
    id: "newcastle",
    name: "Newcastle",
    region: "England",
    count: "1 location",
    stores: [
      { name: "Block & Bottle", address: "188 Heaton Road, Newcastle upon Tyne NE6 5HP" },
    ],
  },
  {
    id: "scotland",
    name: "Scotland",
    region: "Scotland",
    count: "2 locations",
    stores: [
      { name: "C. Sinclair", address: "182 High Street, Burntisland KY3 9AP" },
      { name: "Quince & Cook", address: "Perth, Scotland" },
    ],
  },
  {
    id: "westmidlands",
    name: "West Midlands",
    region: "England",
    count: "2 locations",
    stores: [
      { name: "Chefslocker HQ", address: "22 Parade Centre, St. Mary's Place, Shrewsbury SY1 1DL" },
      { name: "Shop Kaizen", address: "22 Parade Centre, St. Mary's Place, Shrewsbury SY1 1DL" },
    ],
  },
  {
    id: "suffolk",
    name: "Suffolk",
    region: "England",
    count: "1 location",
    stores: [
      { name: "Frankie's Studio", address: "14 High Street, Hadleigh IP7 5AP" },
    ],
  },
  {
    id: "dorset",
    name: "Dorset",
    region: "England",
    count: "1 location",
    stores: [
      { name: "The Kitchen Table", address: "1a Bell Street, Shaftesbury SP7 8AR" },
    ],
  },
  {
    id: "eastsussex",
    name: "East Sussex",
    region: "England",
    count: "2 locations",
    stores: [
      { name: "Best Health Food Shop", address: "Uckfield, East Sussex" },
      { name: "Best Health Food Shop", address: "Shoreham-by-Sea, West Sussex" },
    ],
  },
  {
    id: "hampshire",
    name: "Hampshire",
    region: "England",
    count: "1 location",
    stores: [
      { name: "Hampshire Pantry", address: "Badger Farm Road, Winchester SO23 9RZ" },
    ],
  },
  {
    id: "rotterdam",
    name: "Rotterdam",
    region: "Netherlands",
    count: "European base",
    stores: [
      { name: "The Basic Ingredients B.V.", address: "Westplein 12–14, 3016BM Rotterdam" },
    ],
  },
];

function SupplierMap() {
  const [active, setActive] = React.useState("london");
  const activeStockist = STOCKISTS.find(s => s.id === active);
  const detailRef = React.useRef(null);

  const handleActivate = (id) => {
    setActive(id);
    if (window.innerWidth <= 768 && detailRef.current) {
      setTimeout(() => {
        detailRef.current.scrollIntoView({ behavior: "smooth", block: "start" });
      }, 50);
    }
  };

  return (
    <section style={{
      padding: "clamp(80px, 12vh, 160px) var(--pad-x)",
      background: "var(--paper)",
      color: "var(--ink)",
    }}>
      <div style={{ maxWidth: "var(--maxw)", margin: "0 auto" }}>

        {/* Heading row */}
        <Reveal>
          <div style={{
            display: "grid", gridTemplateColumns: "1fr auto",
            alignItems: "end", gap: 32,
            marginBottom: "clamp(56px, 7vh, 96px)",
          }}>
            <h2 style={{
              fontFamily: "var(--f-display)", fontWeight: 400,
              fontSize: "clamp(44px, 6vw, 92px)",
              letterSpacing: "-0.03em", lineHeight: 0.92, margin: 0,
              fontVariationSettings: '"opsz" 144, "SOFT" 30',
            }}>
              <span style={{ whiteSpace: "nowrap" }}>Where to find us.</span><br/>
              <em style={{ fontStyle: "normal", fontFamily: "var(--f-body)", fontWeight: 400, letterSpacing: "-0.02em" }}>
                Stocked across the UK.
              </em>
            </h2>
            <div style={{ paddingBottom: 10, textAlign: "right" }}>
              <span style={{
                fontFamily: "var(--f-body)", fontSize: 10.5, letterSpacing: "0.22em",
                textTransform: "uppercase", color: "var(--ink-60)", display: "block",
              }}>
                {STOCKISTS.length} regions
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

        {/* Main layout: list left, detail right */}
        <div className="eb-supplier-layout" style={{
          display: "grid",
          gridTemplateColumns: "1fr 1fr",
          gap: 0,
          border: "1px solid var(--rule)",
        }}>

          {/* Left — numbered location list */}
          <div style={{ borderRight: "1px solid var(--rule)" }}>
            {STOCKISTS.map((s, i) => (
              <LocationRow
                key={s.id}
                s={s}
                index={i}
                active={active === s.id}
                onActivate={() => handleActivate(s.id)}
                isLast={i === STOCKISTS.length - 1}
              />
            ))}
          </div>

          {/* Right — detail panel */}
          <div ref={detailRef}><DetailPanel s={activeStockist} /></div>
        </div>
      </div>
    </section>
  );
}

function LocationRow({ s, index, active, onActivate, isLast }) {
  const [hover, setHover] = React.useState(false);
  const highlighted = active || hover;

  return (
    <div
      onMouseEnter={() => { setHover(true); onActivate(); }}
      onMouseLeave={() => setHover(false)}
      onClick={onActivate}
      style={{
        display: "grid",
        gridTemplateColumns: "56px 1fr auto",
        alignItems: "center",
        gap: 0,
        padding: "0 32px 0 0",
        borderBottom: isLast ? "none" : "1px solid var(--rule)",
        background: highlighted ? "var(--ink)" : "transparent",
        cursor: "pointer",
        transition: "background 200ms var(--ease-out)",
        minHeight: 72,
      }}
    >
      {/* Number */}
      <div style={{
        padding: "0 0 0 28px",
        fontFamily: "var(--f-body)", fontSize: 10, letterSpacing: "0.22em",
        textTransform: "uppercase",
        color: highlighted ? "rgba(246,246,246,0.45)" : "rgba(10,10,10,0.35)",
        transition: "color 200ms var(--ease-out)",
        userSelect: "none",
      }}>
        {String(index + 1).padStart(2, "0")}
      </div>

      {/* City name */}
      <div style={{
        fontFamily: "var(--f-display)", fontWeight: 400,
        fontSize: "clamp(18px, 1.8vw, 26px)",
        letterSpacing: "-0.02em",
        fontVariationSettings: '"opsz" 144, "SOFT" 30',
        color: highlighted ? "var(--paper)" : "var(--ink)",
        transition: "color 200ms var(--ease-out)",
        userSelect: "none",
      }}>
        {s.name}
      </div>

      {/* Region + count */}
      <div style={{ textAlign: "right" }}>
        <div style={{
          fontFamily: "var(--f-body)", fontSize: 9.5, letterSpacing: "0.22em",
          textTransform: "uppercase",
          color: highlighted ? "rgba(246,246,246,0.5)" : "rgba(10,10,10,0.4)",
          transition: "color 200ms var(--ease-out)",
          userSelect: "none",
        }}>
          {s.region}
        </div>
        <div style={{
          fontFamily: "var(--f-body)", fontSize: 9.5, letterSpacing: "0.22em",
          textTransform: "uppercase",
          color: highlighted ? "rgba(246,246,246,0.7)" : "rgba(10,10,10,0.55)",
          transition: "color 200ms var(--ease-out)",
          marginTop: 3,
          userSelect: "none",
        }}>
          {s.count}
        </div>
      </div>
    </div>
  );
}

function DetailPanel({ s }) {
  if (!s) return null;
  return (
    <div style={{
      background: "var(--ink)",
      color: "var(--paper)",
      padding: "clamp(32px, 4vw, 56px)",
      display: "flex", flexDirection: "column",
      minHeight: 520,
    }}>
      {/* Header */}
      <div style={{
        display: "flex", justifyContent: "space-between", alignItems: "baseline",
        paddingBottom: 20, borderBottom: "1px solid rgba(246,246,246,0.15)",
        fontFamily: "var(--f-body)", fontSize: 9.5, letterSpacing: "0.22em",
        textTransform: "uppercase",
      }}>
        <span style={{ opacity: 0.5 }}>Stockists</span>
        <span style={{ opacity: 0.5 }}>{s.count}</span>
      </div>

      {/* City heading */}
      <div style={{ paddingTop: 28, marginBottom: 36 }}>
        <div style={{
          fontFamily: "var(--f-body)", fontSize: 10, letterSpacing: "0.22em",
          textTransform: "uppercase", color: "rgba(246,246,246,0.45)", marginBottom: 10,
        }}>
          {s.region} · United Kingdom
        </div>
        <h3 style={{
          fontFamily: "var(--f-display)", fontWeight: 400,
          fontSize: "clamp(32px, 3.2vw, 52px)",
          lineHeight: 1, letterSpacing: "-0.03em", margin: 0,
          fontVariationSettings: '"opsz" 144, "SOFT" 30',
        }}>
          {s.name}
        </h3>
      </div>

      {/* Store list */}
      <div style={{ flex: 1, display: "flex", flexDirection: "column", gap: 0 }}>
        {s.stores.map((store, i) => (
          <div key={i} style={{
            padding: "16px 0",
            borderTop: "1px solid rgba(246,246,246,0.1)",
            display: "grid",
            gridTemplateColumns: "1fr",
            gap: 4,
          }}>
            <span style={{
              fontFamily: "var(--f-body)", fontSize: 13.5,
              letterSpacing: "0",
              color: "rgba(246,246,246,0.95)",
            }}>
              {store.name}
            </span>
            <span style={{
              fontFamily: "var(--f-body)", fontSize: 10, letterSpacing: "0.22em",
              color: "rgba(246,246,246,0.4)",
              textTransform: "uppercase",
            }}>
              {store.address}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

/* Inject responsive styles */
const _supplierStyle = document.createElement("style");
_supplierStyle.textContent = `
  @media (max-width: 768px) {
    .eb-supplier-layout { grid-template-columns: 1fr !important; }
    .eb-supplier-layout > div:first-child { border-right: none !important; border-bottom: 1px solid var(--rule); }
  }
`;
document.head.appendChild(_supplierStyle);

window.SupplierMap = SupplierMap;
