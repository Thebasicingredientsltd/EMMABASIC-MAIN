# Emma Basic — Minimalist Grit (Design System Prototype)

A high-fidelity, interactive redesign prototype for **emmabasic.co.uk**.
Aesthetic direction: *Minimalist Grit* — Aesop-clinical precision × Cadence-raw athletics.

> **Note on copyright:** this is an *original* design system. No Aesop,
> Cadence or other third-party UI is reproduced. Aesthetic cues are
> referenced only at the philosophy level (density, restraint, monochrome,
> editorial serif).

---

## Run the prototype

Open `Emma Basic Homepage.html` in the preview. Toggle **Tweaks** (top toolbar)
to swap serif, grid density, accent mode, and paper tone.

### Interactions wired up
- Slide-out **Label Decoder** drawer on product-card click (Esc / scrim to close)
- Hover reveal on product tiles ("Read the Label")
- Newsletter form with local submit state
- Basket counter persists via in-memory cart
- Tweak panel persists to `localStorage` and writes back to the HTML file

---

## Design tokens — at a glance

| Token | Value | Rationale |
|---|---|---|
| `--ink` | `#0A0A0A` | Never pure #000 — reads softer in long-form |
| `--paper` | `#F6F4EF` | Warm off-white "daylight paper" |
| `--paper-bright` | `#FFFFFF` | Product pedestals, drawer |
| `--daylight` | `oklch(0.88 0.08 95)` | *Only* accent — reserved for "BEST SELLER" pill |
| `--rule` | `rgba(10,10,10,0.12)` | Hairline dividers everywhere |
| `--f-display` | Fraunces (Fahkwang/Minerva stand-in) | Editorial, variable-axis for soft/wonk tuning |
| `--f-body` | Inter Tight (Futura Book stand-in) | Clinical, legible |
| `--f-mono` | JetBrains Mono | Apothecary-label feel |
| `--section-y` | `clamp(96px, 14vw, 180px)` | Generous negative space |
| `--dur-drawer` | `420ms` | Drawer slide timing |
| `--ease-out` | `cubic-bezier(0.2, 0.8, 0.2, 1)` | Standard motion |

> Fonts are **free substitutes** because Fahkwang/Minerva/Futura-Book aren't
> on Google Fonts. Once licensed, swap the `@font-face` declarations and the
> layout will hold — Fraunces is metrically similar enough to Fahkwang.

---

## Next.js integration map

Every file under `components/` is framework-agnostic vanilla JSX. Port into
a Next.js App Router project like this:

```
app/
├─ layout.tsx              ← load Google Fonts, import globals.css
├─ page.tsx                ← renders <Homepage />
├─ globals.css             ← paste components/tokens.css
components/
├─ Placeholder.tsx         ← replace with <Image /> wrapper in prod
├─ TopNav.tsx
├─ IntegratedHero.tsx
├─ FounderNarrative.tsx
├─ ApothecaryGrid.tsx      ← owns ProductCard + Pill
├─ SlideOutPanel.tsx       ← Framer-Motion variant recommended in prod
├─ Sections.tsx            ← EducationalBlock, LifestyleGrid, Newsletter, Footer
data/
└─ products.ts             ← lift the PRODUCTS array from ApothecaryGrid.jsx
```

**Swap-outs for production**
- `SlideOutPanel` → use Framer Motion `<AnimatePresence>` + `motion.aside`
  for GPU-accelerated transforms; keep 420ms / ease-out timing.
- `Placeholder` → `next/image` with `sizes` set for the grid breakpoints.
- `PRODUCTS` → Sanity/Shopify schema; `ingredients`, `ours`, `theirs`,
  `notTested`, `batchCert` are the fields the drawer needs.

---

## Component responsibilities

### TopNav
Persistent horizontal menu (no hamburger). Serif wordmark centered,
utility links on both sides, mono-typed manifesto ticker below.

### IntegratedHero
Two-panel "Grit / Purity" composition over editorial display heading.
Left tile = athlete photography (dark tone). Right column = product
pedestal + thesis paragraph. Display heading uses Fraunces italic on
the second line for editorial rhythm.

### FounderNarrative
20% allocation. Sticky portrait left, two-column letter right.
Signature line uses Fraunces wonky italic axis for handwritten feel.

### ApothecaryGrid + ProductCard + Pill
The commercial hub. 3×2 (or 4-col compact) grid on hairline rules.
Cards show index, origin, lot number, price. Hover reveals
"Read the Label" CTA. Click opens the drawer.

### SlideOutPanel (drawer)
560px wide, 420ms slide. Contents:
1. Hero image
2. Name + tagline (italic serif)
3. **Label comparison** — two columns (ink vs paper, ours vs theirs)
4. Ingredient list (full, serif-set)
5. "What's never in the jar" — strikethrough mono chips
6. Batch certificate download
7. Sticky footer with price + Add to Basket

### EducationalBlock
Ink-background section. Four-line promise, stacked on hairlines.
Visual proof = "27 ingredients vs 1 ingredient" split comparison.

### LifestyleGrid
Widescreen asymmetric grid (4-col, 220px rows, span modifiers for
tall/wide tiles). Tiles tagged "The Grit" or "The Purity" with
mono-set overlay pill.

### NewsletterCapture
"Join the No-Additive Movement." Display-serif email input, hairline
underline only — no input chrome.

### SiteFooter
5-column grid (brand + 4 link columns). Mono meta row at the base.

---

## Imagery brief (for photo shoot handoff)

All placeholders are tagged in monospace with exactly what belongs
there. Tone codes on the placeholders indicate treatment:

- **`tone="ink"`** — raw, exertion, low-key. Post-run, sweat,
  worn-in shoes, heath at dawn.
- **`tone="warm"`** — pristine apothecary daylight. Product
  on off-white surface, single window-light, soft shadow.
- **`tone="cool"`** — kitchen / process. Pouring, pressing,
  stirring, cutting — shot at the counter.

Every tile on the lifestyle grid alternates kinds — never two
"Purity" shots adjacent.

---

## Copy voice — adopted throughout

- Short, declarative. No exclamation marks.
- "We" speaks as Emma + her team, never corporate.
- Numbers in mono, always zero-padded (N°01, Lot HB-240418).
- "The Grit / The Purity" is the recurring framework — use on
  section headers, image captions, and product story pages.

---

## Known next steps

1. Commission real photography per the brief above.
2. License Fahkwang + Futura Book; swap the `@font-face`s.
3. Build the full product pages; the drawer is the bridge, not
   the destination.
4. Add **Matcha Lab** — a dedicated educational sub-site the top-nav
   already points to.
5. Mobile: redesign the two-panel hero as stacked; drawer becomes
   bottom-sheet at <720px.
