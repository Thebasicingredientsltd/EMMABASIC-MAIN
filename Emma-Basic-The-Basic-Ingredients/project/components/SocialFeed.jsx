/* ============================================================
   SocialFeed — official platform embeds under The Grit.
   Instagram / Facebook / X use their public profile plugins.
   LinkedIn has no public company-timeline embed; we show official
   per-post embeds when URLs are pasted in the CRM.
   ============================================================ */

function SocialFeed() {
  const S = (typeof window !== "undefined" && window.EB_HOME && window.EB_HOME.social) || {};
  if (S.visible === false) return null;

  const instagram = S.instagram || {};
  const linkedin = S.linkedin || {};
  const facebook = S.facebook || {};
  const x = S.x || {};

  const platforms = [];
  if (instagram.enabled !== false && instagram.href) {
    platforms.push({ id: "instagram", label: "Instagram" });
  }
  if (linkedin.enabled !== false && (linkedin.href || (linkedin.posts || []).length)) {
    platforms.push({ id: "linkedin", label: "LinkedIn" });
  }
  if (facebook.enabled === true && facebook.href) {
    platforms.push({ id: "facebook", label: "Facebook" });
  }
  if (x.enabled === true && x.href) {
    platforms.push({ id: "x", label: "X" });
  }

  const [active, setActive] = React.useState(platforms[0] ? platforms[0].id : "");
  const current = platforms.some((p) => p.id === active) ? active : (platforms[0] && platforms[0].id) || "";

  React.useEffect(() => {
    if (current !== "x") return;
    if (typeof window === "undefined") return;
    const existing = document.getElementById("eb-twitter-widgets");
    const load = () => {
      if (window.twttr && window.twttr.widgets) window.twttr.widgets.load();
    };
    if (existing) {
      load();
      return;
    }
    const script = document.createElement("script");
    script.id = "eb-twitter-widgets";
    script.src = "https://platform.twitter.com/widgets.js";
    script.async = true;
    script.onload = load;
    document.body.appendChild(script);
  }, [current]);

  const eyebrow = S.eyebrow || "On social";
  const headingLine1 = S.headingLine1 || "The Grit,";
  const headingLine2 = S.headingLine2 || "online.";
  const intro = S.intro || "Kitchen notes, training days, and company news — as they happen.";

  const igHref = instagram.href || "";
  const igHandle = instagram.handle || socialHandleFromUrl(igHref, "@") || "@emmabasic";
  const igEmbed = instagramEmbedSrc(igHref);
  const liHref = linkedin.href || "";
  const liPosts = (Array.isArray(linkedin.posts) ? linkedin.posts : [])
    .map(linkedInEmbedSrc)
    .filter(Boolean);
  const fbEmbed = facebook.href ? facebookPluginSrc(facebook.href) : "";
  const xHref = x.href || "";

  const followLinks = [
    instagram.enabled !== false && igHref ? { label: igHandle, href: igHref } : null,
    linkedin.enabled !== false && liHref ? { label: "LinkedIn", href: liHref } : null,
    facebook.enabled === true && facebook.href ? { label: "Facebook", href: facebook.href } : null,
    x.enabled === true && xHref ? { label: "X", href: xHref } : null,
  ].filter(Boolean);

  return (
    <section className="eb-social-feed" style={{
      padding: "clamp(28px, 4vh, 56px) var(--pad-x) clamp(48px, 7vh, 88px)",
      borderTop: "1px solid var(--rule)",
    }}>
      <div style={{ maxWidth: "var(--maxw)", margin: "0 auto" }}>
        <div className="eb-social-layout" style={{
          display: "grid",
          gridTemplateColumns: "minmax(0, 0.9fr) minmax(0, 1.1fr)",
          gap: "clamp(32px, 5vw, 72px)",
          alignItems: "start",
        }}>
          <Reveal>
            <div>
              <div style={{
                fontFamily: "var(--f-body)", fontSize: 11, letterSpacing: "0.22em",
                textTransform: "uppercase", color: "var(--ink-60)", marginBottom: 16,
              }}>{eyebrow}</div>
              <h2 style={{
                fontFamily: "var(--f-display)", fontWeight: 400,
                fontSize: "clamp(36px, 5vw, 72px)",
                letterSpacing: "-0.03em", lineHeight: 0.95, margin: "0 0 20px",
                fontVariationSettings: '"opsz" 144, "SOFT" 30',
              }}>
                <span>{headingLine1}</span><br/>
                <em style={{ fontStyle: "normal", fontFamily: "var(--f-body)", fontWeight: 400, letterSpacing: "-0.02em" }}>
                  {headingLine2}
                </em>
              </h2>
              <p style={{
                fontFamily: "var(--f-body)", fontSize: 17, lineHeight: 1.55,
                maxWidth: 420, margin: "0 0 28px", color: "var(--ink)",
              }}>{intro}</p>

              {platforms.length > 1 && (
                <div role="tablist" aria-label="Social platforms" style={{
                  display: "flex", flexWrap: "wrap", gap: 18, marginBottom: 28,
                }}>
                  {platforms.map((p) => {
                    const on = p.id === current;
                    return (
                      <button
                        key={p.id}
                        type="button"
                        role="tab"
                        aria-selected={on}
                        onClick={() => setActive(p.id)}
                        style={{
                          fontFamily: "var(--f-body)", fontSize: 11, letterSpacing: "0.22em",
                          textTransform: "uppercase", background: "none", border: 0,
                          padding: "0 0 4px", cursor: "pointer", color: "var(--ink)",
                          borderBottom: on ? "1px solid var(--ink)" : "1px solid transparent",
                          opacity: on ? 1 : 0.45,
                        }}
                      >{p.label}</button>
                    );
                  })}
                </div>
              )}

              {followLinks.length > 0 && (
                <div style={{ display: "flex", flexWrap: "wrap", gap: 20 }}>
                  {followLinks.map((link) => (
                    <a key={link.href} href={link.href} target="_blank" rel="noopener noreferrer" style={{
                      fontFamily: "var(--f-body)", fontSize: 11, letterSpacing: "0.22em",
                      textTransform: "uppercase", color: "var(--ink)",
                      textDecoration: "none", borderBottom: "1px solid var(--ink)",
                      paddingBottom: 2,
                    }}>{link.label} →</a>
                  ))}
                </div>
              )}
            </div>
          </Reveal>

          <div style={{ minHeight: 420 }}>
            {!platforms.length && (
              <SocialEmpty
                title="Social profiles coming soon"
                body="Add Instagram, LinkedIn, Facebook, or X links in the CRM homepage editor to show them here."
              />
            )}
            {current === "instagram" && (
              igEmbed ? (
                <iframe
                  title="Emma Basic on Instagram"
                  src={igEmbed}
                  loading="lazy"
                  style={embedFrameStyle}
                />
              ) : (
                <SocialEmpty
                  title="Instagram is not connected yet"
                  body="Add the public Instagram profile link in the CRM. No password is needed if the account is public."
                  href={igHref}
                  cta="Open Instagram"
                />
              )
            )}
            {current === "linkedin" && (
              liPosts.length ? (
                <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
                  {liPosts.slice(0, 3).map((src) => (
                    <iframe
                      key={src}
                      title="Emma Basic on LinkedIn"
                      src={src}
                      loading="lazy"
                      style={{ ...embedFrameStyle, minHeight: 520, height: 520 }}
                    />
                  ))}
                </div>
              ) : (
                <SocialEmpty
                  title="LinkedIn updates"
                  body="LinkedIn does not let websites show a full company feed automatically. Follow the company page, or paste individual post links in the CRM to display them here."
                  href={liHref}
                  cta="Open LinkedIn"
                />
              )
            )}
            {current === "facebook" && (
              fbEmbed ? (
                <iframe
                  title="Emma Basic on Facebook"
                  src={fbEmbed}
                  loading="lazy"
                  style={{ ...embedFrameStyle, minHeight: 620, height: 620 }}
                />
              ) : (
                <SocialEmpty
                  title="Facebook is not connected yet"
                  body="Add the Facebook page link in the CRM to show the official timeline."
                />
              )
            )}
            {current === "x" && (
              xHref ? (
                <a
                  className="twitter-timeline"
                  data-height="620"
                  data-chrome="noheader nofooter noborders transparent"
                  href={xHref}
                >Posts on X</a>
              ) : (
                <SocialEmpty
                  title="X is not connected yet"
                  body="Add the X profile link in the CRM to show the official timeline."
                />
              )
            )}
          </div>
        </div>
      </div>
      <style>{`
        .eb-social-feed iframe { background: var(--paper-shade); }
        @media (max-width: 800px) {
          .eb-social-layout { grid-template-columns: 1fr !important; }
        }
      `}</style>
    </section>
  );
}

