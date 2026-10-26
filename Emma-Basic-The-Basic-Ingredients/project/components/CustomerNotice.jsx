/* ============================================================
   CustomerNotice — homepage recall / customer message.
   Sits under the fixed nav, before the hero, on paper.
   Hidden when the CRM marks it off, or when it has no copy.
   ============================================================ */
function CustomerNotice() {
  const N = (typeof window !== "undefined" && window.EB_HOME && window.EB_HOME.notice) || {};
  if (N.visible === false) return null;

  const title = String(N.title || "").trim();
  const body = String(N.body || "").trim();
  const eyebrow = String(N.eyebrow || "").trim() || "Customer notice";
  const linkLabel = String(N.linkLabel || "").trim() || "Read the full notice";
  const href = String(N.href || "").trim();
  if (!title && !body) return null;

  const safeHref = /^(https?:\/\/|mailto:|assets\/|\/)/i.test(href) && !/^\/\//.test(href)
    ? href
    : "";

  return (
    <section
      className="eb-notice"
      role="region"
      aria-label={eyebrow}
      style={{
        background: "var(--paper-bright)",
        color: "var(--ink)",
        borderBottom: "1px solid var(--ink)",
        padding: "112px var(--pad-x) 36px",
      }}
    >
      <style>{`
        .eb-notice__grid {
          max-width: 760px;
          margin: 0 auto;
          display: flex;
          flex-direction: column;
          align-items: flex-start;
          gap: 14px;
        }
        .eb-notice__title {
          font-family: var(--f-display);
          font-weight: 400;
          font-size: clamp(28px, 3vw, 44px);
          line-height: 1.05;
          letter-spacing: -0.02em;
          margin: 0;
        }
        .eb-notice__body {
          font-family: var(--f-body);
          font-weight: 400;
          font-size: 16px;
          line-height: 1.55;
          margin: 12px 0 0;
          max-width: 62ch;
          color: var(--ink-90);
        }
        .eb-notice__link {
          font-family: var(--f-mono);
          font-size: 11px;
          letter-spacing: 0.18em;
          text-transform: uppercase;
          color: var(--ink);
          text-decoration: none;
          border-bottom: 1px solid var(--ink);
          padding-bottom: 4px;
          white-space: nowrap;
          min-height: 44px;
          display: inline-flex;
          align-items: center;
        }
        .eb-notice__link:hover { color: var(--ink-60); border-bottom-color: var(--ink-60); }
        .eb-notice__link:focus-visible { outline: 2px solid var(--ink); outline-offset: 4px; }
        @media (max-width: 800px) {
          .eb-notice { padding-top: 104px !important; padding-bottom: 28px !important; }
          .eb-notice__grid { max-width: none; }
        }
      `}</style>
      <div className="eb-notice__grid">
        <p className="eyebrow" style={{ margin: 0, color: "var(--ink)" }}>{eyebrow}</p>
        <div>
          {title ? <h2 className="eb-notice__title">{title}</h2> : null}
          {body ? <p className="eb-notice__body">{body}</p> : null}
        </div>
        {safeHref ? (
          <a className="eb-notice__link" href={safeHref} target="_blank" rel="noopener noreferrer">
            {linkLabel}
          </a>
        ) : null}
      </div>
    </section>
  );
}

window.CustomerNotice = CustomerNotice;
