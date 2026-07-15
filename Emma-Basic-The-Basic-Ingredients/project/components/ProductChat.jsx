/* ============================================================
   ProductChat — AI-powered product assistant via Claude API.
   Calls /api/chat on the Vercel proxy. Falls back gracefully.
   ============================================================ */

(function () {

  // ── Replace this with your Vercel deployment URL once deployed ──
  const PROXY_URL = "https://emma-basic-chat.vercel.app/api/chat";

  const SUGGESTIONS = [
    "What goes well with sushi rice?",
    "Tell me about your matcha",
    "Which products are gluten free?",
    "How do I contact you?",
  ];

  function ProductChat() {
    const [open, setOpen]         = React.useState(false);
    const [expanded, setExpanded] = React.useState(false);
    const [input, setInput]       = React.useState("");
    const [loading, setLoading]   = React.useState(false);
    const [messages, setMessages] = React.useState([
      { from: "bot", text: "Hi! I'm the Emma Basic assistant. Ask me anything about our products — ingredients, what they pair with, nutrition, or where to find us." }
    ]);
    const bottomRef = React.useRef(null);
    const inputRef  = React.useRef(null);

    React.useEffect(() => {
      if (bottomRef.current) bottomRef.current.scrollIntoView({ behavior: "smooth" });
    }, [messages, loading]);

    React.useEffect(() => {
      if (open && inputRef.current) inputRef.current.focus();
    }, [open]);

    async function send(overrideText) {
      const text = (overrideText || input).trim();
      if (!text || loading) return;

      const userMsg = { from: "user", text };
      const history = [...messages, userMsg];
      setMessages(history);
      setInput("");
      setLoading(true);

      try {
        const res = await fetch(PROXY_URL, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ messages: history }),
        });
        const data = await res.json();
        const reply = data.reply || "Sorry, I couldn't get a response just now. Please try again.";
        setMessages(prev => [...prev, { from: "bot", text: reply }]);
      } catch {
        setMessages(prev => [...prev, { from: "bot", text: "Sorry, something went wrong. Please try again in a moment." }]);
      } finally {
        setLoading(false);
      }
    }

    function onKey(e) {
      if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(); }
    }

    const showSuggestions = messages.length <= 1;

    return (
      <>
        {/* Floating button */}
        <button
          onClick={() => setOpen(o => !o)}
          title="Ask about our products"
          style={{
            position: "fixed", bottom: 28, right: 28, zIndex: 900,
            width: 52, height: 52, borderRadius: "50%",
            background: "var(--ink)", color: "var(--paper)",
            border: "none", cursor: "pointer",
            display: "flex", alignItems: "center", justifyContent: "center",
            boxShadow: "0 4px 20px rgba(10,10,10,0.28)",
            transition: "transform 220ms var(--ease-out), background 180ms",
            transform: open ? "scale(0.92)" : "scale(1)",
          }}
          onMouseEnter={e => e.currentTarget.style.background = "#222"}
          onMouseLeave={e => e.currentTarget.style.background = "var(--ink)"}
        >
          {open
            ? <svg width="18" height="18" viewBox="0 0 18 18" fill="none"><path d="M2 2l14 14M16 2L2 16" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/></svg>
            : <svg width="20" height="20" viewBox="0 0 24 24" fill="none"><path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z" stroke="currentColor" strokeWidth="1.8" strokeLinejoin="round"/></svg>
          }
        </button>

        {/* Chat panel */}
        {open && (
          <div style={{
            position: "fixed",
            bottom: expanded ? 0 : 90,
            right: expanded ? 0 : 28,
            left: expanded ? 0 : "auto",
            top: expanded ? 0 : "auto",
            zIndex: 901,
            width: expanded ? "100vw" : "clamp(300px, 90vw, 420px)",
            maxHeight: expanded ? "100vh" : "clamp(420px, 75vh, 620px)",
            height: expanded ? "100vh" : "auto",
            background: "var(--paper)",
            border: expanded ? "none" : "1px solid var(--rule)",
            boxShadow: expanded ? "none" : "0 8px 48px rgba(10,10,10,0.18)",
            display: "flex", flexDirection: "column",
            fontFamily: "var(--f-body)", fontSize: expanded ? 15 : 13,
            transition: "all 280ms var(--ease-out)",
            animation: "eb-chat-in 220ms var(--ease-out) both",
          }}>

            {/* Header */}
            <div style={{
              padding: "14px 18px",
              borderBottom: "1px solid var(--rule)",
              display: "flex", alignItems: "center", gap: 10,
              flexShrink: 0,
            }}>
              <div style={{ width: 8, height: 8, borderRadius: "50%", background: "#4caf50", flexShrink: 0 }} />
              <div style={{ flex: 1 }}>
                <div style={{ fontFamily: "var(--f-body)", fontSize: 10, letterSpacing: "0.22em", textTransform: "uppercase", color: "var(--ink)" }}>Emma Basic</div>
                <div style={{ fontFamily: "var(--f-body)", fontSize: 9, letterSpacing: "0.14em", textTransform: "uppercase", color: "var(--ink-40)", marginTop: 1 }}>Product Assistant</div>
              </div>
              <button
                onClick={() => setExpanded(e => !e)}
                title={expanded ? "Collapse" : "Expand"}
                style={{
                  background: "transparent", border: "1px solid var(--rule)",
                  cursor: "pointer", width: 28, height: 28,
                  display: "flex", alignItems: "center", justifyContent: "center",
                  color: "var(--ink-60)", flexShrink: 0,
                  transition: "border-color 150ms, color 150ms",
                }}
                onMouseEnter={e => { e.currentTarget.style.borderColor = "var(--ink)"; e.currentTarget.style.color = "var(--ink)"; }}
                onMouseLeave={e => { e.currentTarget.style.borderColor = "var(--rule)"; e.currentTarget.style.color = "var(--ink-60)"; }}
              >
                {expanded
                  ? <svg width="12" height="12" viewBox="0 0 12 12" fill="none"><path d="M2 2l8 8M10 2L2 10" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/></svg>
                  : <svg width="12" height="12" viewBox="0 0 12 12" fill="none"><path d="M1 1h4M1 1v4M11 1H7M11 1v4M1 11h4M1 11V7M11 11H7M11 11V7" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/></svg>
                }
              </button>
            </div>

            {/* Messages */}
            <div style={{
              flex: 1, overflowY: "auto", padding: "16px 14px",
              display: "flex", flexDirection: "column", gap: 10,
              scrollbarWidth: "thin",
            }}>
              {messages.map((m, i) => (
                <div key={i} style={{ display: "flex", justifyContent: m.from === "user" ? "flex-end" : "flex-start" }}>
                  <div style={{
                    maxWidth: "82%",
                    padding: "9px 13px",
                    background: m.from === "user" ? "var(--ink)" : "var(--paper-shade)",
                    color: m.from === "user" ? "var(--paper)" : "var(--ink)",
                    fontFamily: "var(--f-body)", fontSize: "inherit", lineHeight: 1.35,
                    whiteSpace: "pre-wrap",
                    borderRadius: m.from === "user" ? "14px 14px 2px 14px" : "14px 14px 14px 2px",
                  }}>
                    {m.text}
                  </div>
                </div>
              ))}

              {/* Typing indicator */}
              {loading && (
                <div style={{ display: "flex", justifyContent: "flex-start" }}>
                  <div style={{
                    padding: "10px 14px",
                    background: "var(--paper-shade)",
                    borderRadius: "14px 14px 14px 2px",
                    display: "flex", gap: 4, alignItems: "center",
                  }}>
                    {[0, 1, 2].map(i => (
                      <div key={i} style={{
                        width: 6, height: 6, borderRadius: "50%",
                        background: "var(--ink-40)",
                        animation: `eb-dot-bounce 1.2s ease-in-out ${i * 0.2}s infinite`,
                      }} />
                    ))}
                  </div>
                </div>
              )}

              {/* Quick suggestion pills */}
              {showSuggestions && (
                <div style={{ display: "flex", flexWrap: "wrap", gap: 6, marginTop: 4 }}>
                  {SUGGESTIONS.map((s, i) => (
                    <button key={i} onClick={() => send(s)} style={{
                      fontFamily: "var(--f-body)", fontSize: 9.5, letterSpacing: "0.22em",
                      padding: "5px 10px",
                      background: "none",
                      border: "1px solid var(--rule-strong)",
                      color: "var(--ink-60)",
                      cursor: "pointer",
                      borderRadius: 20,
                      transition: "border-color 150ms, color 150ms",
                    }}
                      onMouseEnter={e => { e.currentTarget.style.borderColor = "var(--ink)"; e.currentTarget.style.color = "var(--ink)"; }}
                      onMouseLeave={e => { e.currentTarget.style.borderColor = "var(--rule-strong)"; e.currentTarget.style.color = "var(--ink-60)"; }}
                    >{s}</button>
                  ))}
                </div>
              )}

              <div ref={bottomRef} />
            </div>

            {/* Input */}
            <div style={{
              borderTop: "1px solid var(--rule)",
              padding: "10px 12px",
              display: "flex", gap: 8, alignItems: "flex-end",
            }}>
              <textarea
                ref={inputRef}
                value={input}
                onChange={e => setInput(e.target.value)}
                onKeyDown={onKey}
                placeholder="Ask about a product…"
                rows={1}
                style={{
                  flex: 1, resize: "none", border: "none", outline: "none",
                  background: "transparent",
                  fontFamily: "var(--f-body)", fontSize: 13, lineHeight: 1.5,
                  color: "var(--ink)",
                  paddingTop: 4,
                  maxHeight: 80, overflowY: "auto",
                }}
              />
              <button
                onClick={() => send()}
                disabled={!input.trim() || loading}
                style={{
                  width: 34, height: 34, borderRadius: "50%", flexShrink: 0,
                  background: (input.trim() && !loading) ? "var(--ink)" : "var(--rule)",
                  border: "none", cursor: (input.trim() && !loading) ? "pointer" : "default",
                  display: "flex", alignItems: "center", justifyContent: "center",
                  transition: "background 160ms",
                }}
              >
                <svg width="14" height="14" viewBox="0 0 16 16" fill="none">
                  <path d="M2 8h12M9 3l5 5-5 5" stroke={(input.trim() && !loading) ? "#f6f4ef" : "#aaa"} strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
              </button>
            </div>

            {/* Disclaimer */}
            <div style={{
              padding: "6px 14px 10px",
              fontFamily: "var(--f-body)", fontSize: 8.5, letterSpacing: "0.22em",
              color: "var(--ink-40)", textAlign: "center",
            }}>
              Product info only · Not a substitute for label advice
            </div>
          </div>
        )}

        <style>{`
          @keyframes eb-chat-in {
            from { opacity: 0; transform: translateY(12px) scale(0.97); }
            to   { opacity: 1; transform: translateY(0) scale(1); }
          }
          @keyframes eb-dot-bounce {
            0%, 80%, 100% { transform: translateY(0); opacity: 0.4; }
            40% { transform: translateY(-5px); opacity: 1; }
          }
        `}</style>
      </>
    );
  }

  window.ProductChat = ProductChat;

})();