const embedFrameStyle = {
  width: "100%",
  maxWidth: 540,
  minHeight: 620,
  height: 620,
  border: "1px solid var(--rule)",
  display: "block",
  background: "var(--paper-shade)",
};

function SocialEmpty({ title, body, href, cta }) {
  return (
    <div style={{
      maxWidth: 540,
      minHeight: 280,
      border: "1px solid var(--rule)",
      padding: "36px 32px",
      background: "var(--paper-shade)",
    }}>
      <div style={{
        fontFamily: "var(--f-display)", fontSize: 28, fontWeight: 400,
        letterSpacing: "-0.03em", marginBottom: 12,
      }}>{title}</div>
      <p style={{
        fontFamily: "var(--f-body)", fontSize: 16, lineHeight: 1.5, margin: "0 0 24px",
        maxWidth: 420,
      }}>{body}</p>
      {href && cta && (
        <a href={href} target="_blank" rel="noopener noreferrer" style={{
          fontFamily: "var(--f-body)", fontSize: 11, letterSpacing: "0.22em",
          textTransform: "uppercase", color: "var(--ink)",
          textDecoration: "none", borderBottom: "1px solid var(--ink)",
          paddingBottom: 2,
        }}>{cta} →</a>
      )}
    </div>
  );
}

function socialHandleFromUrl(href, prefix) {
  const name = firstPathSegment(href);
  if (!name || name === "embed") return "";
  return prefix + name.replace(/^@/, "");
}

