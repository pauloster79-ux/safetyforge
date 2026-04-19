import React from "react";
import {
  AbsoluteFill,
  useCurrentFrame,
  interpolate,
  spring,
  Easing,
} from "remotion";
import { dark, fonts, type } from "../components/dark-styles";
import {
  IconRail,
  TopHeader,
  TabBar,
  MetricTile,
  Section,
  ChatPane,
  ChatMsg,
  ChatEvent,
  DashKicker,
  ProgressBar,
  ProjectState,
} from "../components/ProjectFrame";

// ── Timing (at 30fps) ───────────────────────────────────────
const F = 30;
export const LIFECYCLE_DURATION_FRAMES = 81 * F; // 81 seconds

const T = {
  INTRO_END: 3 * F,
  LEAD_START: 3 * F,
  LEAD_END: 12 * F,              // 9s
  QUOTED_START: 14 * F,          // 2s transition
  QUOTED_END: 28 * F,            // 14s
  ACCEPTED_START: 30 * F,        // 2s transition
  ACCEPTED_END: 40 * F,          // 10s
  ACTIVE_START: 42 * F,          // 2s transition
  ACTIVE_END: 60 * F,            // 18s
  PC_START: 62 * F,              // 2s transition
  PC_END: 72 * F,                // 10s
  CLOSED_START: 74 * F,          // 2s transition
  CLOSED_END: 81 * F,            // 7s
};

type Phase = "INTRO" | "LEAD" | "QUOTED" | "ACCEPTED" | "ACTIVE" | "PC" | "CLOSED";

const phaseForFrame = (frame: number): Phase => {
  if (frame < T.INTRO_END) return "INTRO";
  if (frame < T.LEAD_END) return "LEAD";
  if (frame < T.QUOTED_END) return "QUOTED";
  if (frame < T.ACCEPTED_END) return "ACCEPTED";
  if (frame < T.ACTIVE_END) return "ACTIVE";
  if (frame < T.PC_END) return "PC";
  return "CLOSED";
};

// Cross-fade helper: returns opacity 0→1→1→0 across a window
const fadeWindow = (frame: number, start: number, end: number, fadeIn = 20, fadeOut = 20) => {
  if (frame < start - fadeIn || frame > end + fadeOut) return 0;
  if (frame < start) return interpolate(frame, [start - fadeIn, start], [0, 1], { extrapolateRight: "clamp" });
  if (frame > end) return interpolate(frame, [end, end + fadeOut], [1, 0], { extrapolateLeft: "clamp" });
  return 1;
};

// Slide-in helper
const slideIn = (frame: number, appearAt: number, distance = 16) => {
  const rel = frame - appearAt;
  if (rel < 0) return { opacity: 0, ty: distance };
  const opacity = interpolate(rel, [0, 12], [0, 1], { extrapolateRight: "clamp" });
  const s = spring({ frame: rel, fps: 30, config: { damping: 18, stiffness: 120 } });
  return { opacity, ty: (1 - s) * distance };
};

// ── Intro card ──────────────────────────────────────────────
const IntroCard: React.FC = () => {
  const frame = useCurrentFrame();
  const opacity = fadeWindow(frame, 0, T.INTRO_END - 15, 10, 15);
  const scale = interpolate(frame, [0, 20], [0.97, 1], { extrapolateRight: "clamp" });
  return (
    <AbsoluteFill
      style={{
        backgroundColor: dark.ink0, opacity,
        display: "flex", alignItems: "center", justifyContent: "center",
        transform: `scale(${scale})`,
      }}
    >
      <div style={{ maxWidth: 920, textAlign: "center" }}>
        <div style={{ ...type.kicker, color: dark.machine, fontSize: 12, marginBottom: 16 }}>
          Kerf · Project Lifecycle · Option C
        </div>
        <div
          style={{
            fontSize: 48, fontWeight: 600, lineHeight: 1.1,
            letterSpacing: "-0.01em", color: dark.fg, marginBottom: 20,
          }}
        >
          How the same frame reshapes<br />
          <span style={{ color: dark.machine }}>across a project's life</span>
        </div>
        <div style={{ fontSize: 16, color: dark.fgMuted, lineHeight: 1.5, maxWidth: 640, margin: "0 auto" }}>
          Maple Ridge Phase II. Six states. One frame.<br />
          Dashboard content reshapes. Tabs stay. Sarah stays in control.
        </div>
      </div>
    </AbsoluteFill>
  );
};

// ── Tab definitions (state-aware) ───────────────────────────
const tabsFor = (phase: Phase) => {
  const base = [
    { label: "◉ Dashboard", active: true },
    { label: "⚒ Scope", count: phase === "LEAD" ? undefined : "7", disabled: phase === "LEAD" },
    { label: "⬒ Variations", count: phase === "ACTIVE" ? "1" : phase === "PC" || phase === "CLOSED" ? "1" : undefined, disabled: phase === "LEAD" || phase === "QUOTED" || phase === "ACCEPTED" },
    { label: "◎ Timeline" },
    { label: "$ Money", disabled: phase === "LEAD" || phase === "QUOTED" },
    { label: "▤ Contract", disabled: phase === "LEAD" },
    { label: "⚘ Docs" },
    { label: "⚐ People", count: phase === "LEAD" ? "1" : phase === "QUOTED" ? "2" : phase === "ACCEPTED" ? "3" : "5" },
  ];
  return base;
};

