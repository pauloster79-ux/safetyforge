// Icons v2 — pixel-aligned, construction-aware
//
// Design goals:
//  • Sharp at 14/16/20 by using integer path coords and avoiding
//    stroke widths below 1.5 at display sizes ≤16px.
//  • Consistent optical weight — every glyph has the same "ink coverage"
//    so badges, menu items and inline chips don't flicker between bold/thin.
//  • Purpose-built for the domain: stamps, ledgers, invoices, hard hats,
//    levels, plumb bobs, scaffolding, permits. No generic Lucide stand-ins.
//  • Two density modes — `bold` (sw=2.2) for buttons and primary nav,
//    `line` (sw=1.75) for dense tables and inline meta.

const Ic2 = ({ s = 20, sw = 1.75, fill = 'none', color, stroke = true, children, style }) => (
  <svg
    width={s} height={s} viewBox="0 0 24 24"
    fill={fill}
    stroke={stroke ? (color || 'currentColor') : 'none'}
    strokeWidth={sw}
    strokeLinecap="square"
    strokeLinejoin="miter"
    shapeRendering="geometricPrecision"
    style={{display:'inline-block', verticalAlign:'middle', flexShrink:0, color, ...style}}
  >{children}</svg>
);

// ── CORE NAV ───────────────────────────────────────────────────────
// sun — today / morning brief. Square rays keep it on grid.
const I2Sun = (p) => <Ic2 {...p}>
  <rect x="8" y="8" width="8" height="8"/>
  <path d="M12 3v2M12 19v2M3 12h2M19 12h2M5.5 5.5l1.5 1.5M17 17l1.5 1.5M5.5 18.5l1.5-1.5M17 7l1.5-1.5"/>
</Ic2>;

// speech-column — chat (square caps, no floaty circle)
const I2Chat = (p) => <Ic2 {...p}>
  <path d="M4 5h16v11H10l-4 4v-4H4z"/>
  <path d="M8 9h8M8 12h5"/>
</Ic2>;

// stacked folders — projects (two rails for depth, clearly "many")
const I2Jobs = (p) => <Ic2 {...p}>
  <path d="M3 8v11h15"/>
  <path d="M7 5h4l2 2h8v10H7z"/>
</Ic2>;

// ledger — contract/quote. Bound spine + ruled lines.
const I2Ledger = (p) => <Ic2 {...p}>
  <path d="M5 4h13v16H5z"/>
  <path d="M5 4v16M9 8h6M9 11h6M9 14h4"/>
</Ic2>;

// clipboard with tick (daily log)
const I2Log = (p) => <Ic2 {...p}>
  <path d="M8 4h8v3H8z"/>
  <path d="M6 5h2M16 5h2v15H6V5h2"/>
  <path d="m9 13 2 2 4-4"/>
</Ic2>;

// hard hat — crew. Square brim, dome, top vent.
const I2Crew = (p) => <Ic2 {...p}>
  <path d="M3 17h18v3H3z"/>
  <path d="M6 17V13c0-3 2.5-5 6-5s6 2 6 5v4"/>
  <path d="M11 8V6h2v2"/>
</Ic2>;

// shield with caret — compliance, not a tick (tick is for logs)
const I2Shield = (p) => <Ic2 {...p}>
  <path d="M12 3 4 5v7c0 5 3.5 8 8 9 4.5-1 8-4 8-9V5l-8-2z"/>
  <path d="m9 11 3 3 4-5"/>
</Ic2>;

// wrench — equipment / gear
const I2Wrench = (p) => <Ic2 {...p}>
  <path d="m14 4 2 2-2 2 2 2 3-3a4 4 0 0 0-5-5l-3 3 2 2z"/>
  <path d="M13 10 4 19l2 2 9-9"/>
</Ic2>;

// ruled page — documents
const I2Doc = (p) => <Ic2 {...p}>
  <path d="M6 3h8l4 4v14H6z"/>
  <path d="M14 3v4h4M9 12h6M9 15h6M9 18h4"/>
</Ic2>;

// grid layers — knowledge base / insights
const I2Knowledge = (p) => <Ic2 {...p}>
  <path d="m12 3 9 4-9 4-9-4 9-4z"/>
  <path d="m3 12 9 4 9-4M3 17l9 4 9-4"/>
</Ic2>;

// calendar — schedule
const I2Cal = (p) => <Ic2 {...p}>
  <path d="M4 6h16v14H4zM4 10h16M9 3v5M15 3v5"/>
