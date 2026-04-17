import { CSSProperties } from "react";

// ── Kerf Design System tokens ───────────────────────────────
export const colors = {
  // Light mode palette
  bg: "#f4f5f3",
  foreground: "#0d0e0c",
  card: "#ffffff",
  cardForeground: "#0d0e0c",

  // Brand
  machine: "#F5B800",      // Kerf gold
  machineDark: "#D9A200",
  machineBright: "#FFCA18",
  machineWash: "rgba(245,184,0,0.1)",

  // Neutrals
  muted: "#e6e8e3",
  mutedForeground: "#71766b",
  secondary: "#f4f5f3",
  secondaryForeground: "#3e423a",
  border: "#e6e8e3",
  input: "#e6e8e3",

  // Status
  pass: "#2d8a4e",
  passBg: "rgba(45,138,78,0.1)",
  fail: "#c53030",
  failBg: "rgba(197,48,48,0.1)",
  warn: "#b8860b",
  warnBg: "rgba(184,134,11,0.08)",

  // Sidebar
  sidebar: "#ffffff",
  sidebarForeground: "#545951",
  sidebarBorder: "#e6e8e3",
  sidebarAccent: "rgba(245,184,0,0.1)",

  // Chat
  userBubbleBg: "#0d0e0c",
  userBubbleText: "#ffffff",
  kerfBubbleBg: "#ffffff",
  kerfBubbleText: "#0d0e0c",
  kerfBubbleBorder: "#e6e8e3",
};

export const fonts = {
  sans: "'IBM Plex Sans', -apple-system, BlinkMacSystemFont, sans-serif",
  mono: "'IBM Plex Mono', monospace",
};

export const radius = {
  sm: 1.8,
  md: 2.4,
  lg: 3,
  xl: 4.2,
  button: 3,
  card: 3,
  badge: 20, // pill
  input: 8,
  dialog: 12,
};

export const baseContainer: CSSProperties = {
  width: "100%",
  height: "100%",
  backgroundColor: colors.bg,
  fontFamily: fonts.sans,
  color: colors.foreground,
  display: "flex",
  overflow: "hidden",
};