// ── LEAD dashboard ──────────────────────────────────────────
const LeadDashboard: React.FC<{ baseFrame: number }> = ({ baseFrame }) => {
  const frame = useCurrentFrame();
  const actionAnim = slideIn(frame, baseFrame + 10);
  const p1 = slideIn(frame, baseFrame + 40);
  const p2 = slideIn(frame, baseFrame + 55);
  return (
    <div style={{ padding: 22 }}>
      <DashKicker>LEAD</DashKicker>

      <div
        style={{
          opacity: actionAnim.opacity,
          transform: `translateY(${actionAnim.ty}px)`,
          backgroundColor: dark.machineWash,
          padding: "14px 16px", borderRadius: 4,
          border: `1px solid ${dark.machine}`, marginBottom: 14,
        }}
      >
        <div style={{ ...type.kicker, color: dark.machine, marginBottom: 8 }}>⚡ Next action</div>
        <div style={{ fontSize: 14, color: dark.fg, lineHeight: 1.5, marginBottom: 10 }}>
          <strong style={{ color: dark.machine, fontWeight: 500 }}>Site walk · Thursday · 09:00</strong> — Maple Ridge Ph II. I'll prep a diff against Peachtree's scope the morning of, ready for voice capture on-site.
        </div>
        <div style={{ display: "flex", gap: 8 }}>
          <button
            style={{
              padding: "7px 12px", backgroundColor: dark.machine, color: dark.ink0,
              border: `1px solid ${dark.machine}`, borderRadius: 3,
              fontFamily: fonts.mono, fontSize: 10.5, fontWeight: 600,
              letterSpacing: "0.08em", textTransform: "uppercase",
            }}
          >Add to calendar</button>
          <button
            style={{
              padding: "7px 12px", backgroundColor: "transparent", color: dark.fg,
              border: `1px solid ${dark.hairline}`, borderRadius: 3,
              fontFamily: fonts.mono, fontSize: 10.5, fontWeight: 600,
              letterSpacing: "0.08em", textTransform: "uppercase",
            }}
          >Change time</button>
        </div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14 }}>
        <div style={{ opacity: p1.opacity, transform: `translateY(${p1.ty}px)` }}>
          <Section num="" title="⚑ From Peachtree" chip="Ph I · reference">
            <div style={{ padding: "10px 16px", fontSize: 12 }}>
              <Row k="Final value" v="$116,400 · 1 variation" />
              <Row k="Margin" v="19.2% realised (18% bid)" />
              <Row k="Insights" v={<>Floor-box insight <strong style={{ color: dark.machine }}>+15% low-ceiling</strong></>} />
              <Row k="Notes" v="Rough-1st inspection was late · +10d buffer" last />
            </div>
          </Section>
        </div>
        <div style={{ opacity: p2.opacity, transform: `translateY(${p2.ty}px)` }}>
          <Section num="" title="⚐ Client">
            <div style={{ padding: "10px 16px", fontSize: 12 }}>
              <Row k="Company" v="Maple Ridge Dev. Corp." />
              <Row k="Contact" v="Gary Pemberton · PM" />
              <Row k="History" v="1 project · Peachtree · paid on time" />
              <Row k="Referral" v="Self — called Sarah direct" last />
            </div>
          </Section>
        </div>
      </div>
    </div>
  );
};

const Row: React.FC<{ k: string; v: React.ReactNode; last?: boolean }> = ({ k, v, last }) => (
  <div
    style={{
      display: "grid", gridTemplateColumns: "90px 1fr",
      padding: "7px 0", gap: 14, borderBottom: last ? "none" : `1px solid ${dark.hairline}`,
    }}
  >
    <div style={{ ...type.kicker, color: dark.fgMuted, paddingTop: 2 }}>{k}</div>
    <div style={{ color: dark.fg, lineHeight: 1.45 }}>{v}</div>
  </div>
);

// ── QUOTED dashboard ────────────────────────────────────────
const QuotedDashboard: React.FC<{ baseFrame: number }> = ({ baseFrame }) => {
  const frame = useCurrentFrame();
  const metricsAnim = slideIn(frame, baseFrame + 10);
  const scopeAnim = slideIn(frame, baseFrame + 30);
  const termsAnim = slideIn(frame, baseFrame + 70);
  return (
    <div style={{ padding: 22 }}>
      <DashKicker>QUOTED — the quote document</DashKicker>
      <div
        style={{
          opacity: metricsAnim.opacity, transform: `translateY(${metricsAnim.ty}px)`,
          display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 12, marginBottom: 18,
        }}
      >
        <MetricTile kicker="Quote Total" value="$121,200" primary />
        <MetricTile kicker="Labour" value="$59,860" />
        <MetricTile kicker="Items" value="$37,740" />
        <MetricTile kicker="Avg Margin" value="21%" valueColor={dark.pass} />
      </div>
      <div style={{ opacity: scopeAnim.opacity, transform: `translateY(${scopeAnim.ty}px)` }}>
        <Section num="01" title="⚒ Work Items" action="+ Item" actionPrimary>
          <div style={{ padding: "8px 16px" }}>
            {[
              ["01", "Mobilization & site prep", "1 LS", "18%", "$11,200"],
              ["02", "Rough electrical — 1st floor", "32 PT", "22%", "$30,500"],
              ["03", "Panel upgrade — 200A service", "1 LS", "20%", "$16,300"],
              ["04", "Floor boxes — receptacle + data", "12 EA", "22%", "$9,800"],
              ["05", "Rough electrical — 2nd floor", "28 PT", "21%", "$24,800"],
              ["06", "Finish — 1st + 2nd", "1 LS", "24%", "$20,400"],
              ["07", "Testing & commissioning", "1 LS", "18%", "$8,200"],
            ].map(([n, d, q, m, s], i, arr) => (
              <div
                key={i}
                style={{
                  display: "grid",
                  gridTemplateColumns: "28px 1fr 80px 60px 80px",
                  padding: "9px 0", gap: 12, alignItems: "center",
                  borderBottom: i === arr.length - 1 ? "none" : `1px solid ${dark.hairline}`,
                  fontSize: 12,
                }}
              >
                <span style={{ fontFamily: fonts.mono, color: dark.fgDim }}>{n}</span>
                <span style={{ color: dark.fg }}>
                  {d}
                  {(n === "02" || n === "04") && (
                    <span
                      style={{
                        marginLeft: 6, fontFamily: fonts.mono, fontSize: 9, color: dark.fgMuted,
                        backgroundColor: dark.ink3, padding: "1px 5px", borderRadius: 2,
                        letterSpacing: "0.06em",
                      }}
                    >{n === "04" ? "⚑ +15% insight" : "← Peachtree"}</span>
                  )}
                </span>
                <span style={{ fontFamily: fonts.mono, textAlign: "right", color: dark.fgMuted }}>{q}</span>
                <span style={{ fontFamily: fonts.mono, textAlign: "right", color: dark.pass, fontWeight: 500 }}>{m}</span>
                <span style={{ fontFamily: fonts.mono, textAlign: "right", color: dark.machine, fontWeight: 500 }}>{s}</span>
              </div>
            ))}
          </div>
        </Section>
      </div>

      <div
        style={{
          opacity: termsAnim.opacity, transform: `translateY(${termsAnim.ty}px)`,
          display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14,
        }}
      >
        <Section num="02" title="⚠ Assumptions" chip="2 Variation">
          <div style={{ padding: "10px 16px", fontSize: 12 }}>
            <Row k="Programme" v={<>Site 5 days/wk, 0700–1700. <span style={{ color: dark.machine, fontSize: 11 }}>⬒ Weekend = T&amp;M</span></>} />
            <Row k="Access" v={<>Material hoist 0730–0930. <span style={{ color: dark.machine, fontSize: 11 }}>⬒ Delay = variation</span></>} />
            <Row k="Power" v="Temp 200A at panel B2 by GC." />
            <Row k="Drawings" v="Rev 4 IFC · 03/28." last />
          </div>
        </Section>
        <Section num="03" title="⊘ Exclusions">
          <div style={{ padding: "10px 16px", fontSize: 12 }}>
            <Row k="Scope" v="Fire alarm — by others." />
            <Row k="Scope" v="Permits — reimbursable at cost + 5%." />
            <Row k="Environ." v="Hazardous abatement — excluded." last />
          </div>
        </Section>
      </div>
    </div>
  );
};

