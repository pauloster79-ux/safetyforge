/**
 * Demo mode chat simulation — stateful conversation that behaves like real Claude.
 *
 * The inspection simulation maintains real checklist state and distinguishes:
 * - Questions ("what do you mean by open edges?") → answers without advancing
 * - Pass/fail answers ("looks good", "failed") → records result and advances
 * - Commands ("go back", "skip") → navigates the checklist
 * - Notes ("add a note: saw some rust") → appends to current/previous item
 */

import type { ChatRequest, ChatEvent } from './chat-stream';

const DELAY_MS = 35;

async function delay(ms: number): Promise<void> {
  return new Promise((r) => setTimeout(r, ms));
}

async function* yieldText(text: string): AsyncGenerator<ChatEvent> {
  const words = text.split(' ');
  for (let i = 0; i < words.length; i++) {
    const word = (i > 0 ? ' ' : '') + words[i];
    yield { type: 'text_delta', data: { text: word } };
    await delay(DELAY_MS);
  }
}

// ---------------------------------------------------------------------------
// General mode
// ---------------------------------------------------------------------------

const GENERAL_RESPONSES: Array<{ pattern: RegExp; response: string }> = [
  {
    pattern: /workers?.*expir|expir.*cert|cert.*expir/i,
    response:
      'I found 2 workers with expiring certifications:\n\n' +
      '- **Mike Rodriguez** — OSHA 30-Hour expires in 5 days (Project: Riverside Tower)\n' +
      '- **Sarah Chen** — First Aid/CPR expires in 12 days (Project: Downtown Complex)\n\n' +
      'Would you like me to check compliance for a specific project?',
  },
  {
    pattern: /fail.*inspect|inspect.*fail/i,
    response:
      'There were 3 failed inspections this week:\n\n' +
      '- **Daily Site** (Mon) — Riverside Tower: Fall protection guardrails not secured on level 5\n' +
      '- **Scaffold** (Tue) — Downtown Complex: Missing toe boards on east scaffold\n' +
      '- **Electrical** (Wed) — Riverside Tower: Exposed wiring in utility room B\n\n' +
      'All have open corrective actions. Want details on any of these?',
  },
  {
    pattern: /daily.*log|log.*status/i,
    response:
      'Daily log status for your projects:\n\n' +
      '- **Riverside Tower** — Today: Submitted | This week: 4/5\n' +
      '- **Downtown Complex** — Today: Missing | This week: 3/5\n' +
      '- **Harbor Bridge** — Today: Submitted | This week: 5/5\n\n' +
      "Downtown Complex is missing today's log. Want me to remind the foreman?",
  },
  {
    pattern: /safety.*summary|summary.*project|project.*summary/i,
    response:
      '**Riverside Tower — Safety Summary**\n\n' +
      '- Workers on site: 24\n' +
      '- Open hazards: 2 (1 high, 1 medium)\n' +
      '- Recent incidents: 1 near-miss (scaffolding)\n' +
      '- Last inspection: 6 hours ago (partial pass)\n' +
      '- Expiring certs: 1 worker (OSHA 30 in 5 days)\n\n' +
      'Overall: Needs attention — open high-severity hazard should be prioritised.',
  },
  {
    pattern: /morning.*brief|brief/i,
    response:
      '**Morning Safety Brief — Riverside Tower**\n\n' +
      'Alerts:\n' +
      '- 1 expired certification (Mike Rodriguez — OSHA 30)\n' +
      '- 2 unresolved hazard reports\n' +
      '- No inspection in the last 48 hours\n\n' +
      "Today's Focus:\n" +
      '- Concrete pour on level 3 — ensure fall protection\n' +
      '- Scaffold inspection due (east side)\n' +
      '- Toolbox talk: Heat stress prevention',
  },
];

