/* ============================================================
   TeamGrid — portrait grid.
   Warm intro, then factual: photo, name, role, one-line bio.
   Click a card to flip between professional and informal photo.
   ============================================================ */

const EMMA = { name: "Emma", role: "Founder", bio: "Read the ingredients on the food label.\n\nDon't let the legal but harmful additives hurt you and your loved ones. Cook fresh ingredients in your kitchen are, of course, the finest. Processed foods are not all evil. Many responsible manufacturers are sharing the same belief as we do, in pursuit of removing additives.\n\nRemove additives, my quest, and my purpose.", tone: "warm", image: "assets/Employees-page/emma 1.jpg", image2: "assets/Employees-page/emma 2.jpg", phone: "+44 7894 512430", email: "Emma@thebasicingredients.com" };

const TEAM = [
  { name: "Yoko",     role: "Technical Account Manager",       bio: "",                                                                                                                                                                                                      tone: "cool", image: "assets/Employees-page/yoko.png",         image2: "", phone: "" },
  { name: "Itsuro",   role: "Quality Manager",                 bio: "Cutting additives and UPFs while boosting fiber to 30g daily has transformed my gut health — I feel younger than ever!",                                                                                tone: "cool", image: "assets/Employees-page/itsuro 1.jpg",      image2: "", phone: "" },
  { name: "Ran",      role: "Wholesale Manager",               bio: "I love travelling and enjoy delicious food & wine. I'm always looking for safe, nutritious, and yummy food.\n\nUPF, ultra processed food, it harms your health. It gives your brain instant reward, making you addicted. How to identify these UPFs and keep away from it?\n\nAdditives are the signpost of UPFs. Such as emulsifiers in ice cream or MSG in curry blocks. In the EU, more than 2,000 additives are legally permitted to use. Yes, over 2000, a large number! It's even difficult for a professional working in the food industry with a lifetime of experience to identify so many.\n\nEmma Basic, promises NEVER ANY ADDITIVES. We've removed the additives and harmful ingredients (such as refined oils, maltodextrins, high fructose corn syrup) for you so you don't have to spend 10,000 hours to study it.", tone: "warm", image: "assets/Employees-page/ran 1.jpg", image2: "assets/Employees-page/rann 2.jpg", phone: "+44 7305 075030", email: "Ran@thebasicingredients.com", },
  { name: "Nancy",    role: "Technical Manager",               bio: "Are you looking for food products with no artificial ingredients for your business?\n\nMy team specialises in clean-label foods, recognised by the Food and Drink Federation in Emerging Business 2021 Awards.\n\nWe can source wholesome food ingredients for you, providing the technical expertise, taking the stress of global shipping off your shoulders.\n\nThe catalogue at the bottom of the website details our B2B products. I will be delighted to receive your call.", tone: "cool", image: "assets/Employees-page/Nancy 1.jpg", image2: "assets/Employees-page/nancy 2.jpg", phone: "+44 7521 279887", email: "nancy@thebasicingredients.com" },
  { name: "James",    role: "Head of Technology & E-Commerce", bio: "Working in a clean-label food company is NOT easy!\n\nDiet Coke and Schweppes had been my favourites for many years. Now I've learned artificial sweeteners E951 in Diet Coke and E955 in tonic water could dampen the immune response. Although I've made my decision to quit both, being blood type B-, I am forgetful. Whenever I accidentally buy a bottle of the above, I get a shout from one of the extremists in the team! Guess which one.", tone: "cool", image: "assets/Employees-page/James 1.jpg", image2: "assets/Employees-page/james 2.jpg", phone: "+44 07933 334055", email: "james@thebasicingredients.com" },
  { name: "Ling",     role: "Inventory Buyer",                 bio: "Human beings are drowning in plastic pollution.\n\nBirds and fish are dying because of plastic.\n\nAs a buyer, I DO NOT like to see plastic. Inspire me with your creative and sustainable packages.\n\nIf you have a sustainable product that matches our values, I would love to hear from you.", tone: "warm", image: "assets/Employees-page/ling 1.jpg", image2: "assets/Employees-page/ling 2.jpg", phone: "+44 7526 938210", email: "ling@thebasicingredients.com" },
  { name: "Olivia",   role: "Designer",                        bio: "Growing up in a farming family made food quality second nature — from eating out of the garden to moving to London.",                                                                                   tone: "warm", image: "assets/Employees-page/olivia.jpg",        image2: "", phone: "", imagePosition: "center 12%" },
  { name: "Taiki",    role: "Sales & Operations Executive",    bio: "I love being outside — golfing, playing football, or heading out for a hike whenever I can. Clean, simple ingredients matter to me, which is why Emma Basic fits so naturally into my routine.",        tone: "cool", image: "assets/Employees-page/taiki.jpg",         image2: "", phone: "", imageZoom: 2.4, imagePosition: "40% center" },
  { name: "Cotton",   role: "Chief Morale Officer",            bio: "Attends every tasting. Has never approved an additive.",                                                                                                                                                tone: "warm", image: "assets/Employees-page/cotton 1.jpg",     image2: "assets/Employees-page/cotton 2.jpg", phone: "" },
];