// ── ACCEPTED dashboard ──────────────────────────────────────
const AcceptedDashboard: React.FC<{ baseFrame: number }> = ({ baseFrame }) => {
  const frame = useCurrentFrame();
  const refAnim = slideIn(frame, baseFrame + 8);
  const metricsAnim = slideIn(frame, baseFrame + 24);
  const checkAnim = slideIn(frame, baseFrame + 48);

  const rowStagger = (i: number) => slideIn(frame, baseFrame + 70 + i * 15, 10);

  return (
    <div style={{ padding: 22 }}>
      <DashKicker>ACCEPTED — pre-start</DashKicker>
      <div
        style={{
          opacity: refAnim.opacity, transform: `translateY(${refAnim.ty}px)`,
          backgroundColor: dark.ink1, border: `1px solid ${dark.hairline}`,
          borderRadius: 4, padding: "10px 16px", display: "flex",
          gap: 20, marginBottom: 14, alignItems: "center", fontSize: 11.5,
        }}
      >
        <span style={{ ...type.kicker, color: dark.fgMuted }}>▤ Contract v1 locked</span>
        <Item>🔒 <strong>$121,200</strong> lump sum</Item>
        <Item>Retention <strong>5%</strong></Item>
        <Item>Warranty <strong>12 mo</strong></Item>
        <Item>Payment <strong>30d net</strong></Item>
        <Item>Signed <strong>Mon 16:22</strong></Item>
      </div>

      <div
        style={{
          opacity: metricsAnim.opacity, transform: `translateY(${metricsAnim.ty}px)`,
          display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 12, marginBottom: 18,
        }}
      >
        <MetricTile kicker="Planned start" value="Mon May 5" primary sub="7 days away" />
        <MetricTile kicker="Deposit" value="$12,120" sub="Sent · awaiting" subColor={dark.warn} />
        <MetricTile kicker="Duration" value="~ 8 weeks" sub="Peachtree baseline" />
        <MetricTile kicker="Crew planned" value="4–5" sub="Mike lead + 3 JM" />
      </div>

      <div style={{ opacity: checkAnim.opacity, transform: `translateY(${checkAnim.ty}px)` }}>
        <Section title="⚡ Before we start" chip="3 of 5 ready">
          {[
            ["Deposit invoice sent to Gary — $12,120", "Awaiting", dark.warn, dark.warnBg],
            ["Phoenix electrical permit — drafted", "Hold", dark.warn, dark.warnBg],
            ["Material order — panels + 1,200 LF wire", "Queued", dark.pass, dark.passBg],
            ["Start date confirmed with GC — Mon May 5", "Confirmed", dark.pass, dark.passBg],
            ["Crew assigned & briefed", "Ready", dark.pass, dark.passBg],
          ].map(([label, chip, color, bg], i, arr) => {
            const anim = rowStagger(i);
            return (
              <div
                key={i}
                style={{
                  padding: "10px 16px",
                  borderBottom: i === arr.length - 1 ? "none" : `1px solid ${dark.hairline}`,
                  display: "flex", justifyContent: "space-between",
                  alignItems: "center", fontSize: 12.5,
                  opacity: anim.opacity, transform: `translateY(${anim.ty}px)`,
                }}
              >
                <div style={{ color: dark.fg }}>{label as string}</div>
                <span
                  style={{
                    padding: "2px 7px", borderRadius: 3,
                    fontFamily: fonts.mono, fontSize: 9,
                    letterSpacing: "0.08em", fontWeight: 600,
                    textTransform: "uppercase",
                    backgroundColor: bg as string, color: color as string,
                  }}
                >{chip as string}</span>
              </div>
            );
          })}
        </Section>
      </div>
    </div>
  );
};

const Item: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <span
    style={{
      color: dark.fgMuted, fontFamily: fonts.mono,
      fontSize: 11, letterSpacing: "0.02em",
    }}
  >{children}</span>
);

