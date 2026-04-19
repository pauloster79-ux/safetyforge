import React from "react";
import {
  AbsoluteFill,
  useCurrentFrame,
  interpolate,
  spring,
  Easing,
} from "remotion";
import { dark, fonts, type } from "../components/dark-styles";
import { IconRail, ChatPane, ChatMsg, DashKicker } from "../components/ProjectFrame";

const F = 30;
export const QUOTING_DETAIL_DURATION_FRAMES = 48 * F; // 48 seconds

// Phase timings
const T = {
  P1_OVERVIEW: [0, 9 * F],           // 0–9s  quote overview
  P2_INSPECTOR_OPEN: [9 * F, 18 * F],  // 9–18s inspector slides in, contents reveal
  P3_LABOUR_DRILL: [18 * F, 30 * F],  // 18–30s click labour, equation builds
  P4_PROVENANCE: [30 * F, 42 * F],    // 30–42s provenance tree reveals
  P5_OUTRO: [42 * F, 48 * F],         // 42–48s summary
};

const slideIn = (frame: number, appearAt: number, distance = 16) => {
  const rel = frame - appearAt;
  if (rel < 0) return { opacity: 0, ty: distance, tx: 0 };
  const opacity = interpolate(rel, [0, 12], [0, 1], { extrapolateRight: "clamp" });
  const s = spring({ frame: rel, fps: 30, config: { damping: 18, stiffness: 120 } });
  return { opacity, ty: (1 - s) * distance, tx: 0 };
};

const slideInX = (frame: number, appearAt: number, distance = 40) => {
  const rel = frame - appearAt;
  if (rel < 0) return { opacity: 0, tx: distance };
  const opacity = interpolate(rel, [0, 14], [0, 1], { extrapolateRight: "clamp" });
  const s = spring({ frame: rel, fps: 30, config: { damping: 20, stiffness: 130 } });
  return { opacity, tx: (1 - s) * distance };
};

// ── Shared chrome ───────────────────────────────────────────
const Chrome: React.FC = () => (
  <>
    <div
      style={{
        padding: "14px 22px", backgroundColor: dark.ink2,
        borderBottom: `1px solid ${dark.hairline}`,
        display: "flex", alignItems: "center", gap: 14, flexShrink: 0,
      }}
    >
      <div
        style={{
          width: 22, height: 22, backgroundColor: dark.machine, borderRadius: 3,
          display: "flex", alignItems: "center", justifyContent: "center",
          color: dark.ink0, fontFamily: fonts.mono, fontWeight: 700, fontSize: 11,
        }}
      >K</div>
      <div style={{ ...type.title }}>Maple Ridge — Phase II</div>
      <span style={{ color: dark.fgDim, fontFamily: fonts.mono, fontSize: 11 }}>·</span>
      <span
        style={{
          ...type.kicker, fontSize: 11, color: dark.machine,
          backgroundColor: dark.machineWash, padding: "2px 6px",
          borderRadius: 3, fontWeight: 600,
        }}
      >MRP-2024-118</span>
      <span style={{ color: dark.fgDim, fontFamily: fonts.mono, fontSize: 11 }}>·</span>
      <span style={{ ...type.label, color: dark.fgMuted }}>Maple Ridge Dev. Corp.</span>
      <span
        style={{
          ...type.kicker, fontSize: 10, fontWeight: 600,
          padding: "3px 8px", borderRadius: 3,
          border: `1px solid ${dark.machine}`,
          backgroundColor: dark.machine, color: dark.ink0,
        }}
      >Quoted · Draft A</span>
      <div style={{ marginLeft: "auto", display: "flex", alignItems: "center", gap: 12 }}>
        <div>
          <div style={{ ...type.kicker, color: dark.fgMuted, textAlign: "right" }}>Quote Total</div>
          <div
            style={{
              fontFamily: fonts.mono, fontSize: 16, color: dark.machine,
              fontWeight: 600, textAlign: "right", lineHeight: 1.1,
            }}
          >$121,200</div>
        </div>
        <button
          style={{
            padding: "10px 16px", backgroundColor: dark.machine, color: dark.ink0,
            border: `1px solid ${dark.machine}`, borderRadius: 4,
            fontFamily: fonts.mono, fontSize: 11, fontWeight: 600,
            letterSpacing: "0.06em", textTransform: "uppercase",
          }}
        >Generate Proposal</button>
      </div>
    </div>
    <div
      style={{
        display: "flex", padding: "0 22px",
        backgroundColor: dark.ink1, borderBottom: `1px solid ${dark.hairline}`,
        gap: 2, flexShrink: 0,
      }}
    >
      {["◉ Dashboard", "⚒ Scope · 7", "⬒ Variations", "◎ Timeline", "$ Money", "▤ Contract", "⚘ Docs", "⚐ People · 2"].map((t, i) => (
        <div
          key={i}
          style={{
            padding: "12px 14px 11px", ...type.label,
            color: i === 1 ? dark.machine : dark.fgMuted,
            borderBottom: `2px solid ${i === 1 ? dark.machine : "transparent"}`,
            backgroundColor: i === 1 ? dark.ink0 : "transparent",
          }}
        >{t}</div>
      ))}
    </div>
  </>
);

