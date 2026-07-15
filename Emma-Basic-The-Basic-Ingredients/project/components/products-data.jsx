/* ============================================================
   PRODUCTS — data model (no pricing).
   Drawer data only: ingredients, ours/theirs, "never in jar".
   ============================================================ */

const PRODUCTS = [
  { id: "curry-cubes", name: "Japanese Curry Cubes", origin: "Produced in China", lot: "CC-240410",
    pill: "BEST SELLER", tagline: "Block-style roux. Dissolve into stock, add what's in the fridge.", tone: "warm",
    image: "assets/products-original-backup/curry-cubes-homepage.png",
    amazon: "https://www.amazon.co.uk/dp/B09K6SJ3V3",
    usps: [
      "Addictively tasty — formulated without additives while maintaining full flavour",
      "Ready in approximately 20 minutes",
      "Mild spice level — suitable for children",
      "Free from MSG, colourings, and preservatives",
      "Versatile — use with rice, udon noodles, or whatever vegetables you have",
      "Block form with 8 pieces per packet — serves up to 8 people",
    ],
    ingredients: ["Palm oil (RSPO certified)","Chickpea powder","Curry powder","Coconut milk powder","Sugar","Salt","Tomato powder","Yeast extract","Garlic powder","Onion powder"],
    notTested: ["MSG","Artificial colourings","Preservatives","Flavour enhancers"] },
  { id: "premium-matcha", name: "Premium Grade Matcha", origin: "Shaded 25 days · Produced in China", lot: "HB-240418",
    pill: "BEST SELLER", tagline: "100% pure Tencha leaf. No additives. Batch tested.", tone: "warm",
    image: "assets/products-original-backup/matcha-homepage.jpg",
    imagePosition: "center 30%",
    imageZoom: 1.3,
    amazon: "https://www.amazon.co.uk/dp/B0G8MW2WB7",
    usps: [
      "100% pure matcha from Tencha leaves — no additives, no fillers, no added extract",
      "Every batch tested by accredited laboratories for pesticides and heavy metals",
      "Shade-grown for 25 days before hand-picking — develops natural sweetness, vibrant colour and umami depth",
      "Longjin 43 and Yabukita cultivars — brightness and depth combined",
      "Sealed in multi-layer resealable foil pouch — light-protected to preserve colour and freshness",
      "100g delivers approximately 50–100 cups — ideal for daily use",
      "Naturally contains catechins (tea polyphenols) and L-theanine, a naturally occurring amino acid",
    ],
    ingredients: ["Tencha (green tea). Shade-grown for 25 days prior to harvest."],
    notTested: ["Additives","Fillers","Colourants","Sugar","Anti-caking agents"] },
  { id: "soba-noodles", name: "Soba Noodles", origin: "Buckwheat · Japan", lot: "SN-240501",
    pill: "SOURCE OF PROTEIN", tagline: "100% buckwheat. Nothing added.", tone: "cool",
    image: "assets/products-original-backup/soba-noodles-homepage.png",
    ingredients: ["Buckwheat flour","Water"],
    notTested: ["Wheat flour","Preservatives","Additives"] },
  { id: "sushi-rice", name: "Sushi Rice", origin: "Single-variety · Vietnam", lot: "SR-240501",
    pill: null, tagline: "Short-grain Japonica. Perfect texture every time.", tone: "cool",
    image: "assets/products-original-backup/sushi-rice-homepage.png",
    imagePosition: "40% center",
    imageZoom: 1.35,
    amazon: "https://www.amazon.co.uk/dp/B0G6M7F5BW",
    usps: [
      "Superior-grade Japonica variety — selected by professionals with 140+ years specialising in rice",
      "Perfect texture — balances stickiness and firmness; holds shape without going mushy",
      "Grown in Vietnam's Mekong Delta nutrient-rich soil",
      "Single variety — behaves predictably every time you cook it",
      "Beyond sushi — works as everyday rice with vegetables, meat, or fish",
      "Manufacturer operates under BRC and FSSC food safety programmes",
    ],
    ingredients: ["Japonica rice."],
    notTested: ["Added glucose","Polishing compounds","Preservatives"] },
  { id: "sesame-oil", name: "Pure Toasted Sesame Oil", origin: "Physically pressed · Japan", lot: "SO-240319",
    pill: "NEW FORMULA", tagline: "Physically pressed — never chemically refined.", tone: "warm",
    image: "assets/products-original-backup/sesame-oil-homepage.jpg",
    amazon: "https://www.amazon.co.uk/dp/B089LPHTCZ",
    usps: [
      "100% pure — made from a single ingredient: the finest roasted sesame seeds",
      "Physically pressed, not chemically extracted with hexane",
      "Rich flavour and nutty aroma from properly roasted and gently pressed sesame",
      "Dark caramel colour — widely used across Asian cuisines",
      "Only 14% saturated fats",
      "A kitchen staple — every kitchen needs a bottle",
    ],
    ingredients: ["Sesame oil (100%). Physically pressed, unrefined."],
    notTested: ["Hexane residue","Bleaching agents","Trans fats"] },
  { id: "dashi-soy-sauce", name: "Dashi Soy Sauce", origin: "Brewed · Japan", lot: "DS-240501",
    pill: "GLUTEN FREE", tagline: "Brewed slowly. No shortcuts.", tone: "warm",
    image: "assets/products-original-backup/dashi-soy-sauce-homepage.jpg",
    imageZoom: 1.1,
    imagePosition: "left center",
    ingredients: ["Soy sauce","Dashi (kombu, bonito)","Salt."],
    notTested: ["MSG","Artificial flavourings","Preservatives"] },
  { id: "white-miso-1kg", name: "Miso 1kg", origin: "Traditionally fermented · Produced in China", lot: "MS-240319",
    pill: "UNPASTEURISED", tagline: "Raw, unpasteurised white miso. Fermented from soybeans, rice, and salt — nothing else.", tone: "cool",
    image: "assets/products-original-backup/miso-homepage.png",
    usps: [
      "Raw & unpasteurised — never heat-treated, preserving live cultures and enzymes",
      "Four ingredients only: water, soybeans, rice, salt — nothing added",
      "Non-GMO soybeans, traditionally fermented using time-honoured artisanal methods",
      "Bold umami depth — works in soups, glazes, dressings, stir-fries, and ramen broth",
      "Vegan and suitable for vegetarians",
      "Naturally rich amber colour deepens as the miso continues to age and develop flavour",
    ],
    ingredients: ["Water","Soybeans (28.8%)","Rice (23%)","Salt (11.5%)"],
    notTested: ["MSG","Preservatives","Additives","Artificial flavourings"] },
  { id: "wakame", name: "Wakame 50g", origin: "Wild-harvested · Japan", lot: "WK-240501",
    pill: null, tagline: "Dried at source. Rehydrates in minutes.", tone: "cool",
    image: "assets/products-original-backup/wakame-homepage.png",
    ingredients: ["Wakame seaweed"],
    notTested: ["Salt","Preservatives","Flavour enhancers"] },
];

function Pill({ label }) {
  const isColorful = label === "BEST SELLER" || label === "NEW FORMULA" || label === "GLUTEN FREE" || label === "SOURCE OF PROTEIN" || label.startsWith("GREAT TASTE");
  return (
    <span style={{
      fontFamily: "var(--f-body)", fontSize: 9.5, letterSpacing: "0.22em",
      padding: "5px 9px",
      border: "1px solid var(--ink)",
      background: isColorful ? "var(--daylight)" : "var(--paper-bright)",
      color: "var(--ink)", textTransform: "uppercase",
    }}>{label}</span>
  );
}

window.PRODUCTS = PRODUCTS;
window.Pill = Pill;