// ── ACTIVE dashboard ────────────────────────────────────────
const ActiveDashboard: React.FC<{ baseFrame: number }> = ({ baseFrame }) => {
  const frame = useCurrentFrame();
  const metricsAnim = slideIn(frame, baseFrame + 8);

  // V1 draft arrives at a specific point
  const v1DraftAt = baseFrame + 200;
  const v1Anim = slideIn(frame, v1DraftAt, 20);

  const progressAnim = slideIn(frame, baseFrame + 45);
  const todayAnim = slideIn(frame, baseFrame + 65);

  // Progress bars fill over the scene
  const progressPcts = [
    interpolate(frame, [baseFrame, baseFrame + 80], [100, 100], { extrapolateRight: "clamp" }),
    interpolate(frame, [baseFrame, baseFrame + 180], [70, 85], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }),
    interpolate(frame, [baseFrame, baseFrame + 80], [100, 100], { extrapolateRight: "clamp" }),
    interpolate(frame, [baseFrame, baseFrame + 220], [40, 60], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }),
    interpolate(frame, [baseFrame, baseFrame + 400], [0, 0], { extrapolateRight: "clamp" }),
  ];

  return (
    <div style={{ padding: 22 }}>
      <DashKicker>ACTIVE — execution</DashKicker>

      <div
        style={{
          opacity: metricsAnim.opacity, transform: `translateY(${metricsAnim.ty}px)`,
          display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 12, marginBottom: 14,
        }}
      >
        <MetricTile kicker="Complete" value={<>45<span style={{ fontSize: 14, opacity: 0.6 }}> %</span></>} primary sub="2 days behind" />
        <MetricTile kicker="Spent · Budget" value="$65,200" sub="$4,200 over · floor boxes" subColor={dark.fail} />
        <MetricTile kicker="Invoiced · Paid" value="$42,420" valueColor={dark.pass} sub="M1 + M2 cleared" />
        <MetricTile kicker="Next Milestone" value={<span style={{ fontSize: 16 }}>Rough 2nd · May 12</span>} sub="Inspection booked" />
      </div>

      {/* Needs your call row — V1 slides in */}
      {frame >= v1DraftAt - 30 && (
        <div style={{ opacity: v1Anim.opacity, transform: `translateY(${v1Anim.ty}px)`, marginBottom: 14 }}>
          <Section title="⚡ Needs your call" accent>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14, padding: "14px 16px" }}>
              <div
                style={{
                  backgroundColor: dark.ink3, padding: "12px 14px",
                  borderRadius: 4, borderLeft: `3px solid ${dark.machine}`,
                }}
              >
                <div style={{ ...type.kicker, color: dark.machine, marginBottom: 6 }}>V1 · Draft</div>
                <div style={{ fontSize: 13, color: dark.fg, marginBottom: 6 }}>
                  4 additional slab cores — south hallway · <strong style={{ color: dark.machine }}>+$1,840</strong> · +0.5 day
                </div>
                <div style={{ fontSize: 11.5, color: dark.fgMuted, lineHeight: 1.5 }}>
                  Kerf drafted from daily logs + your chat. Evidence chain attached. Review and issue to Maple Ridge Dev.
                </div>
                <div style={{ display: "flex", gap: 8, marginTop: 10 }}>
                  <button
                    style={{
                      padding: "5px 10px", backgroundColor: dark.machine, color: dark.ink0,
                      border: `1px solid ${dark.machine}`, borderRadius: 3,
                      fontFamily: fonts.mono, fontSize: 10, fontWeight: 600,
                      letterSpacing: "0.06em", textTransform: "uppercase",
                    }}
                  >Review &amp; issue</button>
                  <button
                    style={{
                      padding: "5px 10px", backgroundColor: dark.ink4, color: dark.fg,
                      border: `1px solid ${dark.hairline}`, borderRadius: 3,
                      fontFamily: fonts.mono, fontSize: 10, fontWeight: 600,
                      letterSpacing: "0.06em", textTransform: "uppercase",
                    }}
                  >Edit</button>
                </div>
              </div>
              <div
                style={{
                  backgroundColor: dark.ink3, padding: "12px 14px",
                  borderRadius: 4, borderLeft: `3px solid ${dark.warn}`,
                }}
              >
                <div style={{ ...type.kicker, color: dark.warn, marginBottom: 6 }}>Labour variance</div>
                <div style={{ fontSize: 13, color: dark.fg, marginBottom: 6 }}>
                  Floor boxes <strong style={{ color: dark.warn }}>+$2,400 over</strong> estimate
                </div>
                <div style={{ fontSize: 11.5, color: dark.fgMuted, lineHeight: 1.5 }}>
                  Partly covered by V1. If V1 issues + approves, net is <strong style={{ color: dark.fg }}>$560</strong> over. If withdrawn, re-bid the floor-box insight.
                </div>
              </div>
            </div>
          </Section>
        </div>
      )}

      <div
        style={{
          display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14,
        }}
      >
        <div style={{ opacity: progressAnim.opacity, transform: `translateY(${progressAnim.ty}px)` }}>
          <Section title="⚒ Progress by WorkItem">
            <div style={{ padding: "4px 0" }}>
              {[
                ["01", "Mobilization & site prep", progressPcts[0], dark.pass],
                ["02", "Rough electrical — 1st floor", progressPcts[1], dark.machine],
                ["03", "Panel upgrade — 200A", progressPcts[2], dark.pass],
                ["04", "Floor boxes — receptacle + data", progressPcts[3], dark.machine],
                ["05", "Rough electrical — 2nd floor", progressPcts[4], dark.ink3],
              ].map(([n, d, pct, color], i) => (
                <div
                  key={i}
                  style={{
                    display: "grid", gridTemplateColumns: "28px 1fr 160px",
                    padding: "9px 16px", gap: 12, alignItems: "center",
                    borderBottom: i === 4 ? "none" : `1px solid ${dark.hairline}`,
                    fontSize: 12,
                  }}
                >
                  <span style={{ fontFamily: fonts.mono, color: dark.fgDim }}>{n as string}</span>
                  <span style={{ color: dark.fg }}>{d as string}</span>
                  <ProgressBar pct={Math.round(pct as number)} color={color as string} />
                </div>
              ))}
            </div>
          </Section>
        </div>
        <div style={{ opacity: todayAnim.opacity, transform: `translateY(${todayAnim.ty}px)` }}>
          <Section title="◉ Today">
            <div style={{ padding: "4px 16px" }}>
              {[
                ["14:23", <>{" "}<strong style={{ color: dark.machine, fontWeight: 500 }}>V1 drafted</strong> · 4 cores · +$1,840{" "}</>, "Kerf · from chat"],
                ["11:40", "Daily log · rough 1st at 85% · crew 4", "Mike · voice"],
                ["09:15", "2 photos — floor box cores", "Mike"],
                ["07:12", "4 crew clocked in", "GPS"],
              ].map(([when, what, actor], i, arr) => (
                <div
                  key={i}
                  style={{
                    display: "grid", gridTemplateColumns: "100px 1fr",
                    padding: "9px 0", gap: 14,
                    borderBottom: i === arr.length - 1 ? "none" : `1px solid ${dark.hairline}`,
                    fontSize: 12,
                  }}
                >
                  <span style={{ fontFamily: fonts.mono, fontSize: 10, color: dark.fgMuted, letterSpacing: "0.06em", textTransform: "uppercase" }}>{when as string}</span>
                  <span style={{ color: dark.fg, lineHeight: 1.5 }}>
                    {what as React.ReactNode}
                    <span
                      style={{
                        fontFamily: fonts.mono, fontSize: 10, color: dark.fgDim,
                        letterSpacing: "0.06em", textTransform: "uppercase", marginLeft: 6,
                      }}
                    >{actor as string}</span>
                  </span>
                </div>
              ))}
            </div>
          </Section>
        </div>
      </div>
    </div>
  );
};

