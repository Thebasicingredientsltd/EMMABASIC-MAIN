/* ============================================================
   Journal — editorial article index page.
   Categories: Recipes, Ingredient Stories, Behind the Product,
   The Grit (lifestyle / training / running)
   ============================================================ */

const JOURNAL_POSTS = [
  {
    id: "matcha-preparation",
    category: "Ingredient Stories",
    date: "14 Apr 2026",
    title: "How to prepare matcha properly — and why most people don't.",
    excerpt: "The temperature of the water, the direction of the whisk, the age of the powder. Small things with large consequences.",
    image: "assets/journal/Matcha-journal-image.png",
    tone: "warm",
    featured: true,
  },
  {
    id: "sushi-rice-ratio",
    category: "Recipes",
    date: "08 Apr 2026",
    title: "Koshihikari and the short-grain question. What the rice in your bowl actually is.",
    excerpt: "Most sushi rice in British kitchens is Italian. The difference between that and genuine short-grain Japonica is something you taste immediately — once you know what you're looking for.",
    image: "assets/journal/Sushi-rice-journal-image.avif",
    tone: "warm",
    featured: false,
  },
  {
    id: "binchotan-kitchen",
    category: "Behind the Product",
    date: "01 Apr 2026",
    title: "Binchotan: 300 years of Japanese charcoal production.",
    excerpt: "We spent a day with a Wakayama producer. Here's what we learned about a process that hasn't changed since the Edo period.",
    image: "assets/journal/Binochtan-water-filter-journal.jpg",
    tone: "ink",
    featured: false,
  },
  {
    id: "cold-run-furikake",
    category: "The Grit",
    date: "24 Mar 2026",
    title: "What we eat after a long run.",
    excerpt: "The rice goes on before the run. By the time you're back, it's waiting. Furikake, a soft egg, sesame oil. That's it.",
    image: "assets/journal/Nori-furikake-journal.png",
    tone: "ink",
    featured: false,
  },
  {
    id: "tamari-vs-soy",
    category: "Ingredient Stories",
    date: "17 Mar 2026",
    title: "Tamari vs soy sauce. They are not the same thing.",
    excerpt: "One uses wheat. One doesn't. The difference in flavour is real, and once you know it, you can't un-taste it.",
    image: "assets/journal/Soy-sauce-image.jpg",
    tone: "warm",
    featured: false,
  },
  {
    id: "gyoza-technique",
    category: "Recipes",
    date: "10 Mar 2026",
    title: "The yaki-gyoza method. Steam-fry, not fry.",
    excerpt: "Hot oil, golden base, then water and a lid. Two minutes of steam finishes what the pan starts. Order matters.",
    image: "assets/journal/Chicken-gyoza-journal.jpg",
    tone: "warm",
    featured: false,
  },
  {
    id: "sesame-oil-press",
    category: "Behind the Product",
    date: "03 Mar 2026",
    title: "Why we only use physically pressed sesame oil.",
    excerpt: "Most sesame oil is solvent-extracted. Ours isn't. The process takes longer, costs more, and the difference is unmistakeable.",
    image: "assets/journal/Sesame-oil-journal.jpg",
    tone: "warm",
    featured: false,
  },
  {
    id: "trail-noodles",
    category: "The Grit",
    date: "24 Feb 2026",
    title: "24 miles. Cold. What you eat matters more than you think.",
    excerpt: "Long run nutrition doesn't have to be complicated. Soba, dashi, sesame. The body wants simple things, done well.",
    image: "assets/journal/soba-dashi-journal.jpg",
    tone: "ink",
    featured: false,
  },
  {
    id: "wakame-guide",
    category: "Ingredient Stories",
    date: "17 Feb 2026",
    title: "Wakame: the seaweed worth knowing.",
    excerpt: "It's not nori. It's not kelp. Wakame is its own thing — silky, mild, nutritionally serious, and underused in Western kitchens.",
    image: "assets/journal/wakame-50g-journal.png",
    tone: "warm",
    featured: false,
  },
];

const CATEGORIES = ["All", "Recipes", "Ingredient Stories", "Behind the Product", "The Grit"];
const INSTAGRAM_TAB = "Instagram";

