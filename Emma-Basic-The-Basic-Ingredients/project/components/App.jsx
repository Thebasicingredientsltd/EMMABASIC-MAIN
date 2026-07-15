/* ============================================================
   App — new composition (gallery-boutique direction)
   ============================================================ */
function App() {
  const [state, setStateRaw] = React.useState(() => {
    try {
      const s = JSON.parse(localStorage.getItem("emma-basic-state") || "{}");
      return { serif: "fraunces", paper: "warm", ...s };
    } catch { return { serif: "fraunces", paper: "warm" }; }
  });
  const setState = (patch) => setStateRaw(s => {
    const next = { ...s, ...patch };
    try { localStorage.setItem("emma-basic-state", JSON.stringify(next)); } catch {}
    return next;
  });

  const [openId, setOpenId] = React.useState(null);
  const [editMode, setEditMode] = React.useState(false);

  React.useEffect(() => {
    const onMsg = (e) => {
      if (!e.data || typeof e.data !== "object") return;
      if (e.data.type === "__activate_edit_mode") setEditMode(true);
      if (e.data.type === "__deactivate_edit_mode") setEditMode(false);
    };
    window.addEventListener("message", onMsg);
    window.parent.postMessage({ type: "__edit_mode_available" }, "*");
    return () => window.removeEventListener("message", onMsg);
  }, []);

  React.useEffect(() => {
    const map = {
      fraunces: '"Fraunces", "Times New Roman", serif',
      playfair: '"Playfair Display", "Times New Roman", serif',
      dmserif:  '"DM Serif Display", "Times New Roman", serif',
    };
    document.documentElement.style.setProperty("--f-display", map[state.serif] || map.fraunces);
  }, [state.serif]);

  React.useEffect(() => {
    const map = {
      warm:   { paper: "#F6F6F6", shade: "#ECECEC" },
      cool:   { paper: "#F0F1EE", shade: "#E3E5E1" },
      bright: { paper: "#FBFAF7", shade: "#F0EEE8" },
    };
    const c = map[state.paper] || map.warm;
    document.documentElement.style.setProperty("--paper", c.paper);
    document.documentElement.style.setProperty("--paper-shade", c.shade);
  }, [state.paper]);

  const open = openId ? PRODUCTS.find(p => p.id === openId) : null;

  return (
    <>
      <TopNav hasHero={true} />
      <main>
        <Hero />
        <ProductRail onOpen={setOpenId} />
        <AdditiveFreeBanner />
        <FounderNarrative />
        <ShelfTest />
        <LifestyleGrid />
      </main>
      <SiteFooter />
      <SlideOutPanel product={open} open={!!openId} onClose={() => setOpenId(null)} />
      <TweakPanel open={editMode} state={state} setState={setState} />
    </>
  );
}

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(<App />);
