import React from "react";
import { interpolate, useCurrentFrame, spring } from "remotion";
import { colors, fonts, radius } from "./styles";

interface ChatBubbleProps {
  speaker: "user" | "kerf";
  text: string | React.ReactNode;
  appearFrame: number;
  stageDirection?: string;
}

export const ChatBubble: React.FC<ChatBubbleProps> = ({
  speaker,
  text,
  appearFrame,
  stageDirection,
}) => {
  const frame = useCurrentFrame();
  const rel = frame - appearFrame;
  if (rel < 0) return null;

  const slideUp = spring({
    frame: rel,
    fps: 30,
    config: { damping: 18, stiffness: 120 },
  });
  const opacity = interpolate(rel, [0, 8], [0, 1], {
    extrapolateRight: "clamp",
  });

  const isKerf = speaker === "kerf";

  return (
    <div
      style={{
        opacity,
        transform: `translateY(${(1 - slideUp) * 16}px)`,
        marginBottom: 8,
        display: "flex",
        justifyContent: isKerf ? "flex-start" : "flex-end",
      }}
    >
      <div
        style={{
          maxWidth: "88%",
          padding: "8px 12px",
          borderRadius: 8,
          backgroundColor: isKerf ? colors.kerfBubbleBg : colors.userBubbleBg,
          color: isKerf ? colors.kerfBubbleText : colors.userBubbleText,
          border: isKerf ? `1px solid ${colors.kerfBubbleBorder}` : "none",
          fontSize: 12.5,
          lineHeight: 1.55,
          fontFamily: fonts.sans,
          boxShadow: isKerf ? "0 1px 2px rgba(0,0,0,0.04)" : "none",
        }}
      >
        {stageDirection && (
          <div
            style={{
              fontSize: 10.5,
              fontStyle: "italic",
              color: isKerf ? colors.mutedForeground : "rgba(255,255,255,0.5)",
              marginBottom: 3,
            }}
          >
            {stageDirection}
          </div>
        )}
        {typeof text === "string" ? <span>{text}</span> : text}
      </div>
    </div>
  );
};

// ── Typing indicator ────────────────────────────────────────
export const TypingIndicator: React.FC<{ appearFrame: number; hideFrame?: number }> = ({
  appearFrame,
  hideFrame,
}) => {
  const frame = useCurrentFrame();
  const rel = frame - appearFrame;
  if (rel < 0) return null;
  if (hideFrame && frame >= hideFrame) return null;

  return (
    <div style={{ marginBottom: 8, display: "flex" }}>
      <div
        style={{
          padding: "8px 14px",
          borderRadius: 8,
          backgroundColor: colors.card,
          border: `1px solid ${colors.border}`,
          display: "flex",
          gap: 4,
          alignItems: "center",
        }}
      >
        {[0, 1, 2].map((i) => (
          <div
            key={i}
            style={{
              width: 5,
              height: 5,
              borderRadius: 3,
              backgroundColor: colors.mutedForeground,
              opacity:
                0.25 + 0.6 * Math.sin(((rel + i * 4) / 8) * Math.PI),
            }}
          />
        ))}
      </div>
    </div>
  );
};
