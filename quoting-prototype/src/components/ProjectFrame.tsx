import React from "react";
import { interpolate, spring, useCurrentFrame } from "remotion";
import { dark, fonts, type } from "./dark-styles";

// ── Icon rail (left, 48px) ──────────────────────────────────
export const IconRail: React.FC = () => {
  const items = [
    { path: "M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z", active: false },
    { path: "M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z", active: true },
    { path: "M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2M9 11a4 4 0 100-8 4 4 0 000 8", active: false },
    { path: "M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z", active: false },
    { path: "M9 11l3 3L22 4", active: false },
  ];
  return (
    <nav
      style={{
        width: 48, height: "100%",
        backgroundColor: dark.ink1,
        borderRight: `1px solid ${dark.hairline}`,
        display: "flex", flexDirection: "column", alignItems: "center",
        padding: "12px 0", gap: 6, flexShrink: 0,
      }}
    >
      <div
        style={{
          width: 28, height: 28, backgroundColor: dark.machine, borderRadius: 4,
          display: "flex", alignItems: "center", justifyContent: "center",
          fontFamily: fonts.mono, fontWeight: 700, fontSize: 14,
          color: dark.ink0, marginBottom: 10,
        }}
      >K</div>
      {items.map((it, i) => (
        <div
          key={i}
          style={{
            width: 32, height: 32, borderRadius: 4,
            display: "flex", alignItems: "center", justifyContent: "center",
            color: it.active ? dark.machine : dark.fgDim,
            backgroundColor: it.active ? dark.ink3 : "transparent",
          }}
        >
          <svg width={16} height={16} fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24">
            <path d={it.path} />
          </svg>
        </div>
      ))}
    </nav>
  );
};

// ── State chip ──────────────────────────────────────────────
export type ProjectState = "LEAD" | "QUOTED" | "ACCEPTED" | "ACTIVE" | "PC" | "CLOSED";

const STATE_STYLES: Record<ProjectState, { bg: string; fg: string; border: string; label: string }> = {
  LEAD: { bg: dark.ink3, fg: dark.fgMuted, border: dark.hairline, label: "Lead" },
  QUOTED: { bg: dark.machine, fg: dark.ink0, border: dark.machine, label: "Quoted · Draft A" },
  ACCEPTED: { bg: dark.machineWash, fg: dark.machine, border: dark.machine, label: "Accepted" },
  ACTIVE: { bg: dark.passBg, fg: dark.pass, border: dark.pass, label: "Active" },
  PC: { bg: dark.warnBg, fg: dark.warn, border: dark.warn, label: "Practical Completion" },
  CLOSED: { bg: dark.ink4, fg: dark.fgMuted, border: dark.hairline, label: "Closed · completed" },
};

export const StateChip: React.FC<{ state: ProjectState; suffix?: string; animKey?: number }> = ({
  state, suffix, animKey,
}) => {
  const s = STATE_STYLES[state];
  const frame = useCurrentFrame();
  const rel = animKey !== undefined ? frame - animKey : frame;
  const pulse = animKey !== undefined && rel >= 0 && rel < 30
    ? 1 + 0.08 * Math.sin((rel / 30) * Math.PI * 2) : 1;
  return (
    <span
      style={{
        ...type.kicker, fontSize: 10, fontWeight: 600,
        padding: "3px 8px", borderRadius: 3,
        border: `1px solid ${s.border}`,
        backgroundColor: s.bg, color: s.fg,
        display: "inline-block",
        transform: `scale(${pulse})`,
        transition: "background-color 400ms ease, color 400ms ease, border-color 400ms ease",
      }}
    >
      {s.label}{suffix ? ` · ${suffix}` : ""}
    </span>
  );
};

