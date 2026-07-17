/* ============================================================
   TopNav — shared across pages. Always visible.
   Props:
     - hasHero: true on homepage (dark hero) → adapts text color.
                false on interior pages → always ink on paper.
   Dropdown: "Products Without E-Numbers" reveals a submenu (All Products).
   ============================================================ */
function TopNav({ hasHero = false }) {
  const [scrolled, setScrolled] = React.useState(false);
  const [openDropdown, setOpenDropdown] = React.useState(null);
  const [mobileOpen, setMobileOpen] = React.useState(false);
  React.useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 12);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);
  React.useEffect(() => {
    if (mobileOpen) document.body.style.overflow = "hidden";
    else document.body.style.overflow = "";
    return () => { document.body.style.overflow = ""; };
  }, [mobileOpen]);

  // On interior pages there's no dark hero, so always use ink-on-paper.
  const overHero = hasHero && !scrolled;
  const textColor = overHero ? "#F6F6F6" : "var(--ink)";
  const bg = overHero
    ? "linear-gradient(180deg, rgba(10,10,10,0.35) 0%, rgba(10,10,10,0) 100%)"
    : "rgba(246,246,246,0.92)";

  const leftLinks = [
    { label: "Products Without E-Numbers", href: "Our Products.html" },
  ];
  const rightLinks = [
    { label: "Field Notes", href: "Journal.html" },
    { label: "People",      href: "People%20%26%20Places.html" },
  ];

  const allLinks = [...leftLinks, ...rightLinks];

  return (
    <header style={{
      position: "fixed", top: 0, left: 0, right: 0, zIndex: 40,
      transition: "background 260ms var(--ease-out), border-color 260ms var(--ease-out), color 260ms var(--ease-out)",
      background: mobileOpen ? "var(--paper)" : bg,
      backdropFilter: (!overHero && !mobileOpen) ? "saturate(140%) blur(12px)" : "none",
      borderBottom: `1px solid ${(!overHero || mobileOpen) ? "var(--rule)" : "transparent"}`,
      color: mobileOpen ? "var(--ink)" : textColor,
    }}>
      <div style={{
        maxWidth: "var(--maxw)", margin: "0 auto",
        padding: "22px var(--pad-x)",
        display: "grid", gridTemplateColumns: "1fr auto 1fr",
        alignItems: "center", gap: 24,
      }}>
        {/* Desktop left nav */}
        <nav className="eb-nav-desktop" style={{ display: "flex", gap: 32, alignItems: "center" }}>
          {leftLinks.map(l => (
            <NavLink
              key={l.label}
              link={l}
              color={textColor}
              openDropdown={openDropdown}
              setOpenDropdown={setOpenDropdown}
              overHero={overHero}
            />
          ))}
        </nav>
        {/* Mobile: hamburger fills left slot */}
        <button
          className="eb-nav-mobile-toggle"
          onClick={() => setMobileOpen(o => !o)}
          aria-label={mobileOpen ? "Close menu" : "Open menu"}
          style={{
            display: "none",
            background: "none", border: "none", cursor: "pointer",
            padding: "8px 0", justifyContent: "flex-start",
            color: mobileOpen ? "var(--ink)" : textColor,
            transition: "color 260ms var(--ease-out)",
          }}
        >
          <div style={{ width: 24, height: 16, position: "relative", display: "flex", flexDirection: "column", justifyContent: "space-between" }}>
            <span style={{
              display: "block", height: 1.5,
              background: "currentColor",
              transform: mobileOpen ? "translateY(7px) rotate(45deg)" : "none",
              transition: "transform 240ms var(--ease-out)",
            }}/>
            <span style={{
              display: "block", height: 1.5,
              background: "currentColor",
              opacity: mobileOpen ? 0 : 1,
              transition: "opacity 180ms var(--ease-out)",
            }}/>
            <span style={{
              display: "block", height: 1.5,
              background: "currentColor",
              transform: mobileOpen ? "translateY(-7px) rotate(-45deg)" : "none",
              transition: "transform 240ms var(--ease-out)",
            }}/>
          </div>
        </button>

        <a href="Emma Basic Homepage.html" style={{
          fontFamily: '"Futura", "Helvetica Neue", Arial, sans-serif',
          fontSize: 24, letterSpacing: "0.04em",
          fontWeight: 400, fontStyle: "normal",
          textTransform: "uppercase",
          textDecoration: "none",
          color: mobileOpen ? "var(--ink)" : textColor,
          whiteSpace: "nowrap",
          transition: "color 260ms var(--ease-out)",
          textAlign: "center",
        }}>
          Emma Basic
        </a>
        <nav className="eb-nav-desktop" style={{ display: "flex", gap: 32, alignItems: "center", justifyContent: "flex-end" }}>
          {rightLinks.map(l => (
            <NavLink key={l.label} link={l} color={textColor} overHero={overHero} openDropdown={openDropdown} setOpenDropdown={setOpenDropdown} />
          ))}
        </nav>
        {/* Mobile: empty right slot to keep logo centred */}
        <div className="eb-nav-mobile-spacer" style={{ display: "none" }} />
      </div>

      {/* Mobile full-screen menu */}
      <div style={{
        position: "fixed", top: 0, left: 0, right: 0, bottom: 0,
        background: "var(--paper)",
        display: "flex", flexDirection: "column",
        padding: "100px var(--pad-x) 48px",
        opacity: mobileOpen ? 1 : 0,
        pointerEvents: mobileOpen ? "auto" : "none",
        transform: mobileOpen ? "translateY(0)" : "translateY(-12px)",
        transition: "opacity 280ms var(--ease-out), transform 280ms var(--ease-out)",
        zIndex: 39,
        overflowY: "auto",
      }}>
        <nav style={{ display: "flex", flexDirection: "column", gap: 0 }}>
          {allLinks.map(l => (
            <div key={l.label}>
              <a href={l.href} onClick={() => setMobileOpen(false)} style={{
                fontFamily: "var(--f-display)", fontWeight: 400,
                fontSize: "clamp(28px, 7vw, 44px)",
                letterSpacing: "-0.02em", lineHeight: 1.1,
                color: "var(--ink)", textDecoration: "none",
                display: "block", padding: "12px 0",
                borderBottom: "1px solid var(--rule)",
              }}>
                {l.label}
              </a>
              {l.dropdown && l.dropdown.map(d => (
                <a key={d.label} href={d.href} onClick={() => setMobileOpen(false)} style={{
                  fontFamily: "var(--f-body)", fontSize: 11, letterSpacing: "0.22em",
                  textTransform: "uppercase",
                  color: "var(--ink-60)", textDecoration: "none",
                  display: "block", padding: "10px 0 10px 20px",
                  borderBottom: "1px solid var(--rule)",
                }}>
                  {d.label}
                </a>
              ))}
            </div>
          ))}
        </nav>
      </div>

      <style>{`
        @media (max-width: 768px) {
          .eb-nav-desktop { display: none !important; }
          .eb-nav-mobile-toggle { display: flex !important; }
          .eb-nav-mobile-spacer { display: block !important; }
        }
      `}</style>
    </header>
  );
}

