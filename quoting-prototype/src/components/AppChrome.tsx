import React from "react";
import { useCurrentFrame } from "remotion";
import { colors, fonts, radius } from "./styles";

// ── Kerf Logo Mark ──────────────────────────────────────────
export const LogoMark: React.FC<{ size?: number }> = ({ size = 32 }) => (
  <div
    style={{
      width: size,
      height: size,
      backgroundColor: colors.machine,
      borderRadius: 6,
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
    }}
  >
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="white"
      strokeWidth="3"
      strokeLinecap="round"
      strokeLinejoin="round"
      style={{ width: size * 0.5, height: size * 0.5 }}
    >
      <polyline points="20 6 9 17 4 12" />
    </svg>
  </div>
);

// ── Icon Rail (exact match: w-12, white bg, border-r) ───────
interface RailItemDef {
  label: string;
  icon: string;
  active?: boolean;
}

const RAIL_ITEMS: RailItemDef[] = [
  { label: "Chat", icon: "M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z" },
  { label: "Projects", icon: "M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" },
  { label: "Workers", icon: "M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2M9 11a4 4 0 100-8 4 4 0 000 8M23 21v-2a4 4 0 00-3-3.87M16 3.13a4 4 0 010 7.75" },
  { label: "Quotes", icon: "M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z M14 2v6h6 M16 13H8 M16 17H8 M10 9H8" },
  { label: "Inspections", icon: "M9 11l3 3L22 4M21 12v7a2 2 0 01-2 2H5a2 2 0 01-2-2V5a2 2 0 012-2h11" },
  { label: "Equipment", icon: "M14.7 6.3a1 1 0 000 1.4l1.6 1.6a1 1 0 001.4 0l3.77-3.77a6 6 0 01-7.94 7.94l-6.91 6.91a2.12 2.12 0 01-3-3l6.91-6.91a6 6 0 017.94-7.94l-3.76 3.76z" },
  { label: "Settings", icon: "M12 15a3 3 0 100-6 3 3 0 000 6z" },
];

export const IconRail: React.FC = () => (
  <nav
    style={{
      width: 48,
      height: "100%",
      backgroundColor: "#ffffff",
      borderRight: `1px solid ${colors.border}`,
      display: "flex",
      flexDirection: "column",
      alignItems: "center",
      paddingTop: 12,
      paddingBottom: 12,
      flexShrink: 0,
    }}
  >
    {/* Logo */}
    <div style={{ marginBottom: 16 }}>
      <LogoMark size={32} />
    </div>

    {/* Items */}
    <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 4, flex: 1 }}>
      {RAIL_ITEMS.map((item) => {
        const active = item.label === "Quotes";
        return (
          <div
            key={item.label}
            style={{
              position: "relative",
              width: 40,
              height: 40,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              borderRadius: 2,
              backgroundColor: active ? colors.machineWash : "transparent",
              cursor: "pointer",
            }}
          >
            {active && (
              <div
                style={{
                  position: "absolute",
                  left: 0,
                  top: "50%",
                  transform: "translateY(-50%)",
                  width: 2,
                  height: 20,
                  borderRadius: "0 2px 2px 0",
                  backgroundColor: colors.machine,
                }}
              />
            )}
            <svg
              viewBox="0 0 24 24"
              fill="none"
              stroke={active ? colors.machineDark : colors.mutedForeground}
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
              style={{ width: 18, height: 18 }}
            >
              <path d={item.icon} />
            </svg>
          </div>
        );
      })}
    </div>
  </nav>
);

// ── Chat pane header (sparkle icon + "Kerf") ────────────────
export const ChatHeader: React.FC = () => (
  <div
    style={{
      display: "flex",
      alignItems: "center",
      justifyContent: "space-between",
      borderBottom: `1px solid ${colors.border}`,
      backgroundColor: colors.card,
      padding: "12px 16px",
    }}
  >
    <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
      <div
        style={{
          width: 24,
          height: 24,
          borderRadius: 2,
          backgroundColor: colors.machine,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        <svg
          viewBox="0 0 24 24"
          fill="none"
          stroke="white"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
          style={{ width: 14, height: 14 }}
        >
          <path d="M12 3l1.5 4.5L18 9l-4.5 1.5L12 15l-1.5-4.5L6 9l4.5-1.5L12 3z" />
        </svg>
      </div>
      <span style={{ fontSize: 14, fontWeight: 600 }}>Kerf</span>
    </div>
    <span
      style={{
        fontSize: 11,
        color: colors.mutedForeground,
        cursor: "pointer",
      }}
    >
      New chat
    </span>
  </div>
);

// ── Chat input bar (border-t, bg-card) ──────────────────────
export const ChatInputBar: React.FC = () => (
  <div
    style={{
      borderTop: `1px solid ${colors.border}`,
      backgroundColor: colors.card,
      padding: "12px 16px",
      display: "flex",
      alignItems: "center",
      gap: 8,
    }}
  >
    <div
      style={{
        flex: 1,
        height: 32,
        borderRadius: radius.input,
        border: `1px solid ${colors.input}`,
        backgroundColor: "transparent",
        padding: "0 10px",
        fontSize: 13,
        color: colors.mutedForeground,
        display: "flex",
        alignItems: "center",
      }}
    >
      Ask a question...
    </div>
    <div
      style={{
        width: 36,
        height: 36,
        borderRadius: radius.button,
        backgroundColor: colors.machine,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        cursor: "pointer",
      }}
    >
      <svg
        viewBox="0 0 24 24"
        fill="none"
        stroke={colors.foreground}
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
        style={{ width: 16, height: 16 }}
      >
        <line x1="22" y1="2" x2="11" y2="13" />
        <polygon points="22 2 15 22 11 13 2 9 22 2" />
      </svg>
    </div>
  </div>
);