// ── Top header ──────────────────────────────────────────────
export const TopHeader: React.FC<{
  title: string; pid: string; client: string;
  state: ProjectState; stateSuffix?: string; stateAnimKey?: number;
  totalLabel: string; totalValue: string;
  ctaLabel: string; ctaAlt?: boolean;
  extras?: React.ReactNode;
}> = ({ title, pid, client, state, stateSuffix, stateAnimKey, totalLabel, totalValue, ctaLabel, ctaAlt, extras }) => (
  <div
    style={{
      padding: "14px 22px",
      backgroundColor: dark.ink2,
      borderBottom: `1px solid ${dark.hairline}`,
      display: "flex", alignItems: "center", gap: 14, flexWrap: "wrap",
    }}
  >
    <div
      style={{
        width: 22, height: 22, backgroundColor: dark.machine, borderRadius: 3,
        display: "flex", alignItems: "center", justifyContent: "center",
        color: dark.ink0, fontFamily: fonts.mono, fontWeight: 700, fontSize: 11,
      }}
    >K</div>
    <div style={{ ...type.title }}>{title}</div>
    <span style={{ color: dark.fgDim, fontFamily: fonts.mono, fontSize: 11 }}>·</span>
    <span
      style={{
        ...type.kicker, fontSize: 11, color: dark.machine,
        backgroundColor: dark.machineWash, padding: "2px 6px",
        borderRadius: 3, fontWeight: 600,
      }}
    >{pid}</span>
    <span style={{ color: dark.fgDim, fontFamily: fonts.mono, fontSize: 11 }}>·</span>
    <span style={{ ...type.label, color: dark.fgMuted }}>{client}</span>
    <StateChip state={state} suffix={stateSuffix} animKey={stateAnimKey} />
    {extras}
    <div style={{ marginLeft: "auto", display: "flex", alignItems: "center", gap: 12 }}>
      <div>
        <div style={{ ...type.kicker, color: dark.fgMuted, textAlign: "right", marginBottom: 0 }}>
          {totalLabel}
        </div>
        <div
          style={{
            fontFamily: fonts.mono, fontSize: 16, color: dark.machine,
            fontWeight: 600, textAlign: "right", lineHeight: 1.1,
          }}
        >{totalValue}</div>
      </div>
      <button
        style={{
          padding: "10px 16px",
          backgroundColor: ctaAlt ? dark.ink3 : dark.machine,
          color: ctaAlt ? dark.fg : dark.ink0,
          border: `1px solid ${ctaAlt ? dark.hairline : dark.machine}`,
          borderRadius: 4,
          fontFamily: fonts.mono, fontSize: 11, fontWeight: 600,
          letterSpacing: "0.06em", textTransform: "uppercase",
        }}
      >{ctaLabel}</button>
    </div>
  </div>
);

// ── Tab bar ──────────────────────────────────────────────────
export const TabBar: React.FC<{ tabs: { label: string; active?: boolean; count?: string; disabled?: boolean }[] }> = ({ tabs }) => (
  <div
    style={{
      display: "flex", padding: "0 22px",
      backgroundColor: dark.ink1, borderBottom: `1px solid ${dark.hairline}`, gap: 2,
      flexShrink: 0,
    }}
  >
    {tabs.map((t, i) => (
      <div
        key={i}
        style={{
          padding: "12px 14px 11px",
          ...type.label,
          color: t.active ? dark.machine : t.disabled ? dark.fgDim : dark.fgMuted,
          opacity: t.disabled ? 0.4 : 1,
          borderBottom: `2px solid ${t.active ? dark.machine : "transparent"}`,
          backgroundColor: t.active ? dark.ink0 : "transparent",
          display: "flex", alignItems: "center", gap: 6,
        }}
      >
        {t.label}
        {t.count && (
          <span
            style={{
              backgroundColor: t.active ? dark.machineWash : dark.ink3,
              color: t.active ? dark.machine : dark.fgMuted,
              padding: "1px 5px", borderRadius: 3, fontSize: 10,
            }}
          >{t.count}</span>
        )}
      </div>
    ))}
  </div>
);

// ── Metric tile ──────────────────────────────────────────────
export const MetricTile: React.FC<{
  kicker: string; value: React.ReactNode; sub?: React.ReactNode;
  primary?: boolean; valueColor?: string; subColor?: string;
}> = ({ kicker, value, sub, primary, valueColor, subColor }) => (
  <div
    style={{
      backgroundColor: primary ? dark.machine : dark.ink2,
      border: `1px solid ${primary ? dark.machine : dark.hairline}`,
      borderRadius: 4, padding: "14px 16px",
      color: primary ? dark.ink0 : dark.fg,
    }}
  >
    <div
      style={{
        ...type.kicker,
        color: primary ? dark.ink0 : dark.fgMuted,
        opacity: primary ? 0.75 : 1,
        marginBottom: 6,
      }}
    >{kicker}</div>
    <div
      style={{
        fontFamily: fonts.mono, fontSize: 22,
        fontWeight: 600, lineHeight: 1.05,
        color: valueColor || (primary ? dark.ink0 : dark.fg),
      }}
    >{value}</div>
    {sub && (
      <div
        style={{
          fontFamily: fonts.mono, fontSize: 11,
          color: subColor || (primary ? dark.ink0 : dark.fgMuted),
          opacity: primary && !subColor ? 0.7 : 1,
          marginTop: 4, letterSpacing: "0.04em",
        }}
      >{sub}</div>
    )}
  </div>
);