function TeamGrid() {
  // CMS-managed content (data/people.js). Falls back to the built-in
  // defaults above so the page still renders if the data file is missing.
  const teamData = (window.EB_PEOPLE && window.EB_PEOPLE.team) || {};
  const members = (teamData.members && teamData.members.length)
    ? teamData.members
    : [EMMA, ...TEAM];
  const headingLine1 = teamData.headingLine1 || "The people";
  const headingLine2 = teamData.headingLine2 || "behind the jar.";
  const intro = teamData.intro || "A small team, united by one rule — no additives, ever.";

  return (
    <section style={{
      padding: "clamp(120px, 16vh, 180px) var(--pad-x) clamp(80px, 12vh, 140px)",
      background: "var(--paper)",
      color: "var(--ink)",
    }}>
      <div style={{ maxWidth: "var(--maxw)", margin: "0 auto" }}>
        <div style={{
          display: "grid", gridTemplateColumns: "1fr 1fr",
          gap: "clamp(32px, 6vw, 96px)", alignItems: "end",
          marginBottom: "clamp(56px, 8vh, 96px)",
        }}>
          <Reveal>
            <h2 style={{
              fontFamily: "var(--f-display)", fontWeight: 400,
              fontSize: "clamp(44px, 6vw, 92px)",
              letterSpacing: "-0.03em", lineHeight: 0.92, margin: 0,
              fontVariationSettings: '"opsz" 144, "SOFT" 30',
            }}>
              {headingLine1}<br/>
              <em style={{ fontStyle: "normal", fontFamily: "var(--f-body)", fontWeight: 400, letterSpacing: "-0.02em" }}>
                {headingLine2}
              </em>
            </h2>
          </Reveal>
          <Reveal delay={160}>
            <p style={{
              fontFamily: "var(--f-body)", fontSize: 18, lineHeight: 1.7,
              maxWidth: 460, margin: 0, color: "var(--ink-90)", paddingBottom: 12,
            }}>
              {intro}
            </p>
          </Reveal>
        </div>

        {/* Full team grid including Emma */}
        <div className="eb-team-grid" style={{
          display: "grid",
          gridTemplateColumns: "repeat(4, 1fr)",
          gap: "clamp(16px, 2vw, 32px) clamp(16px, 2vw, 32px)",
          alignItems: "start",
        }}>
          {members.map((m, i) => (
            <TeamMember key={i} m={m} index={i} />
          ))}
        </div>

      </div>
    </section>
  );
}