</Ic2>;

// ── DOMAIN ─────────────────────────────────────────────────────────
// receipt with stub — line item / quote line
const I2Receipt = (p) => <Ic2 {...p}>
  <path d="M6 3h12v18l-2-2-2 2-2-2-2 2-2-2-2 2z"/>
  <path d="M9 8h6M9 11h6M9 14h4"/>
</Ic2>;

// gavel with block — decisions / approvals
const I2Gavel = (p) => <Ic2 {...p}>
  <path d="m14 3 7 7-3 3-7-7z"/>
  <path d="M11 6 4 13l3 3 7-7"/>
  <path d="M4 21h12"/>
</Ic2>;

// plumb bob — sources / truth
const I2Plumb = (p) => <Ic2 {...p}>
  <path d="M12 3v9"/>
  <path d="m8 12 4 8 4-8zM8 12h8"/>
</Ic2>;

// spirit level — verify / check
const I2Level = (p) => <Ic2 {...p}>
  <path d="M2 9h20v6H2z"/>
  <circle cx="12" cy="12" r="2"/>
  <path d="M7 9v6M17 9v6"/>
</Ic2>;

// anvil — knowledge / rates / built things
const I2Anvil = (p) => <Ic2 {...p}>
  <path d="M4 7h14l-2 4h4v2H5a3 3 0 0 1-3-3V7z"/>
  <path d="M7 13v4h10v4H5v-2"/>
</Ic2>;

// scaffolding — safety / structure
const I2Scaffold = (p) => <Ic2 {...p}>
  <path d="M3 4v16M9 4v16M15 4v16M21 4v16"/>
  <path d="M3 9h18M3 14h18M3 19h18"/>
</Ic2>;

// stamp — approved / issued
const I2Stamp = (p) => <Ic2 {...p}>
  <path d="M9 3h6v5l2 3H7l2-3z"/>
  <path d="M4 14h16v3H4zM4 19h16"/>
</Ic2>;

// triangle + bang — alert
const I2Alert = (p) => <Ic2 {...p}>
  <path d="m12 3 10 17H2z"/>
  <path d="M12 10v5M12 18h.01"/>
</Ic2>;

// exclamation-doc — variation trigger
const I2Variation = (p) => <Ic2 {...p}>
  <path d="M6 3h9l3 3v15H6z"/>
  <path d="M15 3v3h3"/>
  <path d="M12 10v4M12 17h.01"/>
</Ic2>;

// ban — exclusion
const I2Ban = (p) => <Ic2 {...p}>
  <circle cx="12" cy="12" r="8"/>
  <path d="m6 6 12 12"/>
</Ic2>;

// question-doc — assumption
const I2Assumption = (p) => <Ic2 {...p}>
  <path d="M6 3h9l3 3v15H6z"/>
  <path d="M15 3v3h3"/>
  <path d="M10 11c0-1 1-2 2-2s2 1 2 2-2 2-2 3M12 17h.01"/>
</Ic2>;

// microphone — voice (sharper: square cap, no curved base)
const I2Mic = (p) => <Ic2 {...p}>
  <path d="M9 3h6v10H9z"/>
  <path d="M5 11a7 7 0 0 0 14 0M12 18v3M8 21h8"/>
</Ic2>;

// arrow-up-right — send / submit (square, confident)
const I2Send = (p) => <Ic2 {...p}>
  <path d="M5 19 19 5M9 5h10v10"/>
</Ic2>;

// arrow — nav
const I2Arrow = (p) => <Ic2 {...p}><path d="M4 12h16M13 5l7 7-7 7"/></Ic2>;

// plus
const I2Plus = (p) => <Ic2 {...p}><path d="M12 4v16M4 12h16"/></Ic2>;

// refresh
const I2Refresh = (p) => <Ic2 {...p}>
  <path d="M4 11V5l3 3a8 8 0 0 1 12 2"/>
  <path d="M20 13v6l-3-3a8 8 0 0 1-12-2"/>
</Ic2>;

// trash
const I2Trash = (p) => <Ic2 {...p}>
  <path d="M4 7h16M9 7V4h6v3M6 7v13h12V7"/>
  <path d="M10 11v5M14 11v5"/>
</Ic2>;

// search
const I2Search = (p) => <Ic2 {...p}><circle cx="11" cy="11" r="6"/><path d="m16 16 5 5"/></Ic2>;