// ── Section container ───────────────────────────────────────
export const Section: React.FC<{
  num?: string; title: string; chip?: string; chipColor?: "machine" | "pass" | "warn";
  action?: string; actionPrimary?: boolean;
  children: React.ReactNode;
  accent?: boolean; warn?: boolean;
}> = ({ num, title, chip, chipColor = "machine", action, actionPrimary, children, accent, warn }) => (
  <div
    style={{
      backgroundColor: dark.ink2,
      border: `1px solid ${accent ? dark.machine : warn ? dark.warn : dark.hairline}`,
      borderRadius: 4, marginBottom: 14, overflow: "hidden",
    }}
  >
    <div
      style={{
        padding: "12px 16px",
        display: "flex", alignItems: "center", gap: 12,
        borderBottom: `1px solid ${dark.hairline}`,
      }}
    >
      {num && <span style={{ fontFamily: fonts.mono, fontSize: 10, color: dark.fgDim, letterSpacing: "0.08em", fontWeight: 600 }}>{num}</span>}
      <span
        style={{
          ...type.label, fontSize: 11, fontWeight: 600,
          color: accent ? dark.machine : warn ? dark.warn : dark.fg,
        }}
      >{title}</span>
      {chip && (
        <span
          style={{
            ...type.kicker, fontSize: 9, fontWeight: 600,
            padding: "2px 6px", borderRadius: 3,
            backgroundColor:
              chipColor === "pass" ? dark.passBg : chipColor === "warn" ? dark.warnBg : dark.machineWash,
            color:
              chipColor === "pass" ? dark.pass : chipColor === "warn" ? dark.warn : dark.machine,
            border: `1px solid ${
              chipColor === "pass" ? dark.pass : chipColor === "warn" ? dark.warn : dark.machineWash
            }`,
          }}
        >{chip}</span>
      )}
      <div style={{ flex: 1 }} />
      {action && (
        <button
          style={{
            padding: "5px 10px",
            backgroundColor: actionPrimary ? dark.machineWash : dark.ink3,
            color: actionPrimary ? dark.machine : dark.fg,
            border: `1px solid ${actionPrimary ? dark.machineWash : dark.hairline}`,
            borderRadius: 3,
            fontFamily: fonts.mono, fontSize: 10, fontWeight: 600,
            letterSpacing: "0.06em", textTransform: "uppercase",
          }}
        >{action}</button>
      )}
    </div>
    {children}
  </div>
);

// ── Chat message bubble (reusable) ──────────────────────────
export const ChatMsg: React.FC<{
  who: string; avatar: string; speaker: "user" | "kerf";
  text: React.ReactNode; appearFrame?: number;
}> = ({ who, avatar, speaker, text, appearFrame }) => {
  const frame = useCurrentFrame();
  let opacity = 1, ty = 0;
  if (appearFrame !== undefined) {
    const rel = frame - appearFrame;
    if (rel < 0) return null;
    opacity = interpolate(rel, [0, 10], [0, 1], { extrapolateRight: "clamp" });
    const s = spring({ frame: rel, fps: 30, config: { damping: 18, stiffness: 140 } });
    ty = (1 - s) * 14;
  }
  const isUser = speaker === "user";
  return (
    <div style={{ opacity, transform: `translateY(${ty}px)`, marginBottom: 14 }}>
      <div
        style={{
          ...type.kicker, fontSize: 10, color: dark.fgDim,
          letterSpacing: "0.08em", marginBottom: 4,
          display: "flex", alignItems: "center", gap: 6,
          textTransform: "none" as any,
        }}
      >
        <span
          style={{
            width: 16, height: 16,
            backgroundColor: isUser ? dark.ink4 : dark.machine,
            color: isUser ? dark.fg : dark.ink0,
            borderRadius: 3, fontSize: 10, fontWeight: 700,
            display: "flex", alignItems: "center", justifyContent: "center",
          }}
        >{avatar}</span>
        {who}
      </div>
      <div
        style={{
          padding: "10px 12px", borderRadius: 6, lineHeight: 1.45,
          backgroundColor: isUser ? dark.machine : dark.ink2,
          color: isUser ? dark.ink0 : dark.fg,
          border: isUser ? "none" : `1px solid ${dark.hairline}`,
          fontWeight: isUser ? 500 : 400,
          fontSize: 12.5,
        }}
      >{text}</div>
    </div>
  );
};