function instagramEmbedSrc(href) {
  const clean = String(href || "").trim();
  if (!clean) return "";
  try {
    const u = new URL(clean);
    if (!/instagram\.com$/i.test(u.hostname.replace(/^www\./, ""))) return "";
    const parts = u.pathname.split("/").filter(Boolean);
    const user = parts.find((p) => p !== "embed" && p !== "reel" && p !== "p");
    if (!user) return "";
    return "https://www.instagram.com/" + user + "/embed";
  } catch {
    return "";
  }
}

function linkedInEmbedSrc(url) {
  const raw = String(url || "").trim();
  if (!raw) return "";
  if (raw.indexOf("/embed/feed/update/") !== -1) return raw.split("?")[0];
  const urn = raw.match(/urn:li:(ugcPost|share|activity):(\d+)/);
  if (urn) return "https://www.linkedin.com/embed/feed/update/urn:li:" + urn[1] + ":" + urn[2];
  const activity = raw.match(/activity-(\d+)/);
  if (activity) return "https://www.linkedin.com/embed/feed/update/urn:li:activity:" + activity[1];
  return "";
}

function facebookPluginSrc(href) {
  try {
    const u = new URL(String(href || "").trim());
    return "https://www.facebook.com/plugins/page.php?href=" +
      encodeURIComponent(u.toString()) +
      "&tabs=timeline&width=500&height=620&small_header=true&adapt_container_width=true&hide_cover=false&show_facepile=false";
  } catch {
    return "";
  }
}

function firstPathSegment(href) {
  try {
    const u = new URL(String(href || "").trim());
    return u.pathname.split("/").filter(Boolean)[0] || "";
  } catch {
    return "";
  }
}