// ── PC dashboard ────────────────────────────────────────────
const PcDashboard: React.FC<{ baseFrame: number }> = ({ baseFrame }) => {
  const frame = useCurrentFrame();
  const metricsAnim = slideIn(frame, baseFrame + 8);
  const closeAnim = slideIn(frame, baseFrame + 30);
  const insightAnim = slideIn(frame, baseFrame + 70);
  return (
    <div style={{ padding: 22 }}>
      <DashKicker>PC — closeout &amp; DLP</DashKicker>
      <div
        style={{
          opacity: metricsAnim.opacity, transform: `translateY(${metricsAnim.ty}px)`,
          display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 12, marginBottom: 14,
        }}
      >
        <MetricTile kicker="PC date" value={<span style={{ fontSize: 18 }}>Jun 11 2026</span>} primary sub="Certificate snapshotted" />
        <MetricTile kicker="Final value" value="$123,040" valueColor={dark.pass} sub="v1 + V1 approved" />
        <MetricTile kicker="Net margin" value="20.4%" valueColor={dark.pass} sub="vs 21% bid" />
        <MetricTile kicker="DLP ends" value={<span style={{ fontSize: 18 }}>Jun 11 2027</span>} sub="10.5 months left" />
      </div>

      <div style={{ opacity: closeAnim.opacity, transform: `translateY(${closeAnim.ty}px)`, display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14, marginBottom: 14 }}>
        <Section title="⬒ Close-out status" chip="All clear" chipColor="pass">
          {[
            ["Final invoice paid — $12,120", "Paid Jun 14", dark.pass, dark.passBg],
            ["Retention held — 5% · $6,152", "Held", dark.machine, dark.machineWash],
            ["Punch list — 3 items", "All closed", dark.pass, dark.passBg],
            ["V1 approved & installed", "Complete", dark.pass, dark.passBg],
            ["Gary's PC acknowledgment", "Signed Jun 12", dark.pass, dark.passBg],
            ["Close-out docs delivered", "Delivered", dark.pass, dark.passBg],
          ].map(([l, c, fg, bg], i, arr) => (
            <div
              key={i}
              style={{
                padding: "10px 16px",
                borderBottom: i === arr.length - 1 ? "none" : `1px solid ${dark.hairline}`,
                display: "flex", justifyContent: "space-between",
                alignItems: "center", fontSize: 12.5,
              }}
            >
              <div style={{ color: dark.fg }}>{l as string}</div>
              <span
                style={{
                  padding: "2px 7px", borderRadius: 3,
                  fontFamily: fonts.mono, fontSize: 9,
                  letterSpacing: "0.08em", fontWeight: 600,
                  textTransform: "uppercase",
                  backgroundColor: bg as string, color: fg as string,
                }}
              >{c as string}</span>
            </div>
          ))}
        </Section>
        <Section title="⚑ DLP · defects register" chip="1 reported · 0 open" chipColor="pass">
          <div style={{ padding: "4px 16px" }}>
            {[
              ["Wed Jul 16", "Reception can flickering — reported by Gary", "Phone · Mike"],
              ["Fri Jul 18", <><strong style={{ color: dark.machine, fontWeight: 500 }}>Resolved</strong> — driver swapped, 0.3hr</>, "Mike · photo"],
            ].map(([when, what, actor], i, arr) => (
              <div
                key={i}
                style={{
                  display: "grid", gridTemplateColumns: "100px 1fr",
                  padding: "9px 0", gap: 14,
                  borderBottom: i === arr.length - 1 ? "none" : `1px solid ${dark.hairline}`,
                  fontSize: 12,
                }}
              >
                <span style={{ fontFamily: fonts.mono, fontSize: 10, color: dark.fgMuted, letterSpacing: "0.06em", textTransform: "uppercase" }}>{when as string}</span>
                <span style={{ color: dark.fg, lineHeight: 1.5 }}>
                  {what as React.ReactNode}
                  <span
                    style={{
                      fontFamily: fonts.mono, fontSize: 10, color: dark.fgDim,
                      letterSpacing: "0.06em", textTransform: "uppercase", marginLeft: 6,
                    }}
                  >{actor as string}</span>
                </span>
              </div>
            ))}
          </div>
        </Section>
      </div>

      <div style={{ opacity: insightAnim.opacity, transform: `translateY(${insightAnim.ty}px)` }}>
        <Section title="⚭ Insights harvested from this job" chip="2 new" chipColor="pass">
          <div style={{ padding: "12px 16px", fontSize: 12 }}>
            <Row k="Confirmed" v={<>Floor-box low-ceiling insight — <strong style={{ color: dark.pass }}>+15% held true</strong> on 4 more units (total: 16)</>} />
            <Row k="New" v={<>Maple Ridge slab density — <strong style={{ color: dark.machine }}>core-drill time 1.3× standard</strong></>} />
            <Row k="Pattern" v={<>Gary · payment <strong style={{ color: dark.fg }}>11 days from invoice</strong> · no disputes</>} last />
          </div>
        </Section>
      </div>
    </div>
  );
};