async function* simulateGeneral(message: string): AsyncGenerator<ChatEvent> {
  const match = GENERAL_RESPONSES.find((r) => r.pattern.test(message));
  const response = match
    ? match.response
    : "I can help with that. Try asking about:\n\n" +
      '- Worker certifications ("which workers have expiring certs?")\n' +
      '- Failed inspections ("show me failed inspections this week")\n' +
      '- Daily log status ("daily log status for all projects")\n' +
      '- Project safety summaries ("safety summary for Riverside Tower")\n' +
      '- Morning safety briefs ("give me the morning brief")';

  yield { type: 'tool_call', data: { tool: 'query_graph' } };
  await delay(300);
  yield { type: 'tool_result', data: { tool: 'query_graph', result: { count: 3 } } };
  await delay(200);
  yield* yieldText(response);
}

// ---------------------------------------------------------------------------
// Inspection mode — stateful checklist conversation
// ---------------------------------------------------------------------------

const DEMO_CHECKLIST = [
  {
    item_id: 'ds_ppe_01',
    category: 'PPE Compliance',
    description: 'Hard hats worn by all workers in required areas',
    clarification: 'Hard hats are required in all active work zones — anywhere there\'s overhead work, crane operations, or risk of falling objects. Check the main structure area, the crane radius, and around any excavation edges.',
  },
  {
    item_id: 'ds_ppe_02',
    category: 'PPE Compliance',
    description: 'Safety glasses/goggles worn where required',
    clarification: 'Eye protection is required wherever there\'s risk of flying particles, dust, or chemical splash. Key areas: grinding stations, cutting operations, concrete work, and anywhere using power tools.',
  },
  {
    item_id: 'ds_fall_01',
    category: 'Fall Protection',
    description: 'Guardrails intact and secure at all open edges',
    clarification: 'Open edges means any unprotected side or edge of a floor, roof, ramp, or walkway where a worker could fall 6 feet or more. Check all floor openings, stairways without walls, roof perimeters, and any elevated platforms or scaffolding.',
  },
  {
    item_id: 'ds_fall_02',
    category: 'Fall Protection',
    description: 'Covers over floor openings secured and labeled',
    clarification: 'Floor openings include any hole in the floor, roof, or platform large enough for a person to fall through — elevator shafts, stairwell openings, pipe chases, and HVAC penetrations. Covers must be marked "HOLE" or "COVER" and secured so they can\'t be accidentally displaced.',
  },
  {
    item_id: 'ds_house_01',
    category: 'Housekeeping',
    description: 'Work areas clean and free of debris',
    clarification: 'Look for trip hazards — loose materials, tools left on walkways, scrap lumber with nails, tangled extension cords. Also check that materials are stored neatly and waste bins aren\'t overflowing. Good housekeeping is one of the top ways to prevent injuries on site.',
  },
];

// Persistent inspection state across messages
interface InspectionState {
  currentIndex: number;
  responses: Record<string, { status: string; notes: string }>;
  started: boolean;
}

let inspectionState: InspectionState = {
  currentIndex: 0,
  responses: {},
  started: false,
};

function resetInspectionState() {
  inspectionState = { currentIndex: 0, responses: {}, started: false };
}

function currentItem() {
  return DEMO_CHECKLIST[inspectionState.currentIndex] || null;
}

function emitProgress(completed = false): ChatEvent {
  return {
    type: 'inspection_progress',
    data: {
      current_index: inspectionState.currentIndex,
      total_items: DEMO_CHECKLIST.length,
      completed_count: Object.keys(inspectionState.responses).length,
      current_item: completed ? null : currentItem(),
      completed,
      responses: { ...inspectionState.responses },
    },
  };
}

// ---------------------------------------------------------------------------
// Message classification
// ---------------------------------------------------------------------------

type MessageIntent =
  | { type: 'start' }
  | { type: 'pass'; notes: string }
  | { type: 'fail'; notes: string }
  | { type: 'na' }
  | { type: 'skip' }
  | { type: 'go_back' }
  | { type: 'question' }
  | { type: 'add_note'; notes: string }
  | { type: 'unclear' };