function JournalIndex() {
  const [active, setActive] = React.useState("All");

  const filtered = active === "All"
    ? JOURNAL_POSTS
    : JOURNAL_POSTS.filter(p => p.category === active);

  const featured = filtered.find(p => p.featured) || filtered[0];
  const rest = filtered.filter(p => p !== featured);

  return (
    <section style={{ background: "var(--paper)" }}>

      {/* Category filter bar */}
      <div style={{
        position: "sticky", top: 72, zIndex: 20,
        background: "rgba(246,246,246,0.92)",
        backdropFilter: "saturate(140%) blur(10px)",
        borderTop: "1px solid var(--rule)",
        borderBottom: "1px solid var(--rule)",
      }}>
        <div style={{
          maxWidth: "var(--maxw)", margin: "0 auto",
          padding: "14px var(--pad-x)",
          display: "flex", gap: "clamp(16px, 2.5vw, 28px)", alignItems: "center",
          overflowX: "auto", scrollbarWidth: "none",
          paddingRight: 0,
        }}>
          {CATEGORIES.map((cat, i) => (
            <button key={cat} onClick={() => setActive(cat)} style={{
              fontFamily: "var(--f-body)", fontSize: 11, letterSpacing: "0.22em",
              textTransform: "uppercase",
              color: active === cat ? "var(--ink)" : "var(--ink-60)",
              background: "none", border: "none", padding: "0 0 2px", cursor: "pointer",
              borderBottom: `1px solid ${active === cat ? "var(--ink)" : "transparent"}`,
              transition: "color 200ms var(--ease-out), border-color 200ms var(--ease-out)",
              whiteSpace: "nowrap",
            }}>
              {cat}
            </button>
          ))}
          <a href="instagram.html" style={{
            fontFamily: "var(--f-body)", fontSize: 11, letterSpacing: "0.22em",
            textTransform: "uppercase", color: "var(--ink-60)",
            background: "none", border: "none", padding: "0 0 2px", cursor: "pointer",
            borderBottom: "1px solid transparent",
            textDecoration: "none", whiteSpace: "nowrap",
            marginRight: "var(--pad-x)",
            transition: "color 200ms var(--ease-out)",
          }}
            onMouseEnter={e => e.currentTarget.style.color = "var(--ink)"}
            onMouseLeave={e => e.currentTarget.style.color = "var(--ink-60)"}
          >Instagram</a>
        </div>
      </div>

      <div style={{ maxWidth: "var(--maxw)", margin: "0 auto", padding: "clamp(72px, 10vh, 120px) var(--pad-x) clamp(96px, 14vh, 160px)" }}>

        {/* Featured post */}
        {featured && (
          <Reveal>
            <a href={`journal-post.html?id=${featured.id}`} style={{ textDecoration: "none", color: "inherit", display: "block" }}>
              <FeaturedCard post={featured} />
            </a>
          </Reveal>
        )}

        {/* Post grid */}
        {rest.length > 0 && (
          <div className="eb-journal-grid" style={{
            display: "grid",
            gridTemplateColumns: "repeat(3, 1fr)",
            gap: "clamp(48px, 6vh, 80px) clamp(24px, 3vw, 48px)",
            marginTop: "clamp(64px, 10vh, 120px)",
            paddingTop: "clamp(64px, 10vh, 120px)",
            borderTop: "1px solid var(--rule)",
          }}>
            {rest.map((post, i) => (
              <Reveal key={post.id} delay={i * 60}>
                <a href={`journal-post.html?id=${post.id}`} style={{ textDecoration: "none", color: "inherit", display: "block" }}>
                  <PostCard post={post} />
                </a>
              </Reveal>
            ))}
          </div>
        )}

        {filtered.length === 0 && (
          <div style={{
            padding: "120px 0", textAlign: "center",
            fontFamily: "var(--f-body)", fontSize: 11, letterSpacing: "0.22em",
            textTransform: "uppercase", color: "var(--ink-60)",
          }}>
            Nothing here yet.
          </div>
        )}
      </div>
    </section>
  );
}

