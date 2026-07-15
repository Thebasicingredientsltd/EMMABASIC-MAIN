/* ============================================================
   JournalPost — reads ?id= from URL, renders full article.
   ============================================================ */

const JOURNAL_ARTICLES = {

  "matcha-preparation": {
    category: "Ingredient Stories",
    date: "14 Apr 2026",
    readTime: "5 min read",
    title: "How to prepare matcha properly — and why it's worth the extra minute.",
    image: "assets/journal/Matcha-journal-image.png",
    imagePosition: "center 35%",
    intro: "",
const JOURNAL_ARTICLES = {

  "matcha-preparation": {
    category: "Ingredient Stories",
    date: "14 Apr 2026",
    readTime: "5 min read",
    title: "How to prepare matcha properly — and why it's worth the extra minute.",
    image: "assets/journal/Matcha-journal-image.png",
    imagePosition: "center 35%",
    intro: "",
    body: [],
  },

  "sushi-rice-ratio": {
    category: "Recipes",
    date: "08 Apr 2026",
    readTime: "6 min read",
    title: "Koshihikari and the short-grain question. What the rice in your bowl actually is.",
    image: "assets/journal/Sushi-rice-journal-image.avif",
    intro: "",
    body: [],
  },

  "binchotan-kitchen": {
    category: "Behind the Product",
    date: "01 Apr 2026",
    readTime: "6 min read",
    title: "Binchotan: 300 years of Japanese charcoal production.",
    image: "assets/journal/Binochtan-water-filter-journal.jpg",
    intro: "",
    body: [],
  },

  "cold-run-furikake": {
    category: "The Grit",
    date: "24 Mar 2026",
    readTime: "3 min read",
    title: "What we eat after a long run.",
    image: "assets/journal/Nori-furikake-journal.png",
    intro: "",
    body: [],
  },

  "tamari-vs-soy": {
    category: "Ingredient Stories",
    date: "17 Mar 2026",
    readTime: "4 min read",
    title: "Tamari vs. soy sauce. They are not the same thing.",
    image: "assets/journal/Soy-sauce-image.jpg",
    intro: "",
    body: [],
  },

  "gyoza-technique": {
    category: "Recipes",
    date: "10 Mar 2026",
    readTime: "4 min read",
    title: "The yaki-gyoza method. Steam-fry, not fry.",
    image: "assets/journal/Chicken-gyoza-journal.jpg",
    intro: "",
    body: [],
  },

  "sesame-oil-press": {
    category: "Behind the Product",
    date: "03 Mar 2026",
    readTime: "5 min read",
    title: "Why we only use physically pressed sesame oil.",
    image: "assets/journal/Sesame-oil-journal.jpg",
    intro: "",
    body: [],
  },

  "trail-noodles": {
    category: "The Grit",
    date: "24 Feb 2026",
    readTime: "3 min read",
    title: "24 miles. Cold. What you eat matters more than you think.",
    image: "assets/journal/soba-dashi-journal.jpg",
    intro: "",
    body: [],
  },

  "wakame-guide": {
    category: "Ingredient Stories",
    date: "17 Feb 2026",
    readTime: "5 min read",
    title: "Wakame: the seaweed worth knowing.",
    image: "assets/journal/wakame-50g-journal.png",
    intro: "",
    body: [],
  },

};

/* ── Render helpers ─────────────────────────────────────────── */

function ArticleBlock({ block, index }) {
  const baseText = {
    fontFamily: "var(--f-display)", fontWeight: 400,
    fontSize: "clamp(17px, 1.4vw, 20px)", lineHeight: 1.75,
    letterSpacing: "-0.008em", color: "var(--ink-90)", margin: 0,
    fontVariationSettings: '"opsz" 24, "SOFT" 0',
  };
  const headStyle = {
    fontFamily: "var(--f-display)", fontWeight: 400,
    fontSize: "clamp(22px, 2vw, 30px)", lineHeight: 1.2,
    letterSpacing: "-0.02em", color: "var(--ink)",
    margin: "clamp(40px, 5vh, 64px) 0 clamp(16px, 2vh, 24px)",
    fontVariationSettings: '"opsz" 144, "SOFT" 0',
  };

  if (block.type === "p") return (
    <p style={{ ...baseText, marginBottom: "clamp(20px, 2.5vh, 28px)" }}>{block.text}</p>
  );
  if (block.type === "h2") return (
    <h2 style={headStyle}>{block.text}</h2>
  );
  if (block.type === "rule") return (
    <hr style={{ border: "none", borderTop: "1px solid var(--rule)", margin: "clamp(40px, 6vh, 72px) 0" }} />
  );
  return null;
}

/* ── Main component ─────────────────────────────────────────── */

function JournalPost() {
  const id = new URLSearchParams(window.location.search).get("id");
  const post = JOURNAL_ARTICLES[id];

  if (!post) {
    return (
      <div style={{
        minHeight: "60vh", display: "flex", alignItems: "center", justifyContent: "center",
        fontFamily: "var(--f-body)", fontSize: 11, letterSpacing: "0.22em",
        textTransform: "uppercase", color: "var(--ink-60)",
      }}>
        Story not found. <a href="Journal.html" style={{ color: "var(--ink)", marginLeft: 16, borderBottom: "1px solid var(--ink)", paddingBottom: 2 }}>Back to Journal →</a>
      </div>
    );
  }

  return (
    <article style={{ background: "var(--paper)", color: "var(--ink)" }}>

      {/* Hero image */}
      {post.image && (
        <div style={{
          width: "100%",
          height: "clamp(320px, 48vw, 680px)",
          overflow: "hidden",
          position: "relative",
        }}>
          <img
            src={post.image}
            alt={post.title}
            style={{ width: "100%", height: "100%", objectFit: "cover", objectPosition: post.imagePosition || "center", display: "block" }}
          />
        </div>
      )}

      <div style={{ maxWidth: 1100, margin: "0 auto", padding: "clamp(56px, 8vh, 96px) var(--pad-x) clamp(96px, 14vh, 160px)" }}>

        {/* Meta */}
        <div style={{
          display: "flex", gap: 24, alignItems: "center", flexWrap: "wrap",
          marginBottom: "clamp(32px, 4vh, 48px)",
          fontFamily: "var(--f-body)", fontSize: 10.5, letterSpacing: "0.22em",
          textTransform: "uppercase", color: "var(--ink-60)",
        }}>
          <a href="Journal.html" style={{
            color: "var(--ink-60)", textDecoration: "none",
            display: "inline-flex", alignItems: "center", gap: 8,
            transition: "color 200ms var(--ease-out)",
          }}
            onMouseEnter={e => e.currentTarget.style.color = "var(--ink)"}
            onMouseLeave={e => e.currentTarget.style.color = "var(--ink-60)"}
          >
            ← Journal
          </a>
          <span style={{ opacity: 0.35 }}>·</span>
          <span>{post.category}</span>
          <span style={{ opacity: 0.35 }}>·</span>
          <span>{post.date}</span>
          <span style={{ opacity: 0.35 }}>·</span>
          <span>{post.readTime}</span>
        </div>

        {/* Title */}
        <h1 style={{
          fontFamily: "var(--f-display)", fontWeight: 400,
          fontSize: "clamp(36px, 5vw, 72px)",
          lineHeight: 1.0, letterSpacing: "-0.03em", margin: "0 0 clamp(24px, 3vh, 36px)",
          fontVariationSettings: '"opsz" 144, "SOFT" 30',
        }}>
          {post.title}
        </h1>

        {/* Intro */}
        <p style={{
          fontFamily: "var(--f-display)", fontWeight: 400,
          fontSize: "clamp(20px, 1.8vw, 26px)", lineHeight: 1.5,
          letterSpacing: "-0.015em", color: "var(--ink)",
          margin: "0 0 clamp(48px, 6vh, 80px)",
          paddingBottom: "clamp(32px, 4vh, 48px)",
          borderBottom: "1px solid var(--rule)",
          fontVariationSettings: '"opsz" 24, "SOFT" 0',
        }}>
          {post.intro}
        </p>

        {/* Body */}
        <div>
          {post.body.map((block, i) => (
            <ArticleBlock key={i} block={block} index={i} />
          ))}
        </div>

        {/* Footer nav */}
        <div style={{
          marginTop: "clamp(64px, 10vh, 112px)",
          paddingTop: "clamp(32px, 4vh, 48px)",
          borderTop: "1px solid var(--rule)",
          display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: 16,
        }}>
          <a href="Journal.html" style={{
            fontFamily: "var(--f-body)", fontSize: 11, letterSpacing: "0.22em",
            textTransform: "uppercase", color: "var(--ink)",
            textDecoration: "none", borderBottom: "1px solid var(--ink)", paddingBottom: 2,
          }}>
            ← Back to Journal
          </a>
          <span style={{
            fontFamily: "var(--f-body)", fontSize: 10, letterSpacing: "0.22em",
            textTransform: "uppercase", color: "var(--ink-60)",
          }}>
            Emma Basic · {post.category}
          </span>
        </div>
      </div>
    </article>
  );
}

window.JournalPost = JournalPost;
