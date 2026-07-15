/* ============================================================
   FeedbackPopup -- appears after 3 minutes, once per session.
   Dismissed state persists in sessionStorage so it won't
   reappear on the same visit if the user navigates pages.
   ============================================================ */

function FeedbackPopup() {
  const [visible, setVisible] = React.useState(false);
  const [animOut, setAnimOut] = React.useState(false);
  const [name, setName] = React.useState("");
  const [message, setMessage] = React.useState("");
  const [sent, setSent] = React.useState(false);

  React.useEffect(() => {
    if (sessionStorage.getItem("eb-feedback-dismissed")) return;
    const t = setTimeout(() => setVisible(true), 3 * 60 * 1000);
    return () => clearTimeout(t);
  }, []);

  function dismiss() {
    setAnimOut(true);
    setTimeout(() => {
      setVisible(false);
      setAnimOut(false);
    }, 400);
    sessionStorage.setItem("eb-feedback-dismissed", "1");
  }

  function handleSend(e) {
    e.preventDefault();
    if (!message.trim()) return;
    const subject = encodeURIComponent("Product Suggestion from " + (name.trim() || "a customer"));
    const body = encodeURIComponent(
      (name.trim() ? "Name: " + name.trim() + "\n\n" : "") +
      message.trim()
    );
    window.location.href = `mailto:boris@thebasicingredients.com?subject=${subject}&body=${body}`;
    setSent(true);
    setTimeout(dismiss, 2000);
  }

  if (!visible) return null;

  return (
    <div style={{
      position: "fixed", bottom: 32, right: 32, zIndex: 9000,
      width: "min(420px, calc(100vw - 48px))",
      background: "var(--paper, #F6F6F6)",
      border: "1px solid var(--ink, #1a1a1a)",
      boxShadow: "0 12px 48px rgba(10,10,10,0.14), 0 2px 8px rgba(10,10,10,0.06)",
      opacity: animOut ? 0 : 1,
      transform: animOut ? "translateY(16px)" : "translateY(0)",
      transition: "opacity 400ms var(--ease-out, cubic-bezier(0.25,0,0,1)), transform 400ms var(--ease-out, cubic-bezier(0.25,0,0,1))",
      animation: "eb-popup-in 500ms var(--ease-out, cubic-bezier(0.25,0,0,1)) both",
    }}>
      <style>{`
        @keyframes eb-popup-in {
          from { opacity: 0; transform: translateY(24px); }
          to   { opacity: 1; transform: translateY(0); }
        }
      `}</style>

      {/* Header */}
      <div style={{
        display: "flex", justifyContent: "space-between", alignItems: "flex-start",
        padding: "22px 22px 0",
      }}>
        <span style={{
          fontFamily: "var(--f-body, sans-serif)", fontSize: 9.5, letterSpacing: "0.22em",
          textTransform: "uppercase", color: "var(--ink-60, #888)",
        }}>We'd love to hear from you</span>
        <button onClick={dismiss} style={{
          background: "none", border: "none", cursor: "pointer", padding: "0 0 0 12px",
          fontFamily: "var(--f-mono, monospace)", fontSize: 16, color: "var(--ink-60, #888)",
          lineHeight: 1,
        }} aria-label="Close">&times;</button>
      </div>

      <div style={{ padding: "14px 22px 24px" }}>
        {sent ? (
          <div style={{ padding: "12px 0" }}>
            <p style={{
              fontFamily: "var(--f-display, serif)", fontStyle: "italic",
              fontSize: 18, lineHeight: 1.4, margin: 0,
              color: "var(--ink, #1a1a1a)",
            }}>
              Thank you &mdash; we read every suggestion.
            </p>
          </div>
        ) : (
          <>
            <p style={{
              fontFamily: "var(--f-display, serif)", fontStyle: "italic",
              fontSize: "clamp(17px, 1.5vw, 20px)", lineHeight: 1.4,
              margin: "0 0 18px", color: "var(--ink, #1a1a1a)",
              fontVariationSettings: '"opsz" 24, "SOFT" 60',
            }}>
              Feels like something's missing? Tell us what you'd love to see &mdash; we read every message and genuinely want to get it right for you.
            </p>

            <form onSubmit={handleSend} style={{ display: "grid", gap: 12 }}>
              <input
                type="text"
                placeholder="Your name"
                value={name}
                onChange={e => setName(e.target.value)}
                style={{
                  fontFamily: "var(--f-body, sans-serif)", fontSize: 14,
                  background: "transparent",
                  border: "none", borderBottom: "1px solid var(--rule, #d8d8d8)",
                  outline: "none", padding: "6px 0",
                  color: "var(--ink, #1a1a1a)", width: "100%",
                }}
              />
              <textarea
                placeholder="Something you'd love to see from us..."
                value={message}
                onChange={e => setMessage(e.target.value)}
                rows={3}
                required
                style={{
                  fontFamily: "var(--f-body, sans-serif)", fontSize: 14, lineHeight: 1.5,
                  background: "transparent", resize: "none",
                  border: "none", borderBottom: "1px solid var(--rule, #d8d8d8)",
                  outline: "none", padding: "6px 0",
                  color: "var(--ink, #1a1a1a)", width: "100%",
                }}
              />
              <div style={{ display: "flex", justifyContent: "flex-end", paddingTop: 4 }}>
                <button type="submit" style={{
                  fontFamily: "var(--f-body, sans-serif)", fontSize: 10.5, letterSpacing: "0.22em",
                  textTransform: "uppercase",
                  background: "var(--ink, #1a1a1a)", color: "var(--paper, #F6F6F6)",
                  border: "none", cursor: "pointer",
                  padding: "10px 20px",
                }}>
                  Send &rarr;
                </button>
              </div>
            </form>
          </>
        )}
      </div>
    </div>
  );
}

/* Self-mount into its own div so it works on every page */
const _fbDiv = document.createElement("div");
document.body.appendChild(_fbDiv);
ReactDOM.createRoot(_fbDiv).render(<FeedbackPopup />);