// ── CLOSED dashboard ────────────────────────────────────────
const ClosedDashboard: React.FC<{ baseFrame: number }> = ({ baseFrame }) => {
  const frame = useCurrentFrame();
  const reviveAnim = slideIn(frame, baseFrame + 10);
  const summaryAnim = slideIn(frame, baseFrame + 35);

  // Revive card pulses
  const pulseScale = 1 + 0.015 * Math.sin((frame - baseFrame) / 20);

  return (
    <div style={{ padding: 22 }}>
      <DashKicker>CLOSED — archive &amp; revive</DashKicker>

      <div
        style={{
          opacity: reviveAnim.opacity, transform: `translateY(${reviveAnim.ty}px) scale(${pulseScale})`,
          backgroundColor: dark.ink2, border: `1px solid ${dark.machine}`,
          borderRadius: 4, padding: 20, marginBottom: 14, textAlign: "center",
        }}
      >
        <div style={{ ...type.kicker, color: dark.fgMuted, marginBottom: 8 }}>⟲ Revivable with full context</div>
        <div style={{ fontSize: 16, color: dark.fg, marginBottom: 4, fontWeight: 500 }}>
          Gary called about Phase III plans
        </div>
        <div style={{ fontSize: 12.5, color: dark.fgMuted, marginBottom: 12 }}>
          Revive restores this project's state to <strong style={{ color: dark.machine }}>PC</strong> — every conversation, quote, contract, variation, photo, and insight preserved.
        </div>
        <div>
          <span
            style={{
              display: "inline-block", padding: "8px 14px", margin: "0 4px",
              backgroundColor: dark.machine, color: dark.ink0,
              border: `1px solid ${dark.machine}`, borderRadius: 4,
              fontFamily: fonts.mono, fontSize: 11, fontWeight: 600,
              letterSpacing: "0.08em", textTransform: "uppercase",
            }}
          >Revive this project</span>
          <span
            style={{
              display: "inline-block", padding: "8px 14px", margin: "0 4px",
              backgroundColor: dark.ink3, color: dark.machine,
              border: `1px solid ${dark.machineWash}`, borderRadius: 4,
              fontFamily: fonts.mono, fontSize: 11, fontWeight: 600,
              letterSpacing: "0.08em", textTransform: "uppercase",
            }}
          >New linked Project</span>
        </div>
      </div>

      <div
        style={{
          opacity: summaryAnim.opacity, transform: `translateY(${summaryAnim.ty}px)`,
          display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 10, marginBottom: 10, padding: "0 2px",
        }}
      >
        <SummaryItem k="Final value" v="$123,040" />
        <SummaryItem k="Realised margin" v="20.4%" pass />
        <SummaryItem k="Duration" v="62 days · on time" />
        <SummaryItem k="DLP outcome" v="1 defect · 0 open" pass />
      </div>
      <div
        style={{
          opacity: summaryAnim.opacity, transform: `translateY(${summaryAnim.ty}px)`,
          display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 10, padding: "0 2px",
        }}
      >
        <SummaryItem k="Variations" v="1 approved · +$1,840" />
        <SummaryItem k="Insights harvested" v="2 new · 1 confirmed" />
        <SummaryItem k="Client rel." v="Paid on time · no disputes" pass />
        <SummaryItem k="Events captured" v="214 · archived" />
      </div>
    </div>
  );
};

const SummaryItem: React.FC<{ k: string; v: string; pass?: boolean }> = ({ k, v, pass }) => (
  <div
    style={{
      backgroundColor: dark.ink3, padding: "10px 12px", borderRadius: 4,
    }}
  >
    <div style={{ ...type.kicker, color: dark.fgMuted, marginBottom: 4 }}>{k}</div>
    <div style={{ fontFamily: fonts.mono, fontSize: 14, fontWeight: 500, color: pass ? dark.pass : dark.fg }}>{v}</div>
  </div>
);