/* ── Featured Card ───────────────────────────────────────── */
function FeaturedCard({ post }) {
  const [hover, setHover] = React.useState(false);
  return (
    <div
      onMouseEnter={() => setHover(true)}
      onMouseLeave={() => setHover(false)}
      className="eb-journal-featured"
      style={{
        display: "grid",
        gridTemplateColumns: "1fr 1fr",
        gap: "clamp(48px, 8vw, 120px)",
        alignItems: "center",
      }}
    >
      {/* Image */}
      <div style={{
        aspectRatio: "4/3",
        background: post.tone === "ink" ? "var(--ink)" : "var(--paper-shade)",
        overflow: "hidden",
        position: "relative",
      }}>
        {post.image
          ? <img src={post.image} alt={post.title} style={{ width: "100%", height: "100%", objectFit: "cover", objectPosition: "center", display: "block", transform: hover ? "scale(1.04)" : "scale(1)", transition: "transform 700ms var(--ease-out)" }} />
          : <Placeholder label={post.title.toUpperCase()} tone={post.tone} />
        }
      </div>

      {/* Text */}
      <div style={{ display: "grid", gap: 24 }}>
        <div style={{
          fontFamily: "var(--f-body)", fontSize: 10.5, letterSpacing: "0.22em",
          textTransform: "uppercase", color: "var(--ink-60)",
        }}>
          Featured · {post.date}
        </div>
        <h2 style={{
          fontFamily: "var(--f-display)", fontWeight: 400,
          fontSize: "clamp(28px, 3.2vw, 48px)",
          letterSpacing: "-0.02em", lineHeight: 1.1, margin: 0,
          backgroundImage: "linear-gradient(var(--ink), var(--ink))",
          backgroundRepeat: "no-repeat",
          backgroundSize: hover ? "100% 1px" : "0% 1px",
          backgroundPosition: "0 100%",
          paddingBottom: 2,
          transition: "background-size 400ms var(--ease-out)",
        }}>
          {post.title}
        </h2>
        <p style={{
          fontFamily: "var(--f-display)", fontStyle: "italic",
          fontSize: "clamp(16px, 1.4vw, 19px)", lineHeight: 1.6,
          color: "var(--ink-90)", margin: 0, maxWidth: 480,
        }}>
          {post.excerpt}
        </p>
        <span style={{
          fontFamily: "var(--f-body)", fontSize: 11, letterSpacing: "0.22em",
          textTransform: "uppercase", color: "var(--ink)",
          borderBottom: "1px solid var(--ink)", paddingBottom: 2,
          display: "inline-block", width: "fit-content",
          opacity: hover ? 1 : 0.6,
          transition: "opacity 200ms var(--ease-out)",
        }}>
          Read →
        </span>
      </div>
    </div>
  );
}

/* ── Regular Post Card ───────────────────────────────────── */
function PostCard({ post }) {
  const [hover, setHover] = React.useState(false);
  return (
    <div
      onMouseEnter={() => setHover(true)}
      onMouseLeave={() => setHover(false)}
      style={{ display: "grid", gap: 20 }}
    >
      {/* Image */}
      <div style={{
        aspectRatio: "3/2",
        background: post.tone === "ink" ? "var(--ink)" : "var(--paper-shade)",
        overflow: "hidden",
        position: "relative",
      }}>
        {post.image
          ? <img src={post.image} alt={post.title} style={{ width: "100%", height: "100%", objectFit: "cover", objectPosition: "center", display: "block", transform: hover ? "scale(1.04)" : "scale(1)", transition: "transform 700ms var(--ease-out)" }} />
          : <Placeholder label={post.title.toUpperCase()} tone={post.tone} />
        }
      </div>

      {/* Text */}
      <div style={{ display: "grid", gap: 10 }}>
        <div style={{
          fontFamily: "var(--f-body)", fontSize: 10, letterSpacing: "0.22em",
          textTransform: "uppercase", color: "var(--ink-60)",
        }}>
          {post.date}
        </div>
        <h3 style={{
          fontFamily: "var(--f-display)", fontWeight: 400,
          fontSize: "clamp(20px, 1.8vw, 26px)",
          letterSpacing: "-0.016em", lineHeight: 1.15, margin: 0,
          backgroundImage: "linear-gradient(var(--ink), var(--ink))",
          backgroundRepeat: "no-repeat",
          backgroundSize: hover ? "100% 1px" : "0% 1px",
          backgroundPosition: "0 100%",
          paddingBottom: 2,
          transition: "background-size 380ms var(--ease-out)",
        }}>
          {post.title}
        </h3>
        <p style={{
          fontFamily: "var(--f-display)", fontStyle: "italic",
          fontSize: 14, lineHeight: 1.55,
          color: "var(--ink-90)", margin: 0,
        }}>
          {post.excerpt}
        </p>
      </div>
    </div>
  );
}

/* Inject responsive styles */
const _journalStyle = document.createElement("style");
_journalStyle.textContent = `
  @media (max-width: 768px) {
    .eb-journal-featured { grid-template-columns: 1fr !important; gap: clamp(24px, 4vw, 48px) !important; }
    .eb-journal-grid { grid-template-columns: repeat(2, 1fr) !important; }
  }
  @media (max-width: 480px) {
    .eb-journal-grid { grid-template-columns: 1fr !important; }
  }
`;
document.head.appendChild(_journalStyle);

window.JournalIndex = JournalIndex;