function TeamMember({ m, index }) {
  const [ref, visible] = useReveal(0.1);
  const [open, setOpen] = React.useState(false);
  const [hover, setHover] = React.useState(false);
  const canFlip = !!m.image2;

  return (
    <>
      <div
        ref={ref}
        onMouseEnter={() => setHover(true)}
        onMouseLeave={() => setHover(false)}
        onClick={() => canFlip && setOpen(true)}
        style={{
          display: "grid", gap: 16,
          opacity: visible ? 1 : 0,
          transform: `translateY(${visible ? 0 : 28}px)`,
          transition: `opacity 800ms var(--ease-out) ${(index % 4) * 60 + Math.floor(index / 4) * 120}ms, transform 800ms var(--ease-out) ${(index % 4) * 60 + Math.floor(index / 4) * 120}ms`,
          cursor: canFlip ? "pointer" : "default",
        }}>
        <div style={{
          position: "relative",
          aspectRatio: "3/4",
          overflow: "hidden",
          background: "var(--paper-bright)",
        }}>
          {/* B&W image 1 — always rendered, fades out when open */}
          <div style={{
            position: "absolute", inset: 0,
            transform: hover ? "scale(1.04)" : "scale(1)",
            transition: "transform 700ms var(--ease-out)",
          }}>
            {m.image
              ? <img src={m.image} alt={m.name} style={{
                  width: "100%", height: "100%", objectFit: "cover",
                  objectPosition: m.imagePosition || "center top", display: "block",
                  transform: m.imageZoom ? `scale(${m.imageZoom})` : "none",
                  transformOrigin: m.imagePosition || "center top",
                  filter: "grayscale(100%)",
                }} />
              : <Placeholder label={m.name.toUpperCase()} tone={m.tone} />
            }
          </div>
          {canFlip && (
            <div style={{
              position: "absolute", bottom: 10, right: 10,
              background: "rgba(0,0,0,0.38)", borderRadius: 3,
              padding: "4px 8px",
              fontFamily: "var(--f-body)", fontSize: 9.5, letterSpacing: "0.14em",
              textTransform: "uppercase", color: "#fff",
              pointerEvents: "none",
              opacity: hover ? 1 : 0,
              transition: "opacity 220ms var(--ease-out)",
            }}>View</div>
          )}
        </div>
        <div style={{ display: "grid", gap: 4 }}>
          <h3 style={{
            fontFamily: "var(--f-display)", fontWeight: 400,
            fontSize: 22, letterSpacing: "-0.01em", lineHeight: 1.1, margin: 0,
            fontVariationSettings: '"opsz" 144, "SOFT" 30',
          }}>{m.name}</h3>
          <span style={{
            fontFamily: "var(--f-body)", fontWeight: 400, fontSize: 11, letterSpacing: "0.18em",
            textTransform: "uppercase", color: "var(--ink-60)",
          }}>{m.role}</span>
          {m.bio && (
            <p style={{
              fontFamily: "var(--f-body)", fontSize: 14, lineHeight: 1.55,
              color: "var(--ink-70)", margin: "8px 0 0",
            }}>
              {m.bio.match(/[^.!?]+[.!?]+/g)?.slice(0, 2).join(" ") || m.bio.slice(0, 120)}
              {canFlip && <span style={{ color: "var(--ink-40)", marginLeft: 4 }}>...</span>}
            </p>
          )}
        </div>
      </div>

      {/* Popup card */}
      {open && (
        <TeamPopup m={m} onClose={() => setOpen(false)} />
      )}
    </>
  );
}

