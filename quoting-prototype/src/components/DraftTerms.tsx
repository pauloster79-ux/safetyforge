import React from "react";
import { interpolate, useCurrentFrame, spring } from "remotion";
import { colors, fonts, radius } from "./styles";

// ── Assumption card (editable in draft) ─────────────────────
interface AssumptionProps {
  category: string;
  statement: string;
  variationTrigger: boolean;
  reliedOnValue?: string;
  appearFrame: number;
  fromTemplate?: boolean;
}

export const AssumptionCard: React.FC<AssumptionProps> = ({
  category,
  statement,
  variationTrigger,
  reliedOnValue,
  appearFrame,
  fromTemplate,
}) => {
  const frame = useCurrentFrame();
  const rel = frame - appearFrame;
  if (rel < 0) return null;

  const s = spring({ frame: rel, fps: 30, config: { damping: 18 } });
  const op = interpolate(rel, [0, 8], [0, 1], { extrapolateRight: "clamp" });

  return (
    <div
      style={{
        opacity: op,
        transform: `translateY(${(1 - s) * 12}px)`,
        backgroundColor: colors.card,
        border: `1px solid ${colors.border}`,
        borderRadius: radius.lg,
        padding: "8px 10px",
        marginBottom: 4,
        fontSize: 11,
        lineHeight: 1.5,
      }}
    >
      {/* Top row: category badge + variation trigger toggle */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          marginBottom: 4,
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
          <span
            style={{
              fontSize: 9,
              fontWeight: 600,
              textTransform: "uppercase" as const,
              letterSpacing: 0.5,
              color: colors.machine,
              backgroundColor: colors.machineWash,
              padding: "1px 6px",
              borderRadius: radius.badge,
            }}
          >
            {category}
          </span>
          {fromTemplate && (
            <span
              style={{
                fontSize: 8,
                color: colors.mutedForeground,
                fontStyle: "italic",
              }}
            >
              from template
            </span>
          )}
        </div>

        {/* Variation trigger toggle */}
        <div style={{ display: "flex", alignItems: "center", gap: 4 }}>
          <span
            style={{
              fontSize: 9,
              color: variationTrigger ? colors.pass : colors.mutedForeground,
            }}
          >
            Variation trigger
          </span>
          <div
            style={{
              width: 26,
              height: 14,
              borderRadius: 7,
              backgroundColor: variationTrigger ? colors.pass : colors.muted,
              position: "relative",
              cursor: "pointer",
            }}
          >
            <div
              style={{
                width: 10,
                height: 10,
                borderRadius: 5,
                backgroundColor: "#fff",
                position: "absolute",
                top: 2,
                left: variationTrigger ? 14 : 2,
                boxShadow: "0 1px 2px rgba(0,0,0,0.15)",
              }}
            />
          </div>
        </div>
      </div>

      {/* Statement text */}
      <div style={{ color: colors.foreground }}>{statement}</div>

      {/* Relied-on value */}
      {reliedOnValue && (
        <div
          style={{
            marginTop: 3,
            fontSize: 10,
            color: colors.mutedForeground,
            fontFamily: fonts.mono,
          }}
        >
          Relied on: {reliedOnValue}
        </div>
      )}
    </div>
  );
};

// ── Exclusion card (editable in draft) ──────────────────────
interface ExclusionProps {
  statement: string;
  partialInclusion?: string;
  appearFrame: number;
  fromTemplate?: boolean;
  isHighlight?: boolean;
}

export const ExclusionCard: React.FC<ExclusionProps> = ({
  statement,
  partialInclusion,
  appearFrame,
  fromTemplate,
  isHighlight,
}) => {
  const frame = useCurrentFrame();
  const rel = frame - appearFrame;
  if (rel < 0) return null;

  const s = spring({ frame: rel, fps: 30, config: { damping: 18 } });
  const op = interpolate(rel, [0, 8], [0, 1], { extrapolateRight: "clamp" });

  return (
    <div
      style={{
        opacity: op,
        transform: `translateY(${(1 - s) * 12}px)`,
        backgroundColor: isHighlight ? colors.machineWash : colors.card,
        border: `1px solid ${isHighlight ? colors.machine : colors.border}`,
        borderRadius: radius.lg,
        padding: "6px 10px",
        marginBottom: 4,
        fontSize: 11,
        lineHeight: 1.5,
        display: "flex",
        alignItems: "flex-start",
        gap: 6,
      }}
    >
      {/* X icon */}
      <span
        style={{
          color: colors.fail,
          fontSize: 10,
          fontWeight: 700,
          marginTop: 1,
          flexShrink: 0,
        }}
      >
        ✕
      </span>

      <div style={{ flex: 1 }}>
        <span style={{ color: colors.foreground }}>{statement}</span>
        {partialInclusion && (
          <span style={{ color: colors.pass, fontSize: 10 }}>
            {" "}
            (we include: {partialInclusion})
          </span>
        )}
        {fromTemplate && (
          <span
            style={{
              fontSize: 8,
              color: colors.mutedForeground,
              fontStyle: "italic",
              marginLeft: 4,
            }}
          >
            template
          </span>
        )}
      </div>
    </div>
  );
};

// ── Additional work rates ───────────────────────────────────
interface RateRowProps {
  resource: string;
  rate: string;
  appearFrame: number;
}

export const AdditionalWorkRate: React.FC<RateRowProps> = ({
  resource,
  rate,
  appearFrame,
}) => {
  const frame = useCurrentFrame();
  const rel = frame - appearFrame;
  if (rel < 0) return null;

  const op = interpolate(rel, [0, 6], [0, 1], { extrapolateRight: "clamp" });

  return (
    <div
      style={{
        opacity: op,
        display: "flex",
        justifyContent: "space-between",
        padding: "3px 8px",
        fontSize: 11,
        borderBottom: `1px solid ${colors.border}`,
      }}
    >
      <span style={{ color: colors.foreground }}>{resource}</span>
      <span
        style={{
          fontFamily: fonts.mono,
          fontWeight: 500,
          color: colors.secondaryForeground,
          fontSize: 10,
        }}
      >
        {rate}
      </span>
    </div>
  );
};

// ── Section header ──────────────────────────────────────────
interface SectionHeaderProps {
  title: string;
  count?: number;
  appearFrame: number;
  action?: string;
}

export const SectionHeader: React.FC<SectionHeaderProps> = ({
  title,
  count,
  appearFrame,
  action,
}) => {
  const frame = useCurrentFrame();
  const rel = frame - appearFrame;
  if (rel < 0) return null;

  const op = interpolate(rel, [0, 6], [0, 1], { extrapolateRight: "clamp" });

  return (
    <div
      style={{
        opacity: op,
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        marginTop: 12,
        marginBottom: 6,
        paddingBottom: 4,
        borderBottom: `1px solid ${colors.border}`,
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
        <span
          style={{
            fontSize: 10,
            fontWeight: 600,
            textTransform: "uppercase" as const,
            letterSpacing: 0.8,
            color: colors.secondaryForeground,
          }}
        >
          {title}
        </span>
        {count !== undefined && (
          <span
            style={{
              fontSize: 9,
              color: colors.mutedForeground,
              backgroundColor: colors.muted,
              padding: "0 5px",
              borderRadius: radius.badge,
            }}
          >
            {count}
          </span>
        )}
      </div>
      {action && (
        <span
          style={{
            fontSize: 10,
            color: colors.machine,
            fontWeight: 500,
            cursor: "pointer",
          }}
        >
          + {action}
        </span>
      )}
    </div>
  );
};