function classifyMessage(message: string): MessageIntent {
  const m = message.toLowerCase().trim();

  // Start inspection
  if (/^start\b/i.test(m) && /inspection/i.test(m)) return { type: 'start' };

  // Commands
  if (/\b(go back|previous|back up|redo last|revisit)\b/i.test(m)) return { type: 'go_back' };
  if (/^(skip|next|move on|n\/a)\b/i.test(m)) return { type: 'na' };
  if (/\bskip\s*(this|it|that)?\s*(one|item)?\b/i.test(m)) return { type: 'na' };
  if (/\badd\s*a?\s*note\b/i.test(m)) {
    const noteText = m.replace(/.*add\s*a?\s*note:?\s*/i, '').trim();
    return { type: 'add_note', notes: noteText || message };
  }

  // Questions — contains a question mark or starts with question words
  if (/\?$/.test(m)) return { type: 'question' };
  if (/^(what|how|where|why|when|which|who|can you|could you|tell me|explain|clarify|what do you mean)/i.test(m)) {
    return { type: 'question' };
  }

  // Clear fail signals
  if (/\b(fail|failed|no good|not good|issue|problem|bad|missing|broken|damaged|unsafe|violation|noncompliant|non-compliant|not compliant|needs? (work|attention|fixing|repair))\b/i.test(m)) {
    const notes = message.trim();
    return { type: 'fail', notes };
  }

  // Clear pass signals
  if (/\b(pass|good|fine|ok|okay|yes|yep|yeah|all good|looks good|looks great|no issues?|all clear|compliant|in order|checked|confirmed|affirmative|thumbs up|solid|perfect|excellent)\b/i.test(m)) {
    const notes = m.length > 20 ? message.trim() : '';
    return { type: 'pass', notes };
  }

  // N/A signals
  if (/\b(not applicable|n\/a|doesn'?t apply|no work|not relevant|not in use)\b/i.test(m)) {
    return { type: 'na' };
  }

  // If it's short and doesn't match anything, treat as unclear
  return { type: 'unclear' };
}

// ---------------------------------------------------------------------------
// Response generation
// ---------------------------------------------------------------------------

async function* handleInspectionMessage(message: string): AsyncGenerator<ChatEvent> {
  const intent = classifyMessage(message);

  // --- Start ---
  if (intent.type === 'start' || !inspectionState.started) {
    inspectionState.started = true;
    inspectionState.currentIndex = 0;
    inspectionState.responses = {};
    const item = currentItem()!;
    yield* yieldText(
      `Alright, let's get this inspection going. ${DEMO_CHECKLIST.length} items on the checklist today. ` +
      `First up is ${item.category} — ${item.description}. How's it looking?`
    );
    yield emitProgress();
    return;
  }

  const item = currentItem();

  // --- Question about current item ---
  if (intent.type === 'question') {
    if (item) {
      yield* yieldText(
        `${item.clarification}\n\nSo for this item — ${item.description} — what's the status?`
      );
    } else {
      yield* yieldText("We've covered all the items. Would you like to go back to any, or shall I wrap up the inspection?");
    }
    // No progress change — stay on same item
    return;
  }

  // --- Go back ---
  if (intent.type === 'go_back') {
    if (inspectionState.currentIndex > 0) {
      inspectionState.currentIndex--;
      const prev = currentItem()!;
      const prevResp = inspectionState.responses[prev.item_id];
      const prevStatus = prevResp ? ` (currently marked as ${prevResp.status})` : '';
      yield* yieldText(
        `Going back to ${prev.category} — ${prev.description}${prevStatus}. What's the updated status?`
      );
      yield emitProgress();
    } else {
      yield* yieldText("We're already on the first item. What's the status for this one?");
    }
    return;
  }

  // --- Add note ---
  if (intent.type === 'add_note') {
    // Add to the most recently completed item
    const lastCompletedIdx = inspectionState.currentIndex - 1;
    if (lastCompletedIdx >= 0) {
      const lastItem = DEMO_CHECKLIST[lastCompletedIdx];
      const existing = inspectionState.responses[lastItem.item_id];
      if (existing) {
        existing.notes = existing.notes ? `${existing.notes}; ${intent.notes}` : intent.notes;
        yield* yieldText(
          `Added that note to ${lastItem.category}. Anything else, or shall we continue with the current item?`
        );
        yield emitProgress();
        return;
      }
    }
    yield* yieldText("I'm not sure which item to add the note to. Can you give me the pass or fail status for the current item first?");
    return;
  }

  // --- Pass / Fail / NA ---
  if (intent.type === 'pass' || intent.type === 'fail' || intent.type === 'na') {
    if (!item) {
      yield* yieldText("We've already covered all items. Want me to wrap up the inspection?");
      return;
    }

    const status = intent.type === 'na' ? 'na' : intent.type;
    const notes = intent.type === 'na' ? 'N/A' : ('notes' in intent ? intent.notes : '');

    // Record the response
    inspectionState.responses[item.item_id] = { status, notes };

    // Emit tool call for realism
    yield { type: 'tool_call', data: { tool: 'update_inspection_item' } };
    await delay(150);
    yield {
      type: 'tool_result',
      data: {
        tool: 'update_inspection_item',
        result: { updated: item.item_id, status, remaining: DEMO_CHECKLIST.length - Object.keys(inspectionState.responses).length },
      },
    };

    // Advance
    inspectionState.currentIndex++;
    const next = currentItem();

    if (next) {
      // Contextual acknowledgement
      const ack = status === 'pass'
        ? 'Good.'
        : status === 'fail'
          ? `Noted — I've flagged that.`
          : 'Marked as N/A.';

      yield* yieldText(
        `${ack} Next — ${next.category}: ${next.description}. How does it look?`
      );
      yield emitProgress();
    } else {
      // All done — summarise
      const passed = Object.values(inspectionState.responses).filter(r => r.status === 'pass').length;
      const failed = Object.values(inspectionState.responses).filter(r => r.status === 'fail').length;
      const na = Object.values(inspectionState.responses).filter(r => r.status === 'na').length;

      const failedItems = DEMO_CHECKLIST
        .filter(c => inspectionState.responses[c.item_id]?.status === 'fail')
        .map(c => `- ${c.category}: ${c.description} — ${inspectionState.responses[c.item_id].notes}`);

      let summary = `That's all ${DEMO_CHECKLIST.length} items. Results: ${passed} passed, ${failed} failed`;
      if (na > 0) summary += `, ${na} N/A`;
      summary += '.';

      if (failedItems.length > 0) {
        summary += `\n\nFailed items needing corrective action:\n${failedItems.join('\n')}`;
      }

      summary += "\n\nI've saved the inspection. Good work out there.";

      yield { type: 'tool_call', data: { tool: 'complete_inspection' } };
      await delay(200);
      yield {
        type: 'tool_result',
        data: {
          tool: 'complete_inspection',
          result: { saved: true, passed, failed, na },
        },
      };

      yield* yieldText(summary);
      yield emitProgress(true);
    }
    return;
  }

  // --- Unclear ---
  if (intent.type === 'unclear') {
    if (item) {
      yield* yieldText(
        `I didn't quite catch that. For ${item.category} — ${item.description} — would you say it's a pass, fail, or not applicable? You can also ask me what to look for.`
      );
    } else {
      yield* yieldText("I'm not sure what you mean. We've covered all items — want me to wrap up?");
    }
    return;
  }
}

// ---------------------------------------------------------------------------
// Main entry point
// ---------------------------------------------------------------------------

export async function* simulateDemoChat(request: ChatRequest): AsyncGenerator<ChatEvent> {
  await delay(300);

  if (request.mode === 'inspection') {
    yield* handleInspectionMessage(request.message);
  } else {
    resetInspectionState();
    yield* simulateGeneral(request.message);
  }

  yield { type: 'done', data: { session_id: request.session_id || 'demo_session' } };
}