// ── Chat pane content per state ─────────────────────────────
const ChatContent: React.FC<{ phase: Phase; baseFrame: number }> = ({ phase, baseFrame }) => {
  if (phase === "LEAD") {
    return (
      <>
        <div style={{ ...type.kicker, fontSize: 10, color: dark.fgDim, letterSpacing: "0.08em", textAlign: "center", margin: "8px 0 10px" }}>— Tue · Apr 17 · 05:48 —</div>
        <ChatMsg who="Sarah · 05:48" avatar="S" speaker="user" text="Just got off the phone with Maple Ridge. They want us for Phase II." appearFrame={baseFrame + 5} />
        <ChatMsg who="Kerf · 05:48" avatar="K" speaker="kerf" text={<>Creating the project. Peachtree was Phase I — want me to pull its scope when you're ready to quote?</>} appearFrame={baseFrame + 35} />
        <ChatMsg who="Sarah · 05:49" avatar="S" speaker="user" text="Yes. Site walk Thursday. I'll dictate changes then." appearFrame={baseFrame + 80} />
        <ChatMsg who="Kerf · 05:49" avatar="K" speaker="kerf" text={<><strong style={{ color: dark.machine, fontWeight: 500 }}>Thursday site walk</strong> added. I'll have Peachtree's scope ready the morning of.</>} appearFrame={baseFrame + 130} />
      </>
    );
  }
  if (phase === "QUOTED") {
    return (
      <>
        <div style={{ ...type.kicker, fontSize: 10, color: dark.fgDim, letterSpacing: "0.08em", textAlign: "center", margin: "8px 0 10px" }}>— Tue · Apr 22 · 14:05 —</div>
        <ChatMsg who="Kerf · 14:05" avatar="K" speaker="kerf" text={<>Quote drafted. <strong style={{ color: dark.machine, fontWeight: 500 }}>7 items, $121,200, 21% avg margin.</strong> 5 from Peachtree, 2 new. Applied low-ceiling insight to floor boxes.</>} appearFrame={baseFrame + 5} />
        <ChatMsg who="Sarah · 14:08" avatar="S" speaker="user" text="The floor-box margin — where's the 15% from?" appearFrame={baseFrame + 80} />
        <ChatMsg who="Kerf · 14:08" avatar="K" speaker="kerf" text={<><strong style={{ color: dark.machine, fontWeight: 500 }}>Low-ceiling insight.</strong> Floor boxes below 9' ran 15% over on last 3 jobs.</>} appearFrame={baseFrame + 140} />
        <ChatMsg who="Sarah · 14:10" avatar="S" speaker="user" text="Good. Send it." appearFrame={baseFrame + 220} />
        <ChatMsg who="Kerf · 14:10" avatar="K" speaker="kerf" text={<><strong style={{ color: dark.machine, fontWeight: 500 }}>Proposal drafted.</strong> Email to Gary + magic link. Send?</>} appearFrame={baseFrame + 280} />
      </>
    );
  }
  if (phase === "ACCEPTED") {
    return (
      <>
        <div style={{ ...type.kicker, fontSize: 10, color: dark.fgDim, letterSpacing: "0.08em", textAlign: "center", margin: "8px 0 10px" }}>— Mon · Apr 28 · 16:22 —</div>
        <ChatEvent text={<>◈ Event · <strong style={{ color: dark.machine, fontWeight: 500 }}>Gary accepted via magic link</strong></>} appearFrame={baseFrame + 5} />
        <ChatEvent text={<>◈ Event · <strong style={{ color: dark.machine, fontWeight: 500 }}>ContractVersion v1 locked</strong> · $121,200 · 5% · 30d · AZ</>} appearFrame={baseFrame + 35} />
        <div style={{ ...type.kicker, fontSize: 10, color: dark.fgDim, letterSpacing: "0.08em", textAlign: "center", margin: "8px 0 10px" }}>— Tue · Apr 29 · 08:12 —</div>
        <ChatMsg who="Kerf · 08:12" avatar="K" speaker="kerf" text={<>Gary signed yesterday 4:22pm. <strong style={{ color: dark.machine, fontWeight: 500 }}>Contract v1 locked.</strong><br />Drafted: deposit invoice $12,120 · Phoenix permit · material order. Review?</>} appearFrame={baseFrame + 90} />
        <ChatMsg who="Sarah · 08:15" avatar="S" speaker="user" text="Send the deposit. Hold permit." appearFrame={baseFrame + 170} />
      </>
    );
  }
  if (phase === "ACTIVE") {
    return (
      <>
        <div style={{ ...type.kicker, fontSize: 10, color: dark.fgDim, letterSpacing: "0.08em", textAlign: "center", margin: "8px 0 10px" }}>— Fri · May 9 · 14:22 —</div>
        <ChatMsg who="Sarah · 14:22" avatar="S" speaker="user" text="How's Maple Ridge tracking?" appearFrame={baseFrame + 20} />
        <ChatMsg who="Kerf · 14:22" avatar="K" speaker="kerf" text={<>45% through, <strong style={{ color: dark.machine, fontWeight: 500 }}>2 days behind</strong>. Labour $4,200 over — floor-box slab is denser than the insight predicted. Worth a variation?</>} appearFrame={baseFrame + 60} />
        <ChatMsg who="Sarah · 14:23" avatar="S" speaker="user" text="Draft it." appearFrame={baseFrame + 160} />
        <ChatMsg who="Kerf · 14:23" avatar="K" speaker="kerf" text={<><strong style={{ color: dark.machine, fontWeight: 500 }}>V1 drafted.</strong> 4 cores · +$1,840 · +0.5 day. Evidence from logs + chat. Review?</>} appearFrame={baseFrame + 200} />
      </>
    );
  }
  if (phase === "PC") {
    return (
      <>
        <div style={{ ...type.kicker, fontSize: 10, color: dark.fgDim, letterSpacing: "0.08em", textAlign: "center", margin: "8px 0 10px" }}>— Wed · Jun 11 · 16:10 —</div>
        <ChatEvent text={<>◈ <strong style={{ color: dark.machine, fontWeight: 500 }}>PC declared by Sarah</strong> · scope-at-PC snapshotted</>} appearFrame={baseFrame + 5} />
        <ChatEvent text={<>◈ <strong style={{ color: dark.machine, fontWeight: 500 }}>Final invoice issued</strong> · $12,120 · Gary paid Jun 14</>} appearFrame={baseFrame + 35} />
        <ChatEvent text={<>◈ <strong style={{ color: dark.machine, fontWeight: 500 }}>DLP opened</strong> · 12mo clock · ends Jun 11 2027</>} appearFrame={baseFrame + 65} />
        <div style={{ ...type.kicker, fontSize: 10, color: dark.fgDim, letterSpacing: "0.08em", textAlign: "center", margin: "16px 0 10px" }}>— Fri · Jul 18 · 10:20 —</div>
        <ChatMsg who="Mike · 10:20" avatar="M" speaker="user" text="Swapped the driver on reception can. Working. 0.3hrs." appearFrame={baseFrame + 110} />
        <ChatMsg who="Kerf · 10:20" avatar="K" speaker="kerf" text={<>Logged. <strong style={{ color: dark.machine, fontWeight: 500 }}>Defect resolved.</strong> Photo attached.</>} appearFrame={baseFrame + 165} />
      </>
    );
  }
  if (phase === "CLOSED") {
    return (
      <>
        <div style={{ ...type.kicker, fontSize: 10, color: dark.fgDim, letterSpacing: "0.08em", textAlign: "center", margin: "8px 0 10px" }}>— Fri · Jun 25 2027 · 11:04 —</div>
        <ChatEvent text={<>◈ <strong style={{ color: dark.machine, fontWeight: 500 }}>DLP expired</strong> · retention released $6,152</>} appearFrame={baseFrame + 5} />
        <ChatEvent text={<>◈ <strong style={{ color: dark.machine, fontWeight: 500 }}>Project closed by Sarah</strong> · reason: completed</>} appearFrame={baseFrame + 35} />
        <ChatMsg who="Kerf · 11:04" avatar="K" speaker="kerf" text={<>Archived. Full history preserved — 214 events, 3 variations, 47 photos, 28 daily logs.</>} appearFrame={baseFrame + 80} />
        <ChatMsg who="Kerf · 11:04" avatar="K" speaker="kerf" text={<>Gary called last week about Phase III. Want me to <strong style={{ color: dark.machine, fontWeight: 500 }}>revive</strong> this project, or start a new linked one?</>} appearFrame={baseFrame + 140} />
      </>
    );
  }
  return null;
};

// ── Main composition ────────────────────────────────────────
export const LifecycleFlow: React.FC = () => {
  const frame = useCurrentFrame();
  const phase = phaseForFrame(frame);

  // Intro cross-fades out at LEAD_START
  const introOpacity = fadeWindow(frame, 0, T.INTRO_END - 15, 10, 15);

  // Phase opacities (cross-fade between phases in transition windows)
  const phaseOpacities: Record<Phase, number> = {
    INTRO: 0,
    LEAD: fadeWindow(frame, T.LEAD_START, T.LEAD_END, 20, 30),
    QUOTED: fadeWindow(frame, T.QUOTED_START, T.QUOTED_END, 30, 30),
    ACCEPTED: fadeWindow(frame, T.ACCEPTED_START, T.ACCEPTED_END, 30, 30),
    ACTIVE: fadeWindow(frame, T.ACTIVE_START, T.ACTIVE_END, 30, 30),
    PC: fadeWindow(frame, T.PC_START, T.PC_END, 30, 30),
    CLOSED: fadeWindow(frame, T.CLOSED_START, T.CLOSED_END, 30, 20),
  };

  // Phase base frames for local animation timing
  const phaseBases: Record<Phase, number> = {
    INTRO: 0,
    LEAD: T.LEAD_START,
    QUOTED: T.QUOTED_START,
    ACCEPTED: T.ACCEPTED_START,
    ACTIVE: T.ACTIVE_START,
    PC: T.PC_START,
    CLOSED: T.CLOSED_START,
  };

  // Current state for header (the one with highest opacity)
  const currentPhase: Phase = phase;
  const displayState: ProjectState = currentPhase === "INTRO" ? "LEAD" : (currentPhase as ProjectState);
  const stateSuffix =
    displayState === "LEAD" ? "Day 2" :
    displayState === "QUOTED" ? undefined :
    displayState === "ACCEPTED" ? "Day 1" :
    displayState === "ACTIVE" ? "Day 14" :
    displayState === "PC" ? "Day 62" :
    displayState === "CLOSED" ? undefined : undefined;

  const totalLabel =
    displayState === "LEAD" ? "Stage" :
    displayState === "QUOTED" ? "Quote Total" :
    displayState === "ACCEPTED" ? "Contract Sum" :
    displayState === "ACTIVE" ? "Effective Sum" :
    displayState === "PC" ? "Final Value" :
    "Final Value";
  const totalValue =
    displayState === "LEAD" ? "—" :
    displayState === "PC" || displayState === "CLOSED" ? "$123,040" :
    "$121,200";

  const ctaLabel =
    displayState === "LEAD" ? "Start scope" :
    displayState === "QUOTED" ? "Generate Proposal" :
    displayState === "ACCEPTED" ? "Log first hours" :
    displayState === "ACTIVE" ? "Log Time" :
    displayState === "PC" ? "Close project" :
    "Revive →";
  const ctaAlt = displayState === "LEAD" || displayState === "PC" || displayState === "CLOSED";

  // Context label for chat
  const ctxLabel =
    currentPhase === "LEAD" ? "Lead · Maple Ridge" :
    currentPhase === "QUOTED" ? "Contract · Maple Ridge" :
    currentPhase === "ACCEPTED" ? "Accepted · Maple Ridge" :
    currentPhase === "ACTIVE" ? "Active · Maple Ridge" :
    currentPhase === "PC" ? "PC · Maple Ridge" :
    "Closed · archive";

  // State transition animation key (when chip pulses)
  const stateAnimKey =
    frame >= T.QUOTED_START && frame < T.QUOTED_START + 10 ? T.QUOTED_START :
    frame >= T.ACCEPTED_START && frame < T.ACCEPTED_START + 10 ? T.ACCEPTED_START :
    frame >= T.ACTIVE_START && frame < T.ACTIVE_START + 10 ? T.ACTIVE_START :
    frame >= T.PC_START && frame < T.PC_START + 10 ? T.PC_START :
    frame >= T.CLOSED_START && frame < T.CLOSED_START + 10 ? T.CLOSED_START :
    undefined;

  return (
    <AbsoluteFill style={{ backgroundColor: dark.ink0, fontFamily: fonts.sans }}>
      {/* Intro */}
      <div style={{ position: "absolute", inset: 0, opacity: introOpacity, pointerEvents: "none" }}>
        <IntroCard />
      </div>

      {/* Main app frame — always mounted after intro ends */}
      {frame >= T.INTRO_END - 20 && (
        <div
          style={{
            position: "absolute", inset: 0,
            display: "flex",
            opacity: interpolate(frame, [T.INTRO_END - 20, T.INTRO_END], [0, 1], { extrapolateRight: "clamp" }),
          }}
        >
          <IconRail />
          <ChatPane ctxLabel={ctxLabel} timestamp={undefined}>
            <ChatContent phase={currentPhase} baseFrame={phaseBases[currentPhase]} />
          </ChatPane>
          <div
            style={{
              flex: 1, backgroundColor: dark.ink0,
              display: "flex", flexDirection: "column", overflow: "hidden",
            }}
          >
            <TopHeader
              title="Maple Ridge — Phase II"
              pid="MRP-2024-118"
              client="Maple Ridge Dev. Corp."
              state={displayState}
              stateSuffix={stateSuffix}
              stateAnimKey={stateAnimKey}
              totalLabel={totalLabel}
              totalValue={totalValue}
              ctaLabel={ctaLabel}
              ctaAlt={ctaAlt}
            />
            <TabBar tabs={tabsFor(currentPhase)} />
            <div style={{ flex: 1, overflow: "hidden", position: "relative" }}>
              {(["LEAD", "QUOTED", "ACCEPTED", "ACTIVE", "PC", "CLOSED"] as Phase[]).map((p) => {
                const op = phaseOpacities[p];
                if (op === 0) return null;
                return (
                  <div key={p} style={{ position: "absolute", inset: 0, opacity: op, overflow: "auto" }}>
                    {p === "LEAD" && <LeadDashboard baseFrame={phaseBases.LEAD} />}
                    {p === "QUOTED" && <QuotedDashboard baseFrame={phaseBases.QUOTED} />}
                    {p === "ACCEPTED" && <AcceptedDashboard baseFrame={phaseBases.ACCEPTED} />}
                    {p === "ACTIVE" && <ActiveDashboard baseFrame={phaseBases.ACTIVE} />}
                    {p === "PC" && <PcDashboard baseFrame={phaseBases.PC} />}
                    {p === "CLOSED" && <ClosedDashboard baseFrame={phaseBases.CLOSED} />}
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}
    </AbsoluteFill>
  );
};