function TeamPopup({ m, onClose }) {
  React.useEffect(() => {
    const onKey = e => { if (e.key === "Escape") onClose(); };
    document.addEventListener("keydown", onKey);
    document.body.style.overflow = "hidden";
    return () => {
      document.removeEventListener("keydown", onKey);
      document.body.style.overflow = "";
    };
  }, []);

  return ReactDOM.createPortal(
    <div
      onClick={onClose}
      style={{
        position: "fixed", inset: 0, zIndex: 9000,
        background: "rgba(0,0,0,0.55)",
        display: "flex", alignItems: "center", justifyContent: "center",
        padding: "clamp(16px, 4vw, 48px)",
        backdropFilter: "blur(4px)",
        animation: "eb-fade-in 220ms var(--ease-out) both",
      }}>
      <div
        onClick={e => e.stopPropagation()}
        style={{
          background: "var(--paper)",
          maxWidth: 860, width: "100%",
          display: "grid", gridTemplateColumns: "1fr 1fr",
          gap: 0,
          boxShadow: "0 32px 80px rgba(0,0,0,0.22)",
          animation: "eb-slide-up 280ms var(--ease-out) both",
          position: "relative",
          overflow: "hidden",
        }}>
        {/* Photo */}
        <div style={{ height: 520, overflow: "hidden", background: "var(--paper-bright)" }}>
          <img src={m.image2} alt={m.name} style={{
            width: "100%", height: "100%", objectFit: "cover",
            objectPosition: "center top", display: "block",
          }} />
        </div>
        {/* Info */}
        <div style={{
          padding: "clamp(20px, 3vw, 32px)",
          display: "flex", flexDirection: "column", justifyContent: "space-between",
          borderLeft: "1px solid var(--rule)",
          overflowY: "auto", maxHeight: 520,
        }}>
          <div>
            <h3 style={{
              fontFamily: "var(--f-display)", fontWeight: 400,
              fontSize: "clamp(22px, 3vw, 32px)", letterSpacing: "-0.02em",
              lineHeight: 1, margin: "0 0 6px",
              fontVariationSettings: '"opsz" 144, "SOFT" 30',
            }}>{m.name}</h3>
            <span style={{
              fontFamily: "var(--f-body)", fontSize: 10, letterSpacing: "0.2em",
              textTransform: "uppercase", color: "var(--ink-60)",
            }}>{m.role}</span>
            {m.bio ? <div style={{ margin: "20px 0 0" }}>
              {m.bio.split("\n\n").map((para, i) => (
                <p key={i} style={{
                  fontFamily: "var(--f-body)", fontSize: 15, lineHeight: 1.6,
                  color: "var(--ink-90)", margin: i === 0 ? 0 : "12px 0 0",
                  fontStyle: i === m.bio.split("\n\n").length - 1 ? "italic" : "normal",
                }}>{para}</p>
              ))}
            </div> : null}
          </div>
          <div style={{ marginTop: 24 }}>
            {m.phone ? (
              <a href={"tel:" + m.phone} style={{
                fontFamily: "var(--f-body)", fontSize: 15,
                color: "var(--ink)", textDecoration: "none",
                display: "block", marginBottom: 8,
                letterSpacing: "0.02em",
              }}>{m.phone}</a>
            ) : null}
            {m.email ? (
              <a href={"mailto:" + m.email} style={{
                fontFamily: "var(--f-body)", fontSize: 15,
                color: "var(--ink)", textDecoration: "none",
                display: "block", marginBottom: 16,
                letterSpacing: "0.02em",
              }}>{m.email}</a>
            ) : null}
            <button
              onClick={onClose}
              style={{
                fontFamily: "var(--f-body)", fontSize: 10, letterSpacing: "0.18em",
                textTransform: "uppercase", color: "var(--ink-60)",
                background: "none", border: "1px solid var(--rule)",
                padding: "8px 16px", cursor: "pointer",
              }}>Close</button>
          </div>
        </div>
      </div>
    </div>,
    document.body
  );
}

function EventPhoto({ src, alt, index }) {
  const [ref, visible] = useReveal(0.08);
  const [hover, setHover] = React.useState(false);
  return (
    <div
      ref={ref}
      onMouseEnter={() => setHover(true)}
      onMouseLeave={() => setHover(false)}
      style={{
        position: "relative",
        aspectRatio: "3/2",
        overflow: "hidden",
        background: "var(--paper-bright)",
        border: "1px solid var(--rule)",
        opacity: visible ? 1 : 0,
        transform: `translateY(${visible ? 0 : 28}px)`,
        transition: `opacity 800ms var(--ease-out) ${index * 100}ms, transform 800ms var(--ease-out) ${index * 100}ms`,
      }}
    >
      <div style={{
        position: "absolute", inset: 0,
        transform: hover ? "scale(1.03)" : "scale(1)",
        transition: "transform 700ms var(--ease-out)",
      }}>
        <img src={src} alt={alt} style={{ width: "100%", height: "100%", objectFit: "cover", objectPosition: "center", display: "block" }} />
      </div>
    </div>
  );
}

/* Inject responsive styles */
const _teamStyle = document.createElement("style");
_teamStyle.textContent = `
  .eb-team-featured { display: grid; grid-template-columns: 1fr 1fr; }
  @media (max-width: 768px) {
    .eb-team-grid { grid-template-columns: repeat(2, 1fr) !important; }
    .eb-team-featured { grid-template-columns: 1fr !important; }
  }
  @media (max-width: 480px) {
    .eb-team-grid { grid-template-columns: repeat(2, 1fr) !important; }
  }
  @keyframes eb-fade-in {
    from { opacity: 0; }
    to   { opacity: 1; }
  }
  @keyframes eb-slide-up {
    from { opacity: 0; transform: translateY(20px); }
    to   { opacity: 1; transform: translateY(0); }
  }
  @media (max-width: 520px) {
    .eb-team-popup-card { grid-template-columns: 1fr !important; }
    .eb-team-popup-card > div:first-child { height: 260px !important; }
  }
`;
document.head.appendChild(_teamStyle);

window.TeamGrid = TeamGrid;
