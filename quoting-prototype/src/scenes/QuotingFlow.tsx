import React from "react";
import {
  AbsoluteFill,
  useCurrentFrame,
  interpolate,
  spring,
} from "remotion";
import { IconRail, ChatHeader, ChatInputBar } from "../components/AppChrome";
import { ChatBubble, TypingIndicator } from "../components/ChatBubble";
import { WorkItemRow } from "../components/WorkItemRow";
import {
  AssumptionCard,
  ExclusionCard,
  AdditionalWorkRate,
  SectionHeader,
} from "../components/DraftTerms";
import { WorkItemDetail } from "../components/WorkItemDetail";
import { colors, fonts, radius, baseContainer } from "../components/styles";

// ── Timing ──────────────────────────────────────────────────
const F = 30;
const CHAT_START = 2 * F;
const CANVAS_START = 22 * F;
const DETAIL_START = 35 * F;    // Open item 13 detail view
const DETAIL_END = 45 * F;      // Close detail, back to list
const TERMS_START = 45 * F;
const RATES_START = 55 * F;
const DOC_START = 65 * F;

export const QuotingFlow: React.FC = () => {
  const frame = useCurrentFrame();

  const showCanvas = frame >= CANVAS_START - 10;
  const canvasWidth = showCanvas
    ? interpolate(frame, [CANVAS_START - 10, CANVAS_START + 15], [0, 1], {
        extrapolateLeft: "clamp",
        extrapolateRight: "clamp",
      })
    : 0;

  const showDoc = frame >= DOC_START;
  const docOp = showDoc
    ? interpolate(frame, [DOC_START, DOC_START + 15], [0, 1], {
        extrapolateRight: "clamp",
      })
    : 0;

  return (
    <AbsoluteFill>
      <div style={{
        position: "absolute", top: 0, left: 0, right: 0, bottom: 0,
        display: "flex", flexDirection: "row",
        backgroundColor: colors.bg, fontFamily: fonts.sans, color: colors.foreground,
      }}>
      {/* ── Icon Rail ──────────────────────────── */}
      <IconRail />

      {/* ── Desktop layout: ChatPane + CanvasPane */}
      <div style={{ flex: 1, display: "flex", flexDirection: "row" }}>
        {/* ── ChatPane (40% when canvas open, 100% otherwise) */}
        <div
          style={{
            width: canvasWidth > 0 ? "40%" : "100%",
            minWidth: 360,
            display: "flex",
            flexDirection: "column",
            transition: "width 0.2s",
          }}
        >
          {/* Chat header */}
          <ChatHeader />

          {/* Messages area — overflow-y-auto, messages top-down */}
          <div
            style={{
              flex: 1,
              overflowY: "auto",
              padding: "16px 16px",
            }}
          >
            <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
              <ChatBubble
                speaker="user"
                text="Starting a quote. Maria Gonzalez, 1847 East Meadow Drive. 200-amp panel upgrade and kitchen circuits."
                appearFrame={CHAT_START}
                stageDirection="standing in the client's kitchen"
              />

              <TypingIndicator
                appearFrame={CHAT_START + 2 * F}
                hideFrame={CHAT_START + 3 * F}
              />

              <ChatBubble
                speaker="kerf"
                text="Got it — new quote created. Homeowner direct or subbing to a GC?"
                appearFrame={CHAT_START + 3 * F}
              />

              <ChatBubble
                speaker="user"
                text="Direct to homeowner."
                appearFrame={CHAT_START + 5 * F}
              />

              <ChatBubble
                speaker="user"
                text="Main panel is in the garage, 150-amp Federal Pacific Stab-Lok. Replacing with 200-amp, 40-space. Service entrance cable from the meter is about 15 feet."
                appearFrame={CHAT_START + 7 * F}
              />

              <TypingIndicator
                appearFrame={CHAT_START + 9 * F}
                hideFrame={CHAT_START + 10 * F}
              />

              <ChatBubble
                speaker="kerf"
                text={
                  <span>
                    On your last three panel swaps, APS coordination averaged a{" "}
                    <strong style={{ color: colors.machine }}>2-hour wait</strong>.
                    Including that in your labour.
                    <br /><br />
                    Also — the Federal Pacific may have asbestos in the panel backing.
                    Your <strong style={{ color: colors.machine }}>Verde Valley job</strong>{" "}
                    had that. I've added it as an exclusion.
                  </span>
                }
                appearFrame={CHAT_START + 10 * F}
              />

              <ChatBubble
                speaker="user"
                text="Good calls. Kitchen next — 2 dedicated GFCI for countertops, dishwasher, disposal, gas range igniter, microwave. 6 countertop receptacles, 2 island floor boxes, under-cabinet LEDs on a dimmer."
                appearFrame={CHAT_START + 13 * F}
              />

              <TypingIndicator
                appearFrame={CHAT_START + 15 * F}
                hideFrame={CHAT_START + 16 * F}
              />

              <ChatBubble
                speaker="kerf"
                text={
                  <div>
                    <div>Three things from your history:</div>
                    <div style={{ marginTop: 4 }}>
                      <div style={{ marginBottom: 3 }}>
                        <strong style={{ color: colors.machine }}>1.</strong>{" "}
                        Island floor boxes in slab-on-grade — your actual is{" "}
                        <strong style={{ color: colors.machine }}>1.8 hrs</strong>, not the
                        1 hr you usually quote. Using 1.8.
                      </div>
                      <div style={{ marginBottom: 3 }}>
                        <strong style={{ color: colors.machine }}>2.</strong>{" "}
                        AFCI breakers required on all kitchen circuits (2021 NEC). Added at ~$45/ea.
                      </div>
                      <div>
                        <strong style={{ color: colors.machine }}>3.</strong>{" "}
                        Phoenix permit fee is $134 — you've eaten this on your last 4 jobs. Including it.
                      </div>
                    </div>
                  </div>
                }
                appearFrame={CHAT_START + 16 * F}
              />

              <ChatBubble
                speaker="user"
                text="She's buying the LED fixtures, I'm just doing the wiring. Everything else looks right."
                appearFrame={CHAT_START + 19 * F}
              />
            </div>
          </div>

          {/* Chat input bar */}
          <ChatInputBar />
        </div>

        {/* ── CanvasPane (60%, slides in) ──────── */}
        {canvasWidth > 0 && (
          <div
            style={{
              flex: 1,
              minWidth: 400,
              borderLeft: `1px solid ${colors.border}`,
              backgroundColor: colors.card,
              display: "flex",
              flexDirection: "column",
              overflow: "hidden",
              opacity: interpolate(canvasWidth, [0, 0.5, 1], [0, 0, 1]),
            }}
          >
            {canvasWidth > 0.6 && (
              <>
                {/* Canvas header */}
                <div
                  style={{
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "space-between",
                    borderBottom: `1px solid ${colors.border}`,
                    padding: "10px 16px",
                    backgroundColor: colors.card,
                  }}
                >
                  <div>
                    <div style={{ fontSize: 13, fontWeight: 600, color: colors.foreground }}>
                      Gonzalez Kitchen + Panel
                    </div>
                    <div style={{ fontSize: 11, color: colors.mutedForeground }}>
                      Maria Gonzalez — 1847 E Meadow Dr, Phoenix
                    </div>
                  </div>
                  <div
                    style={{
                      padding: "2px 8px",
                      borderRadius: radius.badge,
                      fontSize: 10,
                      fontWeight: 600,
                      textTransform: "uppercase" as const,
                      letterSpacing: 0.5,
                      backgroundColor: frame >= DOC_START ? colors.passBg : colors.machineWash,
                      color: frame >= DOC_START ? colors.pass : colors.machine,
                    }}
                  >
                    {frame >= DOC_START ? "Ready" : "Building"}
                  </div>
                </div>

                {/* Tabs */}
                <div
                  style={{
                    display: "flex",
                    backgroundColor: colors.muted,
                    padding: 3,
                    margin: "8px 12px 0",
                    borderRadius: radius.input,
                    gap: 2,
                  }}
                >
                  {["Work Items", "Terms", "Rates"].map((tab) => {
                    const isActive =
                      (tab === "Work Items" && frame < TERMS_START) ||
                      (tab === "Terms" && frame >= TERMS_START && frame < RATES_START) ||
                      (tab === "Rates" && frame >= RATES_START && frame < DOC_START);
                    return (
                      <div
                        key={tab}
                        style={{
                          flex: 1,
                          textAlign: "center",
                          padding: "4px 8px",
                          fontSize: 11,
                          fontWeight: isActive ? 600 : 400,
                          color: isActive ? colors.foreground : colors.mutedForeground,
                          backgroundColor: isActive ? colors.card : "transparent",
                          borderRadius: radius.lg,
                          border: isActive ? `1px solid ${colors.border}` : "1px solid transparent",
                        }}
                      >
                        {tab}
                        {tab === "Terms" && frame >= TERMS_START && (
                          <span style={{
                            marginLeft: 4, fontSize: 9,
                            backgroundColor: colors.machineWash, color: colors.machine,
                            padding: "0 4px", borderRadius: radius.badge, fontWeight: 600,
                          }}>9</span>
                        )}
                      </div>
                    );
                  })}
                </div>

                {/* Tab content */}
                <div style={{ flex: 1, overflow: "auto", padding: "4px 12px 12px" }}>

                  {/* ── Work Item Detail view ──── */}
                  {frame >= DETAIL_START && frame < DETAIL_END && (
                    <WorkItemDetail appearFrame={DETAIL_START} />
                  )}

                  {/* ── Work Items tab ──────────── */}
                  {frame < DETAIL_START && (
                    <>
                      <SectionHeader title="Work Items" count={17} appearFrame={CANVAS_START} action="Add item" />
                      <WorkItemRow index={0} description="Panel Upgrade" qty="" unit="" amount="" appearFrame={CANVAS_START + 5} isDivision />
                      <WorkItemRow index={1} description="Remove Federal Pacific 150A" qty="1" unit="EA" amount="$258" appearFrame={CANVAS_START + 12} labourHrs="2.5" labourCost="$171" materialCost="$87" />
                      <WorkItemRow index={2} description="Supply + install 200A 40-space" qty="1" unit="EA" amount="$1,240" appearFrame={CANVAS_START + 18} labourHrs="3.2" labourCost="$304" materialCost="$936" />
                      <WorkItemRow index={3} description="Service entrance cable (~15 LF)" qty="15" unit="LF" amount="$485" appearFrame={CANVAS_START + 24} labourHrs="1.5" labourCost="$143" materialCost="$342" />
                      <WorkItemRow index={4} description="Transfer existing circuits + test" qty="1" unit="LS" amount="$570" appearFrame={CANVAS_START + 30} labourHrs="6.0" labourCost="$570" />
                      <WorkItemRow index={5} description="APS disconnect + wait" qty="1" unit="LS" amount="$380" appearFrame={CANVAS_START + 36} highlight labourHrs="4.0" labourCost="$380" />
                      <WorkItemRow index={6} description="Ground rod and bonding" qty="1" unit="LS" amount="$347" appearFrame={CANVAS_START + 42} labourHrs="1.5" labourCost="$143" materialCost="$204" />
                      <WorkItemRow index={0} description="Panel subtotal" qty="" unit="" amount="$3,280" appearFrame={CANVAS_START + 48} isSubtotal />
                      <WorkItemRow index={0} description="Kitchen Circuits" qty="" unit="" amount="" appearFrame={CANVAS_START + F * 2} isDivision />
                      <WorkItemRow index={7} description="Ded. 20A GFCI countertop (×2)" qty="2" unit="EA" amount="$520" appearFrame={CANVAS_START + F * 2 + 8} labourHrs="2.4" labourCost="$228" materialCost="$292" />
                      <WorkItemRow index={8} description="Ded. 20A dishwasher" qty="1" unit="EA" amount="$245" appearFrame={CANVAS_START + F * 2 + 14} labourHrs="1.2" labourCost="$114" materialCost="$131" />
                      <WorkItemRow index={9} description="Ded. 20A disposal" qty="1" unit="EA" amount="$245" appearFrame={CANVAS_START + F * 2 + 20} labourHrs="1.2" labourCost="$114" materialCost="$131" />
                      <WorkItemRow index={10} description="Gas range igniter outlet" qty="1" unit="EA" amount="$165" appearFrame={CANVAS_START + F * 2 + 26} labourHrs="0.8" labourCost="$76" materialCost="$89" />
                      <WorkItemRow index={11} description="Microwave circuit" qty="1" unit="EA" amount="$255" appearFrame={CANVAS_START + F * 3} labourHrs="1.2" labourCost="$114" materialCost="$141" />
                      <WorkItemRow index={12} description="Countertop GFCI receptacles" qty="6" unit="EA" amount="$684" appearFrame={CANVAS_START + F * 3 + 8} labourHrs="2.3" labourCost="$219" materialCost="$465" />
                      <WorkItemRow index={13} description="Island floor box (core drill)" qty="2" unit="EA" amount="$586" appearFrame={CANVAS_START + F * 3 + 14} highlight labourHrs="3.6" labourCost="$342" materialCost="$244" />
                      <WorkItemRow index={14} description="Under-cabinet LED wiring" qty="1" unit="LS" amount="$320" appearFrame={CANVAS_START + F * 3 + 20} labourHrs="2.0" labourCost="$190" materialCost="$130" />
                      <WorkItemRow index={15} description="AFCI breakers (×6)" qty="6" unit="EA" amount="$270" appearFrame={CANVAS_START + F * 3 + 26} highlight materialCost="$270" />
                      <WorkItemRow index={0} description="Kitchen subtotal" qty="" unit="" amount="$4,840" appearFrame={CANVAS_START + F * 4} isSubtotal />
                      <WorkItemRow index={0} description="Other" qty="" unit="" amount="" appearFrame={CANVAS_START + F * 4 + 10} isDivision />
                      <WorkItemRow index={16} description="Phoenix electrical permit" qty="1" unit="EA" amount="$134" appearFrame={CANVAS_START + F * 4 + 16} highlight />
                      <WorkItemRow index={17} description="Final inspection" qty="1" unit="LS" amount="" appearFrame={CANVAS_START + F * 4 + 22} labourHrs="1.0" labourCost="$95" />
                      <WorkItemRow index={0} description="TOTAL" qty="" unit="" amount="$8,254" appearFrame={CANVAS_START + F * 5} isTotal />
                    </>
                  )}

                  {/* ── Terms tab ──────────────── */}
                  {frame >= TERMS_START && frame < RATES_START && (
                    <>
                      <SectionHeader title="Assumptions" count={4} appearFrame={TERMS_START} action="Add" />
                      <AssumptionCard category="site conditions" statement="Existing service entrance conduit and meter base in serviceable condition" variationTrigger={true} appearFrame={TERMS_START} />
                      <AssumptionCard category="site conditions" statement="No aluminium branch wiring requiring remediation" variationTrigger={true} appearFrame={TERMS_START + 10} fromTemplate />
                      <AssumptionCard category="coordination" statement="Kitchen contractor will have cabinet locations marked before rough-in" variationTrigger={false} appearFrame={TERMS_START + 20} />
                      <AssumptionCard category="access" statement="Access during normal working hours (7 AM – 4 PM, Mon–Fri)" variationTrigger={false} reliedOnValue="standard hours" appearFrame={TERMS_START + F} fromTemplate />
                      <SectionHeader title="Exclusions" count={5} appearFrame={TERMS_START + 2 * F} action="Add" />
                      <ExclusionCard statement="Under-cabinet LED fixtures" partialInclusion="wiring and transformer" appearFrame={TERMS_START + 2 * F} />
                      <ExclusionCard statement="Asbestos abatement — priced as extra if found" appearFrame={TERMS_START + 2 * F + 10} isHighlight />
                      <ExclusionCard statement="Drywall patching, painting, or finish work" appearFrame={TERMS_START + 2 * F + 20} fromTemplate />
                      <ExclusionCard statement="Work behind meter or on utility side" appearFrame={TERMS_START + 3 * F} fromTemplate />
                      <ExclusionCard statement="Structural modifications to panel location" appearFrame={TERMS_START + 3 * F + 10} />
                    </>
                  )}

                  {/* ── Rates tab ──────────────── */}
                  {frame >= RATES_START && frame < DOC_START && (
                    <>
                      <SectionHeader title="Additional Work Rates" appearFrame={RATES_START} />
                      <AdditionalWorkRate resource="Electrician" rate="$95/hr" appearFrame={RATES_START} />
                      <AdditionalWorkRate resource="Helper" rate="$58/hr" appearFrame={RATES_START + 8} />
                      <AdditionalWorkRate resource="Materials" rate="cost + 15%" appearFrame={RATES_START + 16} />
                      <SectionHeader title="Payment Terms" appearFrame={RATES_START + F} />
                      {frame >= RATES_START + F && (
                        <div style={{ fontSize: 11, color: colors.secondaryForeground, padding: "4px 8px", lineHeight: 1.7 }}>
                          <div style={{ marginBottom: 4 }}>50% deposit on acceptance</div>
                          <div style={{ marginBottom: 4 }}>50% balance on completion + inspection</div>
                          <div style={{ color: colors.mutedForeground, fontSize: 10 }}>Valid 30 days from quote date</div>
                        </div>
                      )}
                      <SectionHeader title="Quote Summary" appearFrame={RATES_START + 2 * F} />
                      {frame >= RATES_START + 2 * F && (
                        <div style={{ padding: "6px 8px" }}>
                          <div style={{ display: "flex", justifyContent: "space-between", fontSize: 11, marginBottom: 3 }}>
                            <span style={{ color: colors.mutedForeground }}>Work items</span>
                            <span style={{ fontFamily: fonts.mono, fontSize: 10 }}>17 items</span>
                          </div>
                          <div style={{ display: "flex", justifyContent: "space-between", fontSize: 11, marginBottom: 3 }}>
                            <span style={{ color: colors.mutedForeground }}>Assumptions</span>
                            <span style={{ fontFamily: fonts.mono, fontSize: 10 }}>4 (2 with triggers)</span>
                          </div>
                          <div style={{ display: "flex", justifyContent: "space-between", fontSize: 11, marginBottom: 8 }}>
                            <span style={{ color: colors.mutedForeground }}>Exclusions</span>
                            <span style={{ fontFamily: fonts.mono, fontSize: 10 }}>5</span>
                          </div>
                          <div style={{ display: "flex", justifyContent: "space-between", padding: "6px 0", borderTop: `2px solid ${colors.machine}` }}>
                            <span style={{ fontWeight: 700, fontSize: 13 }}>Total</span>
                            <span style={{ fontWeight: 700, fontSize: 15, color: colors.machine, fontFamily: fonts.mono }}>$8,254</span>
                          </div>
                          <div style={{ marginTop: 10, textAlign: "center" }}>
                            <div style={{
                              display: "inline-block", padding: "6px 20px",
                              backgroundColor: colors.machine, color: colors.foreground,
                              fontWeight: 600, fontSize: 12, borderRadius: radius.button,
                            }}>
                              Generate Quote PDF
                            </div>
                          </div>
                        </div>
                      )}
                    </>
                  )}
                </div>
              </>
            )}
          </div>
        )}
      </div>

      {/* ── Quote document overlay ────────────── */}
      {showDoc && (
        <div
          style={{
            position: "absolute", top: 0, left: 0, right: 0, bottom: 0,
            backgroundColor: `rgba(13, 14, 12, ${docOp * 0.7})`,
            display: "flex", alignItems: "center", justifyContent: "center",
          }}
        >
          <div
            style={{
              opacity: docOp, transform: `scale(${0.92 + docOp * 0.08})`,
              width: 560, backgroundColor: "#fff", borderRadius: radius.dialog,
              padding: "32px 28px", color: colors.foreground, maxHeight: 680,
              overflow: "hidden", boxShadow: "0 16px 48px rgba(0,0,0,0.3)",
            }}
          >
            <div style={{ textAlign: "center", marginBottom: 16 }}>
              <div style={{ fontSize: 15, fontWeight: 700, letterSpacing: 0.5 }}>JAKE TORRES ELECTRICAL LLC</div>
              <div style={{ fontSize: 9, color: colors.mutedForeground, marginTop: 2 }}>ROC #298451 | Licensed, Bonded, Insured | Phoenix, AZ</div>
              <div style={{ borderBottom: `2px solid ${colors.machine}`, marginTop: 10 }} />
            </div>
            <div style={{ textAlign: "center", fontWeight: 700, fontSize: 13, marginBottom: 14, letterSpacing: 1 }}>QUOTE</div>
            <div style={{ fontSize: 10.5, marginBottom: 14, lineHeight: 1.6 }}>
              <div><strong>Prepared for:</strong> Maria Gonzalez</div>
              <div><strong>Property:</strong> 1847 East Meadow Drive, Phoenix, AZ</div>
              <div><strong>Date:</strong> April 14, 2026 &bull; <strong>Valid:</strong> 30 days</div>
            </div>
            <div style={{ fontSize: 10.5, borderTop: `1px solid ${colors.border}` }}>
              {[["Panel Upgrade", "6 items", "$3,280"], ["Kitchen Circuits", "9 items", "$4,840"], ["Permit + Inspection", "2 items", "$134"]].map(([d, det, amt]) => (
                <div key={d} style={{ display: "flex", justifyContent: "space-between", padding: "4px 0", borderBottom: `1px solid ${colors.muted}` }}>
                  <span>{d}</span><span style={{ color: colors.mutedForeground, fontSize: 10 }}>{det}</span>
                  <span style={{ fontWeight: 600, fontFamily: fonts.mono, fontSize: 10 }}>{amt}</span>
                </div>
              ))}
              <div style={{ display: "flex", justifyContent: "space-between", padding: "6px 0", fontWeight: 700, fontSize: 13, borderTop: `2px solid ${colors.machine}`, marginTop: 2 }}>
                <span>PROJECT TOTAL</span><span style={{ color: colors.machine }}>$8,254</span>
              </div>
            </div>
            {frame >= DOC_START + F && (
              <><div style={{ marginTop: 10, fontSize: 9, fontWeight: 600, textTransform: "uppercase" as const, letterSpacing: 0.5, color: colors.machine, borderBottom: `1px solid ${colors.muted}`, paddingBottom: 2, marginBottom: 4 }}>Assumptions</div>
              <div style={{ fontSize: 9, color: colors.secondaryForeground, lineHeight: 1.5 }}>Existing service entrance in serviceable condition &bull; No aluminium wiring &bull; Cabinet locations marked before rough-in &bull; Normal working hours access</div></>
            )}
            {frame >= DOC_START + 2 * F && (
              <><div style={{ marginTop: 8, fontSize: 9, fontWeight: 600, textTransform: "uppercase" as const, letterSpacing: 0.5, color: colors.machine, borderBottom: `1px solid ${colors.muted}`, paddingBottom: 2, marginBottom: 4 }}>Exclusions</div>
              <div style={{ fontSize: 9, color: colors.secondaryForeground, lineHeight: 1.5 }}>LED fixtures (owner-supplied) &bull; Drywall/painting &bull; Work behind meter &bull; <strong>Asbestos abatement</strong> (priced as extra if found) &bull; Structural modifications</div></>
            )}
            {frame >= DOC_START + 3 * F && (
              <><div style={{ marginTop: 8, fontSize: 9, fontWeight: 600, textTransform: "uppercase" as const, letterSpacing: 0.5, color: colors.machine, borderBottom: `1px solid ${colors.muted}`, paddingBottom: 2, marginBottom: 4 }}>Additional Work</div>
              <div style={{ fontSize: 9, color: colors.secondaryForeground, lineHeight: 1.5 }}>Beyond this scope: <strong>$95/hr</strong> + materials at cost + 15%, with approval before work begins.</div></>
            )}
            {frame >= DOC_START + 4 * F && (
              <div style={{ marginTop: 12, textAlign: "center", fontSize: 9, color: colors.mutedForeground, borderTop: `1px solid ${colors.muted}`, paddingTop: 8 }}>
                Generated from 8-minute site conversation &bull; Based on rates from 15 completed jobs
              </div>
            )}
          </div>
        </div>
      )}
      </div>
    </AbsoluteFill>
  );
};
