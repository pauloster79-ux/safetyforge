import React from "react";
import { interpolate, useCurrentFrame, spring } from "remotion";
import { colors, fonts, radius } from "./styles";

interface WorkItemRowProps {
  index: number;
  description: string;
  qty: string;
  unit: string;
  amount: string;
  appearFrame: number;
  isSubtotal?: boolean;
  isTotal?: boolean;
  isDivision?: boolean;
  highlight?: boolean;
  // Two-line breakdown
  labourHrs?: string;
  labourCost?: string;
  materialCost?: string;
}

export const WorkItemRow: React.FC<WorkItemRowProps> = ({
  index,
  description,
  qty,
  unit,
  amount,
  appearFrame,
  isSubtotal,
  isTotal,
  isDivision,
  highlight,
  labourHrs,
  labourCost,
  materialCost,
}) => {
  const frame = useCurrentFrame();
  const rel = frame - appearFrame;
  if (rel < 0) return null;

  const slideIn = spring({
    frame: rel,
    fps: 30,
    config: { damping: 20, stiffness: 150 },
  });
  const opacity = interpolate(rel, [0, 6], [0, 1], {
    extrapolateRight: "clamp",
  });

  if (isDivision) {
    return (
      <div
        style={{
          opacity,
          transform: `translateX(${(1 - slideIn) * 20}px)`,
          padding: "5px 8px",
          fontSize: 10,
          fontWeight: 600,
          textTransform: "uppercase" as const,
          letterSpacing: 0.8,
          color: colors.machine,
          backgroundColor: colors.machineWash,
          borderRadius: radius.lg,
          marginTop: 6,
          marginBottom: 2,
        }}
      >
        {description}
      </div>
    );
  }

  if (isTotal) {
    return (
      <div
        style={{
          opacity,
          transform: `translateX(${(1 - slideIn) * 20}px)`,
          display: "flex",
          justifyContent: "space-between",
          padding: "8px",
          borderTop: `2px solid ${colors.machine}`,
          marginTop: 6,
        }}
      >
        <span style={{ fontWeight: 600, fontSize: 13 }}>{description}</span>
        <span
          style={{
            fontWeight: 700,
            fontSize: 15,
            color: colors.machine,
            fontFamily: fonts.mono,
          }}
        >
          {amount}
        </span>
      </div>
    );
  }

  if (isSubtotal) {
    return (
      <div
        style={{
          opacity,
          transform: `translateX(${(1 - slideIn) * 20}px)`,
          display: "flex",
          justifyContent: "space-between",
          padding: "3px 8px",
          borderTop: `1px solid ${colors.border}`,
          fontSize: 11,
          color: colors.mutedForeground,
          fontStyle: "italic",
        }}
      >
        <span>{description}</span>
        <span style={{ fontFamily: fonts.mono, fontWeight: 500 }}>{amount}</span>
      </div>
    );
  }

  const hasBreakdown = labourHrs || materialCost;

  return (
    <div
      style={{
        opacity,
        transform: `translateX(${(1 - slideIn) * 14}px)`,
        padding: "4px 8px",
        borderBottom: `1px solid ${colors.border}`,
        backgroundColor: highlight ? colors.machineWash : "transparent",
        borderRadius: highlight ? radius.lg : 0,
      }}
    >
      {/* Line 1: description + qty + amount */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "22px 1fr 40px 30px 70px",
          gap: 4,
          fontSize: 11,
          alignItems: "center",
        }}
      >
        <span style={{ color: colors.mutedForeground, fontSize: 10 }}>{index}</span>
        <span style={{ color: colors.foreground }}>{description}</span>
        <span style={{ color: colors.mutedForeground, textAlign: "right", fontSize: 10 }}>
          {qty}
        </span>
        <span style={{ color: colors.mutedForeground, fontSize: 9 }}>{unit}</span>
        <span
          style={{
            textAlign: "right",
            fontFamily: fonts.mono,
            color: colors.secondaryForeground,
            fontSize: 10,
          }}
        >
          {amount}
        </span>
      </div>

      {/* Line 2: labour + materials breakdown (muted, smaller) */}
      {hasBreakdown && (
        <div
          style={{
            paddingLeft: 26,
            marginTop: 1,
            fontSize: 9.5,
            color: colors.mutedForeground,
            display: "flex",
            gap: 8,
          }}
        >
          {labourHrs && (
            <span>
              {labourHrs} hrs
              {labourCost && (
                <span style={{ fontFamily: fonts.mono, marginLeft: 3 }}>{labourCost}</span>
              )}
            </span>
          )}
          {labourHrs && materialCost && (
            <span style={{ color: colors.border }}>·</span>
          )}
          {materialCost && (
            <span>
              materials{" "}
              <span style={{ fontFamily: fonts.mono }}>{materialCost}</span>
            </span>
          )}
        </div>
      )}
    </div>
  );
};