function NavLink({ link, color, openDropdown, setOpenDropdown, overHero }) {
  const [hover, setHover] = React.useState(false);
  const hasDropdown = !!link.dropdown;
  const isOpen = hasDropdown && openDropdown === link.label;

  return (
    <div
      onMouseEnter={() => {
        setHover(true);
        if (hasDropdown) setOpenDropdown(link.label);
      }}
      onMouseLeave={() => {
        setHover(false);
        if (hasDropdown) setOpenDropdown(null);
      }}
      style={{ position: "relative" }}
    >
      <a href={link.href}
        style={{
          fontFamily: "var(--f-body)", fontSize: 14.5,
          letterSpacing: "0.04em", textTransform: "uppercase",
          color, textDecoration: "none",
          position: "relative", padding: "4px 0",
          display: "inline-flex", alignItems: "center", gap: 6,
          transition: "color 260ms var(--ease-out)",
        }}>
        {link.label}
        {hasDropdown && (
          <span style={{
            fontFamily: "var(--f-mono)", fontSize: 9, opacity: 0.6,
            transform: `rotate(${isOpen ? 180 : 0}deg)`,
            transition: "transform 220ms var(--ease-out)",
          }}>▾</span>
        )}
        <span style={{
          position: "absolute", left: 0, right: hasDropdown ? 14 : 0, bottom: -2,
          height: 1, background: color,
          transform: `scaleX(${hover ? 1 : 0})`, transformOrigin: "left",
          transition: "transform 240ms var(--ease-out), background 260ms var(--ease-out)",
        }}/>
      </a>

      {hasDropdown && (
        <div style={{
          position: "absolute", top: "100%", left: -16,
          paddingTop: 10, minWidth: 220,
          opacity: isOpen ? 1 : 0,
          pointerEvents: isOpen ? "auto" : "none",
          transform: `translateY(${isOpen ? 0 : -6}px)`,
          transition: "opacity 220ms var(--ease-out), transform 220ms var(--ease-out)",
        }}>
          <div style={{
            background: "var(--paper-bright, #FBFAF7)",
            border: "1px solid var(--rule)",
            padding: "10px 0",
            display: "grid",
          }}>
            {link.dropdown.map(d => (
              <a key={d.label} href={d.href} style={{
                fontFamily: "var(--f-body)", fontSize: 14.5,
                letterSpacing: "0.04em", textTransform: "uppercase",
                color: "var(--ink)", textDecoration: "none",
                padding: "12px 20px",
                transition: "background 180ms var(--ease-out)",
              }}
              onMouseEnter={e => e.currentTarget.style.background = "var(--paper-shade, #ECECEC)"}
              onMouseLeave={e => e.currentTarget.style.background = "transparent"}
              >
                {d.label}
              </a>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

window.TopNav = TopNav;