// dollar — money
const I2Dollar = (p) => <Ic2 {...p}><path d="M12 3v18M16 8c-1-1-2-2-4-2s-4 1-4 3 2 3 4 3 4 1 4 3-2 3-4 3-3-1-4-2"/></Ic2>;

// percent
const I2Percent = (p) => <Ic2 {...p}><path d="m5 19 14-14"/><circle cx="7" cy="7" r="2.5"/><circle cx="17" cy="17" r="2.5"/></Ic2>;

// pencil — edit
const I2Edit = (p) => <Ic2 {...p}><path d="M14 4 20 10l-11 11H3v-6z"/></Ic2>;

// chevron
const I2Chev = (p) => <Ic2 {...p}><path d="m9 6 6 6-6 6"/></Ic2>;
const I2ChevDown = (p) => <Ic2 {...p}><path d="m6 9 6 6 6-6"/></Ic2>;

// x
const I2X = (p) => <Ic2 {...p}><path d="M5 5l14 14M19 5 5 19"/></Ic2>;

// circle dot — bullet
const I2Dot = (p) => <Ic2 {...p} stroke={false} fill="currentColor"><circle cx="12" cy="12" r="3"/></Ic2>;

// file-text — proposal
const I2Proposal = (p) => <Ic2 {...p}>
  <path d="M6 3h9l3 3v15H6z"/>
  <path d="M15 3v3h3M9 11h6M9 14h6M9 17h4"/>
</Ic2>;

// expand — detail
const I2Expand = (p) => <Ic2 {...p}><path d="M4 9V4h5M20 15v5h-5M4 15v5h5M20 9V4h-5"/></Ic2>;

// filter
const I2Filter = (p) => <Ic2 {...p}><path d="M3 5h18l-7 9v6l-4-2v-4z"/></Ic2>;

// eye
const I2Eye = (p) => <Ic2 {...p}><path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7z"/><circle cx="12" cy="12" r="3"/></Ic2>;

// circle check (valid) and circle x (expired) — filled chip style
const I2CheckBadge = (p) => <Ic2 {...p}><circle cx="12" cy="12" r="9"/><path d="m8 12 3 3 5-6"/></Ic2>;
const I2XBadge = (p) => <Ic2 {...p}><circle cx="12" cy="12" r="9"/><path d="m8 8 8 8M16 8l-8 8"/></Ic2>;

// clock — deadline
const I2Clock = (p) => <Ic2 {...p}><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/></Ic2>;

// dots — more / menu
const I2Dots = (p) => <Ic2 {...p} stroke={false} fill="currentColor"><circle cx="5" cy="12" r="1.75"/><circle cx="12" cy="12" r="1.75"/><circle cx="19" cy="12" r="1.75"/></Ic2>;

// bell — notifications
const I2Bell = (p) => <Ic2 {...p}><path d="M6 16V11a6 6 0 0 1 12 0v5l2 2H4z"/><path d="M10 21h4"/></Ic2>;

// settings cog (square, hex-ish)
const I2Cog = (p) => <Ic2 {...p}><path d="M12 3v2M12 19v2M4.5 7.5 6 9M18 15l1.5 1.5M3 12h2M19 12h2M4.5 16.5 6 15M18 9l1.5-1.5"/><circle cx="12" cy="12" r="4"/></Ic2>;

// user circle
const I2User = (p) => <Ic2 {...p}><circle cx="12" cy="9" r="3.5"/><path d="M5 20c1-3 4-5 7-5s6 2 7 5"/></Ic2>;

// lightning — action/fast
const I2Bolt = (p) => <Ic2 {...p}><path d="M13 3 5 13h6l-1 8 8-10h-6l1-8z"/></Ic2>;

Object.assign(window, {
  I2Sun, I2Chat, I2Jobs, I2Ledger, I2Log, I2Crew, I2Shield, I2Wrench, I2Doc, I2Knowledge, I2Cal,
  I2Receipt, I2Gavel, I2Plumb, I2Level, I2Anvil, I2Scaffold, I2Stamp, I2Alert, I2Variation, I2Ban,
  I2Assumption, I2Mic, I2Send, I2Arrow, I2Plus, I2Refresh, I2Trash, I2Search, I2Dollar, I2Percent,
  I2Edit, I2Chev, I2ChevDown, I2X, I2Dot, I2Proposal, I2Expand, I2Filter, I2Eye, I2CheckBadge,
  I2XBadge, I2Clock, I2Dots, I2Bell, I2Cog, I2User, I2Bolt,
});