// ── Quote table (used in Phase 1–2) ─────────────────────────
const QuoteTable: React.FC<{ highlightRow?: number; extraDim?: boolean }> = ({ highlightRow, extraDim }) => {
  const rows = [
    ["01", "Mobilization & site prep", "1 LS", "$6,400", "$2,800", "$11,200"],
    ["02", "Rough electrical — 1st floor", "32 PT", "$18,240", "$5,760", "$30,500"],
    ["03", "Panel upgrade — 200A service", "1 LS", "$4,100", "$8,900", "$16,300"],
    ["04", "Floor boxes — receptacle + data", "12 EA", "$4,560", "$3,240", "$9,800"],
    ["05", "Rough electrical — 2nd floor", "28 PT", "$16,060", "$5,050", "$24,800"],
    ["06", "Finish — 1st + 2nd", "1 LS", "$7,800", "$7,300", "$20,400"],
    ["07", "Testing & commissioning", "1 LS", "$2,700", "$4,700", "$8,200"],
  ];
  return (
    <div
      style={{
        backgroundColor: dark.ink2, border: `1px solid ${dark.hairline}`,
        borderRadius: 4, marginBottom: 14, overflow: "hidden",
      }}
    >
      <div
        style={{
          padding: "12px 16px", display: "flex", alignItems: "center", gap: 12,
          borderBottom: `1px solid ${dark.hairline}`,
        }}
      >
        <span style={{ fontFamily: fonts.mono, fontSize: 10, color: dark.fgDim, letterSpacing: "0.08em", fontWeight: 600 }}>01</span>
        <span style={{ ...type.label, fontWeight: 600 }}>⚒ Work Items</span>
        <span
          style={{
            ...type.kicker, fontSize: 9, fontWeight: 600,
            padding: "2px 6px", borderRadius: 3,
            backgroundColor: dark.machineWash, color: dark.machine,
          }}
        >7</span>
      </div>
      <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 12 }}>
        <thead>
          <tr>
            {["#", "Description", "Qty", "Labour", "Items", "Sell"].map((h, i) => (
              <th
                key={i}
                style={{
                  padding: "9px 16px", textAlign: i === 2 || i === 3 || i === 4 || i === 5 ? "right" : "left",
                  borderBottom: `1px solid ${dark.hairline}`,
                  fontFamily: fonts.mono, fontSize: 10,
                  letterSpacing: "0.06em", textTransform: "uppercase",
                  color: dark.fgMuted, fontWeight: 500, backgroundColor: dark.ink1,
                }}
              >{h}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((r, i) => {
            const isHighlight = highlightRow === i;
            return (
              <tr
                key={i}
                style={{
                  backgroundColor: isHighlight ? dark.machineWash : "transparent",
                  opacity: extraDim && !isHighlight ? 0.5 : 1,
                  transition: "background-color 300ms ease, opacity 300ms ease",
                }}
              >
                <td
                  style={{
                    padding: "9px 16px", fontFamily: fonts.mono,
                    color: isHighlight ? dark.machine : dark.fgDim, width: 28,
                    borderBottom: i === rows.length - 1 ? "none" : `1px solid ${dark.hairline}`,
                    borderLeft: isHighlight ? `3px solid ${dark.machine}` : "none",
                    paddingLeft: isHighlight ? 13 : 16,
                  }}
                >{r[0]}</td>
                <td
                  style={{
                    padding: "9px 16px", color: dark.fg,
                    borderBottom: i === rows.length - 1 ? "none" : `1px solid ${dark.hairline}`,
                  }}
                >
                  {r[1]}
                  {i === 3 && (
                    <span
                      style={{
                        marginLeft: 6, fontFamily: fonts.mono, fontSize: 9,
                        color: dark.machine, backgroundColor: dark.machineWash,
                        padding: "1px 5px", borderRadius: 2, letterSpacing: "0.06em",
                      }}
                    >⚑ +15% insight</span>
                  )}
                </td>
                {[2, 3, 4, 5].map((colIdx) => (
                  <td
                    key={colIdx}
                    style={{
                      padding: "9px 16px",
                      fontFamily: fonts.mono, textAlign: "right",
                      color: colIdx === 5 ? dark.machine : dark.fg,
                      fontWeight: colIdx === 5 ? 500 : 400,
                      borderBottom: i === rows.length - 1 ? "none" : `1px solid ${dark.hairline}`,
                    }}
                  >{r[colIdx] as string}</td>
                ))}
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
};

// ── Inspector panel ─────────────────────────────────────────
const InspectorPanel: React.FC<{ baseFrame: number; showLabourDrill: boolean; showProvenance: boolean }> = ({
  baseFrame, showLabourDrill, showProvenance,
}) => {
  const frame = useCurrentFrame();
  const headAnim = slideIn(frame, baseFrame + 6);
  const tilesAnim = slideIn(frame, baseFrame + 18);
  const insightAnim = slideIn(frame, baseFrame + 38);
  const labourAnim = slideIn(frame, baseFrame + 62);

  return (
    <div
      style={{
        width: 440, backgroundColor: dark.ink2,
        border: `1px solid ${dark.hairline}`, borderRadius: 4,
        overflow: "hidden", display: "flex", flexDirection: "column",
      }}
    >
      <div
        style={{
          opacity: headAnim.opacity, transform: `translateY(${headAnim.ty}px)`,
          padding: "14px 18px", borderBottom: `1px solid ${dark.hairline}`,
          backgroundColor: dark.ink3,
          display: "flex", justifyContent: "space-between", alignItems: "flex-start",
          flexShrink: 0,
        }}
      >
        <div>
          <div
            style={{
              fontFamily: fonts.mono, fontSize: 10, color: dark.machine,
              letterSpacing: "0.12em", textTransform: "uppercase",
              fontWeight: 600, marginBottom: 4,
            }}
          >⚒ Item 04 · WorkItem</div>
          <div style={{ fontSize: 14, color: dark.fg, fontWeight: 500 }}>
            Floor boxes — receptacle + data
          </div>
        </div>
        <div style={{ color: dark.fgDim, fontFamily: fonts.mono, fontSize: 14 }}>✕</div>
      </div>

      <div style={{ flex: 1, padding: "14px 18px", overflow: "hidden" }}>
        {/* Summary tiles */}
        <div
          style={{
            opacity: tilesAnim.opacity, transform: `translateY(${tilesAnim.ty}px)`,
            display: "grid", gridTemplateColumns: "1fr 120px 120px", gap: 10, marginBottom: 14,
          }}
        >
          <div>
            <div style={{ fontSize: 12, color: dark.fgMuted, lineHeight: 1.5 }}>
              <div><strong style={{ color: dark.fg, fontWeight: 500 }}>12 EA</strong> · floor box assemblies</div>
              <div style={{ fontFamily: fonts.mono, fontSize: 10, letterSpacing: "0.06em", marginTop: 4 }}>MasterFormat 26 27 26</div>
              <div style={{ fontSize: 11, marginTop: 2 }}>Reception + open office</div>
            </div>
          </div>
          <div
            style={{
              backgroundColor: dark.ink3, border: `1px solid ${dark.hairline}`,
              borderRadius: 4, padding: "10px 12px",
            }}
          >
            <div style={{ ...type.kicker, color: dark.fgMuted, marginBottom: 4 }}>Sell</div>
            <div style={{ fontFamily: fonts.mono, fontSize: 16, color: dark.machine, fontWeight: 500 }}>$9,800</div>
            <div style={{ fontFamily: fonts.mono, fontSize: 10, color: dark.fgMuted, marginTop: 3, letterSpacing: "0.04em" }}>$817 / unit</div>
          </div>
          <div
            style={{
              backgroundColor: dark.ink3, border: `1px solid ${dark.hairline}`,
              borderRadius: 4, padding: "10px 12px",
            }}
          >
            <div style={{ ...type.kicker, color: dark.fgMuted, marginBottom: 4 }}>Margin</div>
            <div style={{ fontFamily: fonts.mono, fontSize: 16, color: dark.pass, fontWeight: 500 }}>22%</div>
            <div style={{ fontFamily: fonts.mono, fontSize: 10, color: dark.fgMuted, marginTop: 3, letterSpacing: "0.04em" }}>$7,800 cost</div>
          </div>
        </div>

        {/* Insight card */}
        <div
          style={{
            opacity: insightAnim.opacity, transform: `translateY(${insightAnim.ty}px)`,
            backgroundColor: dark.machineStrong, border: `1px solid ${dark.machine}`,
            borderRadius: 4, padding: 14, marginBottom: 14,
          }}
        >
          <div
            style={{
              display: "flex", justifyContent: "space-between",
              alignItems: "center", marginBottom: 10,
            }}
          >
            <div
              style={{
                fontFamily: fonts.mono, fontSize: 10, color: dark.machineBright,
                letterSpacing: "0.12em", textTransform: "uppercase", fontWeight: 600,
              }}
            >⚑ Insight applied · +15% labour</div>
            <div style={{ fontFamily: fonts.mono, fontSize: 10, color: dark.machineBright, letterSpacing: "0.08em" }}>
              Conf 92% · n=3
            </div>
          </div>
          <div style={{ fontSize: 12.5, color: dark.fg, lineHeight: 1.5, marginBottom: 10 }}>
            <strong style={{ color: dark.machineBright, fontWeight: 500 }}>Low-ceiling insight:</strong> floor-box installs below 9' run ~15% longer. Detected from <strong style={{ color: dark.machineBright, fontWeight: 500 }}>Alder St</strong>, <strong style={{ color: dark.machineBright, fontWeight: 500 }}>Chapelwood</strong>, <strong style={{ color: dark.machineBright, fontWeight: 500 }}>Peachtree Ph I</strong>. Maple Ridge reception = 8'6" · match.
          </div>
        </div>

        {/* Labour breakdown */}
        <div style={{ opacity: labourAnim.opacity, transform: `translateY(${labourAnim.ty}px)` }}>
          <div
            style={{
              ...type.kicker, color: dark.machine, marginBottom: 8, fontSize: 10,
            }}
          >Labour · 3 tasks</div>
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 11.5 }}>
            <tbody>
              {[
                ["Core-drill slab + sleeve", "18.4", "$1,693", true],
                ["Set box + unistrut + pull wire", "24.0", "$2,208", false],
                ["Trim device + data jack", "8.0", "$656", false],
              ].map(([task, hrs, cost, isSelected], i) => (
                <tr
                  key={i}
                  style={{
                    backgroundColor: showLabourDrill && isSelected ? dark.machineWash : "transparent",
                    transition: "background-color 300ms ease",
                  }}
                >
                  <td
                    style={{
                      padding: "9px 14px", color: dark.fg,
                      borderLeft: showLabourDrill && isSelected ? `3px solid ${dark.machine}` : "none",
                      paddingLeft: showLabourDrill && isSelected ? 11 : 14,
                      borderBottom: i === 2 ? "none" : `1px solid ${dark.hairline}`,
                    }}
                  >{task as string}</td>
                  <td
                    style={{
                      padding: "9px 14px", fontFamily: fonts.mono, textAlign: "right",
                      color: dark.fg,
                      borderBottom: i === 2 ? "none" : `1px solid ${dark.hairline}`,
                    }}
                  >{hrs as string} hr</td>
                  <td
                    style={{
                      padding: "9px 14px", fontFamily: fonts.mono, textAlign: "right",
                      color: dark.machine, fontWeight: 500,
                      borderBottom: i === 2 ? "none" : `1px solid ${dark.hairline}`,
                    }}
                  >{cost as string}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

// ── Lineage equation panel (Phase 3) ────────────────────────
const LineageEquation: React.FC<{ baseFrame: number }> = ({ baseFrame }) => {
  const frame = useCurrentFrame();
  const n1 = slideIn(frame, baseFrame + 4, 10);
  const n2 = slideIn(frame, baseFrame + 22, 10);
  const n3 = slideIn(frame, baseFrame + 40, 10);
  const n4 = slideIn(frame, baseFrame + 58, 10);
  const n5 = slideIn(frame, baseFrame + 76, 10);
  const n6 = slideIn(frame, baseFrame + 94, 10);
  const n7 = slideIn(frame, baseFrame + 112, 10);

  const Node: React.FC<{ anim: { opacity: number; ty: number }; children: React.ReactNode; variant?: "base" | "insight" | "final" }> = ({ anim, children, variant }) => {
    const bg = variant === "base" ? dark.passBg : variant === "insight" ? dark.machineWash : variant === "final" ? dark.machine : dark.ink4;
    const fg = variant === "base" ? dark.pass : variant === "insight" ? dark.machine : variant === "final" ? dark.ink0 : dark.fg;
    const border = variant === "base" ? dark.pass : variant === "insight" ? dark.machine : variant === "final" ? dark.machine : dark.hairline;
    return (
      <div
        style={{
          opacity: anim.opacity, transform: `translateY(${anim.ty}px)`,
          backgroundColor: bg, color: fg,
          border: `1px solid ${border}`, borderRadius: 3,
          padding: "6px 12px", fontFamily: fonts.mono, fontSize: 12,
          letterSpacing: "0.04em", fontWeight: variant === "final" ? 600 : 500,
          display: "inline-block",
        }}
      >{children}</div>
    );
  };

  const Arrow: React.FC<{ anim: { opacity: number; ty: number }; text?: string }> = ({ anim, text }) => (
    <span
      style={{
        opacity: anim.opacity,
        color: dark.fgDim, fontFamily: fonts.mono, fontSize: 12, padding: "0 4px",
      }}
    >{text || "→"}</span>
  );

  return (
    <div
      style={{
        backgroundColor: dark.ink3, borderRadius: 4, padding: 20,
      }}
    >
      <div
        style={{
          ...type.kicker, color: dark.fgMuted, marginBottom: 16,
        }}
      >How 18.4 hours was computed</div>
      <div
        style={{
          display: "flex", alignItems: "center", gap: 8,
          fontFamily: fonts.mono, fontSize: 12, flexWrap: "wrap",
        }}
      >
        <Node anim={n1}>12 holes</Node>
        <Arrow anim={n2} text="×" />
        <Node anim={n2} variant="base">1.33 hr/hole</Node>
        <Arrow anim={n3} text="=" />
        <Node anim={n3}>16.0 hrs</Node>
        <Arrow anim={n4} text="+15%" />
        <Node anim={n5} variant="insight">low-ceiling insight</Node>
        <Arrow anim={n6} text="=" />
        <Node anim={n7} variant="final">18.4 hrs</Node>
      </div>
    </div>
  );
};

// ── Phase 3: labour drill screen ────────────────────────────
const LabourDrill: React.FC<{ baseFrame: number }> = ({ baseFrame }) => {
  const frame = useCurrentFrame();
  const headAnim = slideIn(frame, baseFrame + 6);
  const eqAnim = slideIn(frame, baseFrame + 20);
  const sampleAnim = slideIn(frame, baseFrame + 180);
  return (
    <div
      style={{
        flex: 1, overflow: "hidden", padding: 22,
      }}
    >
      <div
        style={{
          opacity: headAnim.opacity, transform: `translateY(${headAnim.ty}px)`,
          fontFamily: fonts.mono, fontSize: 10, color: dark.fgMuted,
          letterSpacing: "0.06em", textTransform: "uppercase", marginBottom: 14,
        }}
      >
        WorkItems · <span style={{ color: dark.machine }}>Item 04 Floor boxes</span> · Labour · <span style={{ color: dark.fg }}>Core-drill</span>
      </div>

      <div
        style={{
          opacity: headAnim.opacity, transform: `translateY(${headAnim.ty}px)`,
          backgroundColor: dark.ink2, border: `1px solid ${dark.hairline}`,
          borderRadius: 4, padding: "12px 16px", marginBottom: 14,
          display: "flex", justifyContent: "space-between", alignItems: "center",
        }}
      >
        <div>
          <div style={{ ...type.kicker, color: dark.machine, marginBottom: 4 }}>⛏ Labour · Task</div>
          <div style={{ fontSize: 15, color: dark.fg, fontWeight: 500 }}>Core-drill slab + sleeve</div>
        </div>
        <div
          style={{
            display: "grid", gridTemplateColumns: "auto auto", gap: 14, alignItems: "center",
          }}
        >
          <div>
            <div style={{ ...type.kicker, color: dark.fgMuted }}>Hours</div>
            <div style={{ fontFamily: fonts.mono, fontSize: 20, color: dark.machine, fontWeight: 600 }}>18.4</div>
          </div>
          <div>
            <div style={{ ...type.kicker, color: dark.fgMuted }}>Cost</div>
            <div style={{ fontFamily: fonts.mono, fontSize: 20, color: dark.fg, fontWeight: 600 }}>$1,693</div>
          </div>
        </div>
      </div>

      <div style={{ opacity: eqAnim.opacity, transform: `translateY(${eqAnim.ty}px)`, marginBottom: 14 }}>
        <LineageEquation baseFrame={baseFrame + 30} />
      </div>

      <div
        style={{
          opacity: sampleAnim.opacity, transform: `translateY(${sampleAnim.ty}px)`,
          backgroundColor: dark.ink2, border: `1px solid ${dark.hairline}`,
          borderRadius: 4, padding: "14px 16px",
        }}
      >
        <div style={{ ...type.kicker, color: dark.machine, marginBottom: 12 }}>Base productivity · 3-job sample</div>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 10 }}>
          {[
            ["Alder St · Nov '24", "1.42 hr/hole", "14 holes"],
            ["Chapelwood · Feb '25", "1.28 hr/hole", "8 holes"],
            ["Peachtree · Mar '25", "1.29 hr/hole", "16 holes"],
          ].map(([j, r, s], i) => (
            <div
              key={i}
              style={{
                backgroundColor: dark.ink3, padding: "10px 12px", borderRadius: 4,
              }}
            >
              <div style={{ ...type.kicker, color: dark.fgMuted, marginBottom: 4 }}>{j as string}</div>
              <div style={{ fontFamily: fonts.mono, fontSize: 15, color: dark.fg, fontWeight: 500 }}>{r as string}</div>
              <div style={{ fontFamily: fonts.mono, fontSize: 10, color: dark.fgMuted, marginTop: 3, letterSpacing: "0.04em" }}>{s as string}</div>
            </div>
          ))}
        </div>
        <div
          style={{
            marginTop: 14, display: "flex", alignItems: "center", gap: 14,
            padding: 12, backgroundColor: dark.ink3, borderRadius: 4,
          }}
        >
          <div style={{ ...type.kicker, color: dark.fgMuted, fontWeight: 600 }}>Base rate</div>
          <div
            style={{
              flex: 1, fontFamily: fonts.mono, fontSize: 11, color: dark.fg,
            }}
          >Mean <strong>1.33 hr/hole</strong> · std dev 6.4% · no outliers</div>
          <div style={{ fontFamily: fonts.mono, fontSize: 16, color: dark.machine, fontWeight: 600 }}>
            1.33 hr/hole
          </div>
        </div>
      </div>
    </div>
  );
};

// ── Phase 4: Provenance tree ────────────────────────────────
const ProvenanceTree: React.FC<{ baseFrame: number }> = ({ baseFrame }) => {
  const frame = useCurrentFrame();
  const rows = [
    { level: 0, pre: "", node: "$9,800", label: "sell price, item 04", accent: true },
    { level: 1, pre: "├─", node: "$7,800", label: "cost", muted: true },
    { level: 2, pre: "│   ├─", node: "$4,560", label: "labour (3 tasks)", machine: true },
    { level: 3, pre: "│   │   ├─", label: "$1,693 · Core-drill · Insight +15% × base 1.33 hr/hole · Past 3 jobs" },
    { level: 3, pre: "│   │   ├─", label: "$2,208 · Set box + unistrut · Insight +15% × base 2.0 hr/unit · Past 3 jobs" },
    { level: 3, pre: "│   │   └─", label: "$656 · Trim · base 0.67 hr/unit · Past 5 jobs · No adjustment" },
    { level: 2, pre: "│   └─", node: "$3,240", label: "items (5 lines)", machine: true },
    { level: 3, pre: "│       ├─", label: "$1,766 · Hubbell FBR-2 × 12 · Catalog · City Electric Apr 15" },
    { level: 3, pre: "│       ├─", label: "$538 · Unistrut P1000 × 24 · Catalog" },
    { level: 3, pre: "│       ├─", label: "$462 · Brass covers × 12 · Catalog" },
    { level: 3, pre: "│       ├─", label: "$252 · 12 AWG THHN × 1.5 · Catalog" },
    { level: 3, pre: "│       └─", label: "$222 · Misc connectors · Past 5 jobs lump-sum avg" },
    { level: 1, pre: "└─", node: "$2,000", label: "margin · 20.4%", machine: true },
    { level: 2, pre: "    └─", label: "Target 22% · accepted 20.4% due to labour adjustment", muted: true },
  ];

  return (
    <div
      style={{
        backgroundColor: dark.ink2, border: `1px solid ${dark.hairline}`,
        borderRadius: 4, padding: 22, marginBottom: 14,
      }}
    >
      <div
        style={{
          ...type.kicker, color: dark.machine, marginBottom: 16,
        }}
      >⚬ Provenance tree · sell $9,800</div>
      <div
        style={{
          fontFamily: fonts.mono, fontSize: 12, lineHeight: 1.9, color: dark.fg,
        }}
      >
        {rows.map((r, i) => {
          const appearAt = baseFrame + 10 + i * 14;
          const anim = slideIn(frame, appearAt, 4);
          return (
            <div
              key={i}
              style={{
                opacity: anim.opacity, transform: `translateY(${anim.ty}px)`,
                paddingLeft: r.level * 16,
              }}
            >
              <span style={{ color: dark.fgDim }}>{r.pre}</span>
              {r.node && (
                <>
                  {" "}
                  <span
                    style={{
                      color: r.accent ? dark.machine : r.machine ? dark.machine : dark.pass,
                      fontWeight: r.accent ? 600 : 500,
                    }}
                  >{r.node}</span>
                </>
              )}
              {" "}
              <span style={{ color: r.muted ? dark.fgMuted : dark.fg }}>{r.label}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
};

// ── Outro card ──────────────────────────────────────────────
const OutroCard: React.FC<{ baseFrame: number }> = ({ baseFrame }) => {
  const frame = useCurrentFrame();
  const rel = frame - baseFrame;
  const opacity = interpolate(rel, [0, 20], [0, 1], { extrapolateRight: "clamp" });
  const ty = interpolate(rel, [0, 30], [20, 0], { extrapolateRight: "clamp" });
  return (
    <AbsoluteFill
      style={{
        backgroundColor: dark.ink0, opacity,
        display: "flex", alignItems: "center", justifyContent: "center",
      }}
    >
      <div style={{ maxWidth: 920, textAlign: "center", transform: `translateY(${ty}px)` }}>
        <div style={{ ...type.kicker, color: dark.machine, fontSize: 12, marginBottom: 16 }}>
          Every number citable
        </div>
        <div
          style={{
            fontSize: 38, fontWeight: 600, lineHeight: 1.15,
            color: dark.fg, marginBottom: 24, letterSpacing: "-0.01em",
          }}
        >
          $9,800 = <span style={{ color: dark.machine }}>$4,560 labour</span><br />
          (3 tasks × past-job rates × <span style={{ color: dark.machine }}>+15% low-ceiling insight</span>)<br />
          + <span style={{ color: dark.machine }}>$3,240 items</span> (5 catalog lines)<br />
          + <span style={{ color: dark.machine }}>$2,000 margin</span>.
        </div>
        <div style={{ fontSize: 14, color: dark.fgMuted, lineHeight: 1.5, maxWidth: 600, margin: "0 auto" }}>
          No black boxes. Sarah can trace any number down to source,
          sample size, confidence, and evidence. That's the moat.
        </div>
      </div>
    </AbsoluteFill>
  );
};

// ── Chat content per phase ──────────────────────────────────
const ChatContent: React.FC<{ frame: number }> = ({ frame }) => {
  if (frame < T.P1_OVERVIEW[1]) {
    return (
      <>
        <div
          style={{
            ...type.kicker, fontSize: 10, color: dark.fgDim,
            letterSpacing: "0.08em", textAlign: "center", margin: "8px 0 10px",
          }}
        >— Tue · Apr 22 · 14:05 —</div>
        <ChatMsg who="Kerf · 14:05" avatar="K" speaker="kerf" appearFrame={30} text={<>Quote drafted. <strong style={{ color: dark.machine, fontWeight: 500 }}>7 items, $121,200, 21% avg.</strong> Floor boxes applied low-ceiling insight +15%.</>} />
        <ChatMsg who="Sarah · 14:07" avatar="S" speaker="user" appearFrame={130} text="The floor-box number looks high. Open 04 for me." />
      </>
    );
  }
  if (frame < T.P2_INSPECTOR_OPEN[1]) {
    return (
      <>
        <div
          style={{
            ...type.kicker, fontSize: 10, color: dark.fgDim,
            letterSpacing: "0.08em", textAlign: "center", margin: "8px 0 10px",
          }}
        >— Tue · Apr 22 · 14:08 —</div>
        <ChatMsg who="Sarah · 14:08" avatar="S" speaker="user" appearFrame={T.P2_INSPECTOR_OPEN[0] + 20} text="Walk me through WI 04." />
        <ChatMsg who="Kerf · 14:08" avatar="K" speaker="kerf" appearFrame={T.P2_INSPECTOR_OPEN[0] + 80} text={<>
          <strong style={{ color: dark.machine, fontWeight: 500 }}>12 floor boxes</strong>, receptacle + data.<br />
          <strong style={{ color: dark.machine, fontWeight: 500 }}>Labour:</strong> 50.4 hrs · $4,560 (+15% low-ceiling).<br />
          <strong style={{ color: dark.machine, fontWeight: 500 }}>Items:</strong> $3,240 catalog. <strong style={{ color: dark.machine, fontWeight: 500 }}>Margin:</strong> 22%.
        </>} />
        <ChatMsg who="Sarah · 14:09" avatar="S" speaker="user" appearFrame={T.P2_INSPECTOR_OPEN[0] + 180} text="Where's the 15% from?" />
      </>
    );
  }
  if (frame < T.P3_LABOUR_DRILL[1]) {
    return (
      <>
        <div
          style={{
            ...type.kicker, fontSize: 10, color: dark.fgDim,
            letterSpacing: "0.08em", textAlign: "center", margin: "8px 0 10px",
          }}
        >— Tue · Apr 22 · 14:10 —</div>
        <ChatMsg who="Sarah · 14:10" avatar="S" speaker="user" appearFrame={T.P3_LABOUR_DRILL[0] + 10} text="How did you get to 18.4 hours for core-drilling?" />
        <ChatMsg who="Kerf · 14:10" avatar="K" speaker="kerf" appearFrame={T.P3_LABOUR_DRILL[0] + 80} text={<>
          Base productivity <strong style={{ color: dark.machine, fontWeight: 500 }}>1.33 hr/hole</strong> from your last 3 jobs × 12 = 16.0 hrs. <strong style={{ color: dark.machine, fontWeight: 500 }}>+15%</strong> low-ceiling insight = <strong style={{ color: dark.machine, fontWeight: 500 }}>18.4 hrs</strong>.
        </>} />
        <ChatMsg who="Sarah · 14:11" avatar="S" speaker="user" appearFrame={T.P3_LABOUR_DRILL[0] + 200} text="Which 3 jobs?" />
        <ChatMsg who="Kerf · 14:11" avatar="K" speaker="kerf" appearFrame={T.P3_LABOUR_DRILL[0] + 260} text={<>Alder St Nov · Chapelwood Feb · Peachtree Mar. All slab-on-grade.</>} />
      </>
    );
  }
  // P4 and beyond
  return (
    <>
      <div
        style={{
          ...type.kicker, fontSize: 10, color: dark.fgDim,
          letterSpacing: "0.08em", textAlign: "center", margin: "8px 0 10px",
        }}
      >— Tue · Apr 22 · 14:25 —</div>
      <ChatMsg who="Sarah · 14:25" avatar="S" speaker="user" appearFrame={T.P4_PROVENANCE[0] + 10} text="Show me the full provenance for $9,800." />
      <ChatMsg who="Kerf · 14:25" avatar="K" speaker="kerf" appearFrame={T.P4_PROVENANCE[0] + 80} text={<>
        Full tree on the right. Three origins — <strong style={{ color: dark.machine, fontWeight: 500 }}>past jobs</strong> (base rates), <strong style={{ color: dark.machine, fontWeight: 500 }}>insight</strong> (+15% low-ceiling), <strong style={{ color: dark.machine, fontWeight: 500 }}>catalog</strong> (items). No stated numbers on this item.
      </>} />
    </>
  );
};

// ── Main composition ────────────────────────────────────────
export const QuotingDetailFlow: React.FC = () => {
  const frame = useCurrentFrame();

  // Phases as opacity windows
  const p1Op = frame < T.P2_INSPECTOR_OPEN[0] + 15 ? 1 : interpolate(frame, [T.P2_INSPECTOR_OPEN[0], T.P2_INSPECTOR_OPEN[0] + 20], [1, 0.3], { extrapolateRight: "clamp", extrapolateLeft: "clamp" });
  const inspectorOp = frame >= T.P2_INSPECTOR_OPEN[0] - 10
    ? (frame < T.P3_LABOUR_DRILL[0]
        ? interpolate(frame, [T.P2_INSPECTOR_OPEN[0] - 10, T.P2_INSPECTOR_OPEN[0] + 10], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" })
        : interpolate(frame, [T.P3_LABOUR_DRILL[0], T.P3_LABOUR_DRILL[0] + 20], [1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }))
    : 0;

  const labourOp = frame >= T.P3_LABOUR_DRILL[0] - 10
    ? (frame < T.P4_PROVENANCE[0]
        ? interpolate(frame, [T.P3_LABOUR_DRILL[0] - 10, T.P3_LABOUR_DRILL[0] + 10], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" })
        : interpolate(frame, [T.P4_PROVENANCE[0], T.P4_PROVENANCE[0] + 20], [1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }))
    : 0;

  const provOp = frame >= T.P4_PROVENANCE[0] - 10
    ? (frame < T.P5_OUTRO[0]
        ? interpolate(frame, [T.P4_PROVENANCE[0] - 10, T.P4_PROVENANCE[0] + 15], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" })
        : interpolate(frame, [T.P5_OUTRO[0], T.P5_OUTRO[0] + 15], [1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }))
    : 0;

  const outroOp = frame >= T.P5_OUTRO[0] - 10
    ? interpolate(frame, [T.P5_OUTRO[0] - 10, T.P5_OUTRO[0] + 15], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" })
    : 0;

  // Highlight row 04 during P1 end
  const highlightRow = frame >= T.P1_OVERVIEW[1] - 30 ? 3 : undefined;

  // Inspector panel show/hide
  const showInspector = frame >= T.P2_INSPECTOR_OPEN[0] - 10 && frame < T.P3_LABOUR_DRILL[0] + 20;
  const inspectorSlide = showInspector ? slideInX(frame, T.P2_INSPECTOR_OPEN[0] - 10, 60) : { opacity: 0, tx: 60 };

  const showLabourDrill = frame >= T.P2_INSPECTOR_OPEN[0] + 5 * F;
  const showProvenance = frame >= T.P4_PROVENANCE[0];

  return (
    <AbsoluteFill style={{ backgroundColor: dark.ink0, fontFamily: fonts.sans }}>
      {/* Outro */}
      {frame >= T.P5_OUTRO[0] - 10 && (
        <div style={{ position: "absolute", inset: 0, opacity: outroOp, zIndex: 10 }}>
          <OutroCard baseFrame={T.P5_OUTRO[0]} />
        </div>
      )}

      {/* Main app */}
      <div
        style={{
          position: "absolute", inset: 0,
          display: "flex",
          opacity: 1 - outroOp,
        }}
      >
        <IconRail />
        <ChatPane ctxLabel="Quote · Maple Ridge">
          <ChatContent frame={frame} />
        </ChatPane>
        <div
          style={{
            flex: 1, backgroundColor: dark.ink0,
            display: "flex", flexDirection: "column", overflow: "hidden",
          }}
        >
          <Chrome />
          <div style={{ flex: 1, overflow: "hidden", position: "relative" }}>
            {/* P1: Quote overview */}
            {frame < T.P3_LABOUR_DRILL[0] && (
              <div
                style={{
                  position: "absolute", inset: 0, overflow: "auto",
                  padding: 22,
                  display: "grid",
                  gridTemplateColumns: showInspector ? "1fr 440px" : "1fr",
                  gap: 18,
                }}
              >
                <div style={{ opacity: p1Op, transition: "opacity 400ms ease" }}>
                  <div
                    style={{
                      ...type.kicker, color: dark.machine, marginBottom: 10, fontSize: 10,
                    }}
                  >◉ Dashboard · QUOTED — the quote document</div>
                  <QuoteTable highlightRow={highlightRow} extraDim={showInspector} />
                </div>
                {showInspector && (
                  <div
                    style={{
                      opacity: inspectorSlide.opacity * inspectorOp,
                      transform: `translateX(${inspectorSlide.tx}px)`,
                    }}
                  >
                    <InspectorPanel baseFrame={T.P2_INSPECTOR_OPEN[0]} showLabourDrill={showLabourDrill} showProvenance={false} />
                  </div>
                )}
              </div>
            )}

            {/* P3: Labour drill */}
            {frame >= T.P3_LABOUR_DRILL[0] - 10 && frame < T.P4_PROVENANCE[0] + 20 && (
              <div
                style={{
                  position: "absolute", inset: 0, overflow: "auto",
                  opacity: labourOp,
                }}
              >
                <LabourDrill baseFrame={T.P3_LABOUR_DRILL[0]} />
              </div>
            )}

            {/* P4: Provenance tree */}
            {frame >= T.P4_PROVENANCE[0] - 10 && (
              <div
                style={{
                  position: "absolute", inset: 0, overflow: "auto",
                  opacity: provOp, padding: 22,
                }}
              >
                <div
                  style={{
                    ...type.kicker, color: dark.machine, marginBottom: 10, fontSize: 10,
                  }}
                >◉ Provenance · WI 04 · sell $9,800</div>
                <ProvenanceTree baseFrame={T.P4_PROVENANCE[0]} />
              </div>
            )}
          </div>
        </div>
      </div>
    </AbsoluteFill>
  );
};