// ── Event marker in chat ────────────────────────────────────
export const ChatEvent: React.FC<{ text: React.ReactNode; appearFrame?: number }> = ({ text, appearFrame }) => {
  const frame = useCurrentFrame();
  let opacity = 1;
  if (appearFrame !== undefined) {
    const rel = frame - appearFrame;
    if (rel < 0) return null;
    opacity = interpolate(rel, [0, 10], [0, 1], { extrapolateRight: "clamp" });
  }
  return (
    <div
      style={{
        opacity,
        backgroundColor: dark.ink2, border: `1px dashed ${dark.hairline}`,
        borderRadius: 4, padding: "8px 10px", marginBottom: 14,
        fontFamily: fonts.mono, fontSize: 10.5, color: dark.fgMuted,
        letterSpacing: "0.04em",
      }}
    >{text}</div>
  );
};

// ── Chat pane wrapper ───────────────────────────────────────
export const ChatPane: React.FC<{
  ctxLabel: string;
  timestamp?: string;
  children: React.ReactNode;
}> = ({ ctxLabel, timestamp, children }) => (
  <div
    style={{
      width: 320, backgroundColor: dark.ink1,
      borderRight: `1px solid ${dark.hairline}`,
      display: "flex", flexDirection: "column", flexShrink: 0,
    }}
  >
    <div
      style={{
        padding: "12px 14px", borderBottom: `1px solid ${dark.hairline}`,
        display: "flex", alignItems: "center", justifyContent: "space-between",
      }}
    >
      <div style={{ ...type.kicker, color: dark.fgMuted }}>◎ Conversation</div>
      <div style={{ ...type.kicker, fontSize: 10, color: dark.fgDim, letterSpacing: "0.08em" }}>{ctxLabel}</div>
    </div>
    <div style={{ flex: 1, padding: 14, overflowY: "hidden", fontSize: 12.5 }}>
      {timestamp && (
        <div
          style={{
            ...type.kicker, fontSize: 10, color: dark.fgDim,
            letterSpacing: "0.08em", textAlign: "center", margin: "8px 0 10px",
          }}
        >— {timestamp} —</div>
      )}
      {children}
    </div>
    <div
      style={{
        borderTop: `1px solid ${dark.hairline}`, padding: "10px 14px",
        display: "flex", alignItems: "center", gap: 8, backgroundColor: dark.ink1,
      }}
    >
      <input
        placeholder="Reply — or hold to speak"
        style={{
          flex: 1, backgroundColor: dark.ink2,
          border: `1px solid ${dark.hairline}`, borderRadius: 4,
          padding: "8px 10px", color: dark.fg,
          fontFamily: "inherit", fontSize: 12.5,
        }}
      />
      <button
        style={{
          padding: "8px 10px", borderRadius: 4,
          ...type.label, fontSize: 10, fontWeight: 600,
          border: `1px solid ${dark.hairline}`,
          backgroundColor: dark.ink3, color: dark.fg,
        }}
      >◉ HOLD</button>
      <button
        style={{
          padding: "8px 10px", borderRadius: 4,
          ...type.label, fontSize: 10, fontWeight: 600,
          backgroundColor: dark.machine, color: dark.ink0,
          border: `1px solid ${dark.machine}`,
        }}
      >SEND</button>
    </div>
  </div>
);

// ── Dashboard kicker ────────────────────────────────────────
export const DashKicker: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <div
    style={{
      ...type.kicker, fontSize: 10, fontWeight: 600,
      color: dark.machine, marginBottom: 10,
    }}
  >◉ Dashboard · {children}</div>
);

// ── Progress bar ────────────────────────────────────────────
export const ProgressBar: React.FC<{ pct: number; color?: string; width?: number }> = ({ pct, color, width = 110 }) => (
  <div style={{ display: "flex", alignItems: "center", gap: 8, minWidth: width }}>
    <div
      style={{
        flex: 1, height: 4, backgroundColor: dark.ink3,
        borderRadius: 2, overflow: "hidden",
      }}
    >
      <div style={{ height: "100%", width: `${pct}%`, backgroundColor: color || dark.machine, borderRadius: 2 }} />
    </div>
    <span style={{ fontFamily: fonts.mono, fontSize: 10, color: dark.fgMuted, minWidth: 30, textAlign: "right" }}>{pct}%</span>
  </div>
);
