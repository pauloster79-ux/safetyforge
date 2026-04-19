import { CSSProperties } from "react";

// ── Site Board · Dark mode tokens (from frontend/src/index.css) ──
export const dark = {
  // Surface depth
  ink0: "#0d0e0c",      // page ground
  ink1: "#141511",      // subtle lift
  ink2: "#191b17",      // card surface
  ink3: "#22241f",      // input / hover
  ink4: "#2e312b",      // header chrome

  // Foreground
  fg: "#e8e9e6",
  fgMuted: "#a3a79c",
  fgDim: "#71766b",

  // Lines
  hairline: "rgba(255, 255, 255, 0.06)",
  plateHi: "rgba(255, 255, 255, 0.04)",
  plateLo: "rgba(0, 0, 0, 0.35)",

  // Brand — machine yellow
  machine: "#F5B800",
  machineBright: "#FFCA18",
  machineDark: "#D9A200",
  machineWash: "rgba(245, 184, 0, 0.10)",
  machineStrong: "rgba(245, 184, 0, 0.20)",

  // Status
  pass: "#38a169",
  passBg: "rgba(56, 161, 105, 0.15)",
  fail: "#e53e3e",
  failBg: "rgba(229, 62, 62, 0.15)",
  warn: "#d69e2e",
  warnBg: "rgba(214, 158, 46, 0.10)",
};

export const fonts = {
  sans: "'IBM Plex Sans', -apple-system, BlinkMacSystemFont, sans-serif",
  mono: "'IBM Plex Mono', monospace",
};

// Type scale
export const type = {
  kicker: {
    fontFamily: fonts.mono,
    fontSize: 10,
    letterSpacing: "0.12em",
    textTransform: "uppercase" as const,
    fontWeight: 600,
  },
  label: {
    fontFamily: fonts.mono,
    fontSize: 11,
    letterSpacing: "0.06em",
    textTransform: "uppercase" as const,
    fontWeight: 500,
  },
  body: { fontSize: 12.5, lineHeight: 1.45 },
  title: { fontSize: 15, fontWeight: 600 },
  display: { fontSize: 22, fontWeight: 600, fontFamily: fonts.mono },
};

// Base container for the prototype
export const baseFill: CSSProperties = {
  width: "100%",
  height: "100%",
  backgroundColor: dark.ink0,
  color: dark.fg,
  fontFamily: fonts.sans,
  fontSize: 13,
  lineHeight: 1.4,
  overflow: "hidden",
};
