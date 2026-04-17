import React from "react";
import { interpolate, useCurrentFrame, spring } from "remotion";
import { colors, fonts, radius } from "./styles";

// ── Work Item Detail View (pricing worksheet) ───────────────
// Shows how a single work item's cost was calculated:
// quantity × productivity = labour hours × rate = labour cost
// + each material line with unit cost
// + rate source (where the numbers came from)

interface DetailProps {
  appearFrame: number;
}

export const WorkItemDetail: React.FC<DetailProps> = ({ appearFrame }) => {
  const frame = useCurrentFrame();
  const rel = frame - appearFrame;
  if (rel < 0) return null;

  const slideIn = spring({
    frame: rel,
    fps: 30,
    config: { damping: 18, stiffness: 100 },
  });
  const op = interpolate(rel, [0, 10], [0, 1], {
    extrapolateRight: "clamp",
  });

  const F = 30;

  return (
    <div
      style={{
        opacity: op,
        transform: `translateX(${(1 - slideIn) * 30}px)`,
      }}
    >
      {/* Back button */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 6,
          marginBottom: 10,
          fontSize: 11,
          color: colors.machine,
          fontWeight: 500,
          cursor: "pointer",
        }}
      >
        <span style={{ fontSize: 14 }}>&larr;</span>
        <span>Back to Work Items</span>
      </div>

      {/* Item header */}
      <div
        style={{
          backgroundColor: colors.machineWash,
          borderRadius: radius.lg,
          padding: "10px 12px",
          marginBottom: 12,
          border: `1px solid ${colors.machine}`,
        }}
      >
        <div style={{ fontSize: 13, fontWeight: 600, marginBottom: 2 }}>
          Island floor box (core drill)
        </div>
        <div style={{ fontSize: 11, color: colors.mutedForeground }}>
          Item 13 &bull; 2 EA &bull; Kitchen Circuits
        </div>
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "baseline",
            marginTop: 6,
            paddingTop: 6,
            borderTop: `1px solid rgba(245,184,0,0.3)`,
          }}
        >
          <span style={{ fontSize: 11, color: colors.secondaryForeground }}>
            Total cost
          </span>
          <span
            style={{
              fontSize: 16,
              fontWeight: 700,
              color: colors.machine,
              fontFamily: fonts.mono,
            }}
          >
            $586
          </span>
        </div>
      </div>

      {/* ── LABOUR SECTION ──────────────────────── */}
      {rel >= 8 && (
        <div style={{ opacity: interpolate(rel, [8, 14], [0, 1], { extrapolateRight: "clamp" }) }}>
          <div
            style={{
              fontSize: 10,
              fontWeight: 600,
              textTransform: "uppercase" as const,
              letterSpacing: 0.8,
              color: colors.secondaryForeground,
              marginBottom: 6,
              paddingBottom: 3,
              borderBottom: `1px solid ${colors.border}`,
            }}
          >
            Labour &mdash; 3.6 hrs &mdash; $342
          </div>

          {/* Productivity rate source */}
          <div
            style={{
              backgroundColor: "#fef9e7",
              border: `1px solid ${colors.machineWash}`,
              borderRadius: radius.lg,
              padding: "6px 8px",
              marginBottom: 8,
              fontSize: 10,
              color: colors.secondaryForeground,
              lineHeight: 1.5,
            }}
          >
            <div style={{ fontWeight: 600, color: colors.machine, fontSize: 9, marginBottom: 2 }}>
              RATE SOURCE
            </div>
            Your last 2 floor box installs in slab-on-grade averaged{" "}
            <strong>1.8 hrs/box</strong>. Book rate is 1.0 hr &mdash; your actual
            is 80% higher due to slab core drilling.
          </div>

          {/* Labour line items */}
          <div style={{ fontSize: 11 }}>
            <div
              style={{
                display: "grid",
                gridTemplateColumns: "1fr auto auto auto",
                gap: 8,
                padding: "4px 0",
                borderBottom: `1px solid ${colors.border}`,
                color: colors.mutedForeground,
                fontSize: 9,
                fontWeight: 600,
                textTransform: "uppercase" as const,
              }}
            >
              <span>Task</span>
              <span>Rate</span>
              <span>Hrs</span>
              <span style={{ textAlign: "right" }}>Cost</span>
            </div>

            {[
              { task: "Core drill slab (per box)", rate: "$95/hr", hrs: "2.0", cost: "$190" },
              { task: "Install box + receptacle", rate: "$95/hr", hrs: "1.6", cost: "$152" },
            ].map((row, i) => (
              <div
                key={i}
                style={{
                  display: "grid",
                  gridTemplateColumns: "1fr auto auto auto",
                  gap: 8,
                  padding: "5px 0",
                  borderBottom: `1px solid ${colors.border}`,
                  fontSize: 11,
                  opacity: interpolate(rel, [10 + i * 6, 14 + i * 6], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }),
                }}
              >
                <span style={{ color: colors.foreground }}>{row.task}</span>
                <span style={{ fontFamily: fonts.mono, fontSize: 10, color: colors.mutedForeground }}>{row.rate}</span>
                <span style={{ fontFamily: fonts.mono, fontSize: 10, color: colors.mutedForeground }}>{row.hrs}</span>
                <span style={{ fontFamily: fonts.mono, fontSize: 10, textAlign: "right", fontWeight: 500 }}>{row.cost}</span>
              </div>
            ))}

            {/* Labour total */}
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                padding: "4px 0",
                fontSize: 11,
                fontWeight: 600,
                fontStyle: "italic",
                color: colors.secondaryForeground,
              }}
            >
              <span>Labour subtotal</span>
              <span style={{ fontFamily: fonts.mono, fontSize: 10 }}>$342</span>
            </div>
          </div>
        </div>
      )}

      {/* ── MATERIALS SECTION ──────────────────── */}
      {rel >= F && (
        <div
          style={{
            marginTop: 12,
            opacity: interpolate(rel, [F, F + 8], [0, 1], { extrapolateRight: "clamp" }),
          }}
        >
          <div
            style={{
              fontSize: 10,
              fontWeight: 600,
              textTransform: "uppercase" as const,
              letterSpacing: 0.8,
              color: colors.secondaryForeground,
              marginBottom: 6,
              paddingBottom: 3,
              borderBottom: `1px solid ${colors.border}`,
            }}
          >
            Materials &mdash; $244
          </div>

          <div style={{ fontSize: 11 }}>
            <div
              style={{
                display: "grid",
                gridTemplateColumns: "1fr auto auto auto",
                gap: 8,
                padding: "4px 0",
                borderBottom: `1px solid ${colors.border}`,
                color: colors.mutedForeground,
                fontSize: 9,
                fontWeight: 600,
                textTransform: "uppercase" as const,
              }}
            >
              <span>Item</span>
              <span>Qty</span>
              <span>Unit cost</span>
              <span style={{ textAlign: "right" }}>Cost</span>
            </div>

            {[
              { item: "Floor box (Arlington FLBR5420)", qty: "2", unit: "$68.00", cost: "$136" },
              { item: "Duplex receptacle (Leviton)", qty: "2", unit: "$12.00", cost: "$24" },
              { item: "Cover plate (brass)", qty: "2", unit: "$8.00", cost: "$16" },
              { item: "Conduit + wire (est. 20 LF)", qty: "1", unit: "$48.00", cost: "$48" },
              { item: "Core drill bit rental", qty: "1", unit: "$20.00", cost: "$20" },
            ].map((row, i) => (
              <div
                key={i}
                style={{
                  display: "grid",
                  gridTemplateColumns: "1fr auto auto auto",
                  gap: 8,
                  padding: "4px 0",
                  borderBottom: `1px solid ${colors.border}`,
                  fontSize: 11,
                  opacity: interpolate(rel, [F + 4 + i * 4, F + 8 + i * 4], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }),
                }}
              >
                <span style={{ color: colors.foreground }}>{row.item}</span>
                <span style={{ fontFamily: fonts.mono, fontSize: 10, color: colors.mutedForeground }}>{row.qty}</span>
                <span style={{ fontFamily: fonts.mono, fontSize: 10, color: colors.mutedForeground }}>{row.unit}</span>
                <span style={{ fontFamily: fonts.mono, fontSize: 10, textAlign: "right", fontWeight: 500 }}>{row.cost}</span>
              </div>
            ))}

            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                padding: "4px 0",
                fontSize: 11,
                fontWeight: 600,
                fontStyle: "italic",
                color: colors.secondaryForeground,
              }}
            >
              <span>Materials subtotal</span>
              <span style={{ fontFamily: fonts.mono, fontSize: 10 }}>$244</span>
            </div>
          </div>
        </div>
      )}

      {/* ── MARGIN & TOTAL ────────────────────── */}
      {rel >= 2 * F && (
        <div
          style={{
            marginTop: 12,
            opacity: interpolate(rel, [2 * F, 2 * F + 8], [0, 1], { extrapolateRight: "clamp" }),
          }}
        >
          <div style={{ fontSize: 11, padding: "4px 0", display: "flex", justifyContent: "space-between", borderBottom: `1px solid ${colors.border}` }}>
            <span style={{ color: colors.mutedForeground }}>Labour</span>
            <span style={{ fontFamily: fonts.mono, fontSize: 10 }}>$342</span>
          </div>
          <div style={{ fontSize: 11, padding: "4px 0", display: "flex", justifyContent: "space-between", borderBottom: `1px solid ${colors.border}` }}>
            <span style={{ color: colors.mutedForeground }}>Materials</span>
            <span style={{ fontFamily: fonts.mono, fontSize: 10 }}>$244</span>
          </div>
          <div style={{ fontSize: 11, padding: "4px 0", display: "flex", justifyContent: "space-between", borderBottom: `1px solid ${colors.border}`, fontStyle: "italic" }}>
            <span style={{ color: colors.mutedForeground }}>Subtotal (cost)</span>
            <span style={{ fontFamily: fonts.mono, fontSize: 10 }}>$488</span>
          </div>
          <div style={{ fontSize: 11, padding: "4px 0", display: "flex", justifyContent: "space-between", borderBottom: `1px solid ${colors.border}` }}>
            <span style={{ color: colors.mutedForeground }}>Margin (20%)</span>
            <span style={{ fontFamily: fonts.mono, fontSize: 10 }}>$98</span>
          </div>
          <div style={{ fontSize: 13, padding: "6px 0", display: "flex", justifyContent: "space-between", borderTop: `2px solid ${colors.machine}`, marginTop: 2, fontWeight: 700 }}>
            <span>Sell price</span>
            <span style={{ fontFamily: fonts.mono, color: colors.machine }}>$586</span>
          </div>
        </div>
      )}

      {/* ── HISTORY NOTE ─────────────────────── */}
      {rel >= 2.5 * F && (
        <div
          style={{
            marginTop: 10,
            backgroundColor: colors.machineWash,
            borderRadius: radius.lg,
            padding: "6px 8px",
            fontSize: 9.5,
            color: colors.secondaryForeground,
            lineHeight: 1.5,
            opacity: interpolate(rel, [2.5 * F, 2.5 * F + 8], [0, 1], { extrapolateRight: "clamp" }),
          }}
        >
          <strong style={{ color: colors.machine }}>Agent note:</strong> Adjusted from 1.0 hr/box
          (book rate) to 1.8 hr/box based on your Verde Valley and Scottsdale jobs.
          Both were slab-on-grade core drills. Your margin on this item is lower than
          your 20% target if you hit 1.8 hrs &mdash; at book rate you'd have 38% margin.
        </div>
      )}
    </div>
  );
};
