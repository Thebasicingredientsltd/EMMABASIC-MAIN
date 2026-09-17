/* ============================================================
   SocialFeed — official platform embeds under The Grit.
   One clipped carousel frame (not stacked widgets).
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

  const igHref = instagram.href || "";
  const igHandle = instagram.handle || socialHandleFromUrl(igHref, "@") || "@emmabasic";
  const igEmbed = instagramEmbedSrc(igHref);
  const liHref = linkedin.href || "";
  const liPosts = (Array.isArray(linkedin.posts) ? linkedin.posts : [])
    .map(linkedInEmbedSrc)
    .filter(Boolean);
  const fbEmbed = facebook.href ? facebookPluginSrc(facebook.href, 360) : "";
  const xHref = x.href || "";

  const slides = [];
  if (instagram.enabled !== false && igHref) {
    slides.push(igEmbed ? {
      id: "instagram",
      label: "Instagram",
      kind: "iframe",
      src: igEmbed,
      title: "Emma Basic on Instagram",
    } : {
      id: "instagram",
      label: "Instagram",
      kind: "empty",
      empty: {
        title: "Instagram is not connected yet",
        body: "Add the public Instagram profile link in the CRM. No password is needed if the account is public.",
        href: igHref,
        cta: "Open Instagram",
      },
    });
  }
  if (linkedin.enabled !== false && (liHref || liPosts.length)) {
    if (liPosts.length) {
      liPosts.forEach(function (src, i) {
        slides.push({
          id: "linkedin-" + i,
          label: "LinkedIn",
          kind: "iframe",
          src: src,
          title: "Emma Basic on LinkedIn",
        });
      });
    } else {
      slides.push({
        id: "linkedin",
        label: "LinkedIn",
        kind: "empty",
        empty: {
          title: "LinkedIn updates",
          body: "LinkedIn does not let websites show a full company feed automatically. Follow the company page, or paste individual post links in the CRM to display them here.",
          href: liHref,
          cta: "Open LinkedIn",
        },
      });
    }
  }
  if (facebook.enabled === true && facebook.href) {
    slides.push(fbEmbed ? {
      id: "facebook",
      label: "Facebook",
      kind: "iframe",
      src: fbEmbed,
      title: "Emma Basic on Facebook",
    } : {
      id: "facebook",
      label: "Facebook",
      kind: "empty",
      empty: {
        title: "Facebook is not connected yet",
        body: "Add the Facebook page link in the CRM to show the official timeline.",
      },
    });
  }
  if (x.enabled === true && xHref) {
    slides.push({
      id: "x",
      label: "X",
      kind: "x",
      href: xHref,
    });
  }

  const [index, setIndex] = React.useState(0);
  const pairOk = useMinWidth(640);
  const visible = slides.length ? Math.min(pairOk ? 2 : 1, slides.length) : 1;
  const maxIndex = Math.max(0, slides.length - visible);
  const safeIndex = Math.max(0, Math.min(index, maxIndex));
  const current = slides[safeIndex] || null;
  const reduced = usePrefersReducedMotion();

  React.useEffect(function () {
    if (index > maxIndex) setIndex(maxIndex);
  }, [index, maxIndex]);

  React.useEffect(function () {
    if (!current || current.kind !== "x") return;
    if (typeof window === "undefined") return;
    const existing = document.getElementById("eb-twitter-widgets");
    const load = function () {
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
  }, [current && current.kind]);

  const go = React.useCallback(function (dir) {
    if (slides.length <= visible) return;
    setIndex(function (i) {
      const next = i + dir;
      if (next < 0) return maxIndex;
      if (next > maxIndex) return 0;
      return next;
    });
  }, [slides.length, visible, maxIndex]);

  const onKeyDown = function (e) {
    if (e.key === "ArrowLeft") { e.preventDefault(); go(-1); }
    if (e.key === "ArrowRight") { e.preventDefault(); go(1); }
    if (e.key === "Home") { e.preventDefault(); setIndex(0); }
    if (e.key === "End" && slides.length) { e.preventDefault(); setIndex(maxIndex); }
  };

  const drag = React.useRef({ x: 0, active: false });
  const onPointerDown = function (e) {
    if (e.pointerType === "mouse" && e.button !== 0) return;
    drag.current = { x: e.clientX, active: true };
  };
  const onPointerUp = function (e) {
    if (!drag.current.active) return;
    const dx = e.clientX - drag.current.x;
    drag.current.active = false;
    if (Math.abs(dx) < 48) return;
    go(dx < 0 ? 1 : -1);
  };

  const eyebrow = S.eyebrow || "On social";
  const headingLine1 = S.headingLine1 || "The Grit,";
  const headingLine2 = S.headingLine2 || "online.";
  const intro = S.intro || "Kitchen notes, training days, and company news — as they happen.";

  const followLinks = [
    instagram.enabled !== false && igHref ? { label: igHandle, href: igHref } : null,
    linkedin.enabled !== false && liHref ? { label: "LinkedIn", href: liHref } : null,
    facebook.enabled === true && facebook.href ? { label: "Facebook", href: facebook.href } : null,
    x.enabled === true && xHref ? { label: "X", href: xHref } : null,
  ].filter(Boolean);

  return (
    <section className="eb-social-feed" style={{
      padding: "clamp(24px, 3.5vh, 48px) var(--pad-x) clamp(40px, 6vh, 72px)",
      borderTop: "1px solid var(--rule)",
    }}>
      <div style={{ maxWidth: "var(--maxw)", margin: "0 auto" }}>
        <Reveal>
          <div className="eb-social-head">
            <div>
              <div style={{
                fontFamily: "var(--f-body)", fontSize: 11, letterSpacing: "0.22em",
                textTransform: "uppercase", color: "var(--ink-60)", marginBottom: 12,
              }}>{eyebrow}</div>
              <h2 style={{
                fontFamily: "var(--f-display)", fontWeight: 400,
                fontSize: "clamp(32px, 4.4vw, 56px)",
                letterSpacing: "-0.03em", lineHeight: 0.95, margin: "0 0 12px",
                fontVariationSettings: '"opsz" 144, "SOFT" 30',
              }}>
                <span>{headingLine1}</span>{" "}
                <em style={{ fontStyle: "normal", fontFamily: "var(--f-body)", fontWeight: 400, letterSpacing: "-0.02em" }}>
                  {headingLine2}
                </em>
              </h2>
              <p style={{
                fontFamily: "var(--f-body)", fontSize: 16, lineHeight: 1.5,
                maxWidth: 480, margin: 0, color: "var(--ink)",
              }}>{intro}</p>
            </div>
            {followLinks.length > 0 && (
              <div style={{ display: "flex", flexWrap: "wrap", gap: 16, alignItems: "end" }}>
                {followLinks.map(function (link) {
                  return (
                    <a key={link.href} href={link.href} target="_blank" rel="noopener noreferrer" style={{
                      fontFamily: "var(--f-body)", fontSize: 11, letterSpacing: "0.22em",
                      textTransform: "uppercase", color: "var(--ink)",
                      textDecoration: "none", borderBottom: "1px solid var(--ink)",
                      paddingBottom: 2,
                    }}>{link.label} →</a>
                  );
                })}
              </div>
            )}
          </div>
        </Reveal>

        <div
          className={"eb-social-carousel" + (visible === 2 ? " is-pair" : "")}
          role="region"
          aria-roledescription="carousel"
          aria-label="Emma Basic on social media"
          tabIndex={slides.length > visible ? 0 : undefined}
          onKeyDown={onKeyDown}
        >
          {!slides.length && (
            <div className="eb-social-stage">
              <SocialEmpty
                title="Social profiles coming soon"
                body="Add Instagram, LinkedIn, Facebook, or X links in the CRM homepage editor to show them here."
              />
            </div>
          )}
          {slides.length > 0 && (
            <>
              <div
                className="eb-social-stage"
                onPointerDown={onPointerDown}
                onPointerUp={onPointerUp}
                onPointerCancel={function () { drag.current.active = false; }}
              >
                <div
                  className="eb-social-track"
                  style={{
                    transform: "translate3d(" + (-safeIndex * (100 / visible)) + "%,0,0)",
                    transition: reduced ? "none" : "transform 420ms var(--ease-out)",
                  }}
                >
                  {slides.map(function (slide, i) {
                    const inView = i >= safeIndex && i < safeIndex + visible;
                    return (
                      <div className="eb-social-slide" key={slide.id} aria-hidden={!inView}>
                        {slide.kind === "iframe" && (
                          <iframe
                            title={slide.title}
                            src={slide.src}
                            loading="lazy"
                            tabIndex={inView ? 0 : -1}
                          />
                        )}
                        {slide.kind === "x" && (
                          <a
                            className="twitter-timeline"
                            data-height="360"
                            data-chrome="noheader nofooter noborders transparent"
                            href={slide.href}
                          >Posts on X</a>
                        )}
                        {slide.kind === "empty" && <SocialEmpty {...slide.empty} />}
                      </div>
                    );
                  })}
                </div>
              </div>

              {slides.length > visible && (
                <div className="eb-social-controls">
                  <button type="button" className="eb-social-nav" aria-label="Previous" onClick={function () { go(-1); }}>←</button>
                  <div className="eb-social-dots" role="tablist" aria-label="Social slides">
                    {slides.map(function (slide, i) {
                      const on = i >= safeIndex && i < safeIndex + visible;
                      return (
                        <button
                          key={slide.id}
                          type="button"
                          role="tab"
                          aria-selected={on}
                          aria-label={slide.label + ", " + (i + 1) + " of " + slides.length}
                          className={"eb-social-dot" + (on ? " is-on" : "")}
                          onClick={function () { setIndex(Math.min(i, maxIndex)); }}
                        />
                      );
                    })}
                  </div>
                  <button type="button" className="eb-social-nav" aria-label="Next" onClick={function () { go(1); }}>→</button>
                  <span className="eb-social-status" aria-live="polite">
                    {safeIndex + 1}–{Math.min(safeIndex + visible, slides.length)} / {slides.length}
                  </span>
                </div>
              )}
            </>
          )}
        </div>
      </div>
      <style>{`
        .eb-social-head {
          display: flex;
          justify-content: space-between;
          align-items: end;
          gap: 24px;
          margin-bottom: 28px;
        }
        .eb-social-carousel { outline: none; }
        .eb-social-carousel:focus-visible { box-shadow: 0 0 0 1px var(--ink); }
        .eb-social-stage {
          height: 360px;
          overflow: hidden;
          border: 1px solid var(--rule);
          background: var(--paper-shade);
          touch-action: pan-y;
        }
        .eb-social-track {
          display: flex;
          height: 100%;
          width: 100%;
          will-change: transform;
        }
        .eb-social-slide {
          flex: 0 0 100%;
          width: 100%;
          height: 100%;
          overflow: hidden;
          box-sizing: border-box;
        }
        .eb-social-carousel.is-pair .eb-social-slide { flex-basis: 50%; width: 50%; }
        .eb-social-carousel.is-pair .eb-social-slide + .eb-social-slide {
          border-left: 1px solid var(--rule);
        }
        .eb-social-slide iframe,
        .eb-social-slide .twitter-timeline {
          width: 100%;
          height: 540px;
          border: 0;
          display: block;
          background: var(--paper-shade);
          pointer-events: auto;
        }
        .eb-social-controls {
          display: flex;
          align-items: center;
          gap: 14px;
          margin-top: 16px;
        }
        .eb-social-nav {
          font-family: var(--f-body);
          font-size: 16px;
          line-height: 1;
          color: var(--ink);
          background: none;
          border: 0;
          padding: 6px 4px;
          cursor: pointer;
        }
        .eb-social-nav:active { transform: scale(0.97); }
        .eb-social-dots { display: flex; gap: 8px; align-items: center; }
        .eb-social-dot {
          width: 7px;
          height: 7px;
          padding: 0;
          border: 0;
          border-radius: 50%;
          background: var(--ink);
          opacity: 0.22;
          cursor: pointer;
        }
        .eb-social-dot.is-on { opacity: 1; }
        .eb-social-status {
          margin-left: auto;
          font-family: var(--f-body);
          font-size: 11px;
          letter-spacing: 0.18em;
          text-transform: uppercase;
          color: var(--ink-60);
        }
        @media (max-width: 800px) {
          .eb-social-head { flex-direction: column; align-items: start; margin-bottom: 20px; }
          .eb-social-stage { height: 300px; }
        }
        @media (prefers-reduced-motion: reduce) {
          .eb-social-track { transition: none !important; }
          .eb-social-nav:active { transform: none; }
        }
      `}</style>
    </section>
  );
}

function SocialEmpty({ title, body, href, cta }) {
  return (
    <div style={{
      height: "100%",
      boxSizing: "border-box",
      padding: "28px 24px",
      display: "flex",
      flexDirection: "column",
      justifyContent: "center",
    }}>
      <div style={{
        fontFamily: "var(--f-display)", fontSize: 24, fontWeight: 400,
        letterSpacing: "-0.03em", marginBottom: 10,
      }}>{title}</div>
      <p style={{
        fontFamily: "var(--f-body)", fontSize: 15, lineHeight: 1.5, margin: "0 0 20px",
        maxWidth: 420,
      }}>{body}</p>
      {href && cta && (
        <a href={href} target="_blank" rel="noopener noreferrer" style={{
          fontFamily: "var(--f-body)", fontSize: 11, letterSpacing: "0.22em",
          textTransform: "uppercase", color: "var(--ink)",
          textDecoration: "none", borderBottom: "1px solid var(--ink)",
          paddingBottom: 2,
          alignSelf: "flex-start",
        }}>{cta} →</a>
      )}
    </div>
  );
}

function useMinWidth(px) {
  const [matches, setMatches] = React.useState(true);
  React.useEffect(function () {
    if (typeof window === "undefined" || !window.matchMedia) return;
    const mq = window.matchMedia("(min-width: " + px + "px)");
    const apply = function () { setMatches(!!mq.matches); };
    apply();
    if (mq.addEventListener) mq.addEventListener("change", apply);
    else if (mq.addListener) mq.addListener(apply);
    return function () {
      if (mq.removeEventListener) mq.removeEventListener("change", apply);
      else if (mq.removeListener) mq.removeListener(apply);
    };
  }, [px]);
  return matches;
}

function usePrefersReducedMotion() {
  const [reduced, setReduced] = React.useState(false);
  React.useEffect(function () {
    if (typeof window === "undefined" || !window.matchMedia) return;
    const mq = window.matchMedia("(prefers-reduced-motion: reduce)");
    const apply = function () { setReduced(!!mq.matches); };
    apply();
    if (mq.addEventListener) mq.addEventListener("change", apply);
    else if (mq.addListener) mq.addListener(apply);
    return function () {
      if (mq.removeEventListener) mq.removeEventListener("change", apply);
      else if (mq.removeListener) mq.removeListener(apply);
    };
  }, []);
  return reduced;
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

function facebookPluginSrc(href, height) {
  try {
    const u = new URL(String(href || "").trim());
    const h = height || 360;
    return "https://www.facebook.com/plugins/page.php?href=" +
      encodeURIComponent(u.toString()) +
      "&tabs=timeline&width=500&height=" + h +
      "&small_header=true&adapt_container_width=true&hide_cover=false&show_facepile=false";
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
