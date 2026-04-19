# Data Model Delta — Project Lifecycle + Quoting Intelligence

**Status:** Pre-implementation artifact. Specifies only what's **new or changing** relative to the existing Kerf data model.
**Date:** 2026-04-19
**Scope:** Backend changes needed to support the lifecycle state machine, variations, disputes, revive, overlays, quote versioning, provenance tracking, email channel, magic links, methodology wiring, defect items. Plus indexes and validation queries.
**Non-scope:** Canonical work categories (built per `canonical-work-categories.md`), Methodology entity shape (speced in `methodology.md`), Domain 16 Work Structure, Domain 17 Quoting commercial intelligence (both added per prior handoffs).
**Depends on:** [project-lifecycle-flow.md](../design/project-lifecycle-flow.md) · [project-screen-ia-audit.md](../design/project-screen-ia-audit.md) · [methodology.md](../design/methodology.md)

---

## 0. How to read this

Each section below specifies:
- **Delta** — what's being added, changed, or extended.
- **Cypher** — schema additions (constraints, indexes, node/relationship shape).
- **Migration** — how to evolve existing data, if any exists.
- **Validation queries** — structural checks for CI.
- **Verification needed** — places where I can't confirm the current state from docs alone and a live inspection against `backend/graph/schema.cypher` + existing service code is required before building.

The doc is intentionally terse on prose — this is a schema reference, not a design argument.

---

## 1. Project state machine

### 1.1 Delta

`Project.state` already exists per prior handoff (values: `lead | quoted | active | completed | closed | lost`). Current enum doesn't match the state machine we've designed.

**New enum:** `LEAD | QUOTED | ACCEPTED | ACTIVE | PRACTICAL_COMPLETION | CLOSED`.

**New property:** `closed_reason` — enum `completed | terminated_convenience | terminated_cause | abandoned | lead_lost`. Non-null only when `state = CLOSED`.

**New property:** `state_at_closure` — the state the project was in immediately before closure. Non-null only when `state = CLOSED`. Captures pre-close context without needing separate terminal states.

**Existing `status` field** (per handoff: `normal | on_hold | delayed | suspended`) → **remove.** Replaced by the PAUSED overlay (see §6.1) which carries typed dimensions natively.

### 1.2 Cypher

```cypher
// Add properties (no destructive changes — run in migration)
CREATE CONSTRAINT constraint_project_state_valid IF NOT EXISTS
  FOR (p:Project) REQUIRE p.state IN ['LEAD','QUOTED','ACCEPTED','ACTIVE','PRACTICAL_COMPLETION','CLOSED'];

CREATE INDEX index_project_state IF NOT EXISTS
  FOR (p:Project) ON (p.state);

CREATE INDEX index_project_closed_reason IF NOT EXISTS
  FOR (p:Project) ON (p.closed_reason);
```

### 1.3 Migration

For existing Projects:

```cypher
MATCH (p:Project)
WITH p,
  CASE p.state
    WHEN 'lead' THEN 'LEAD'
    WHEN 'quoted' THEN 'QUOTED'
    WHEN 'active' THEN 'ACTIVE'
    WHEN 'completed' THEN 'PRACTICAL_COMPLETION'  // completed = PC in new model; close needs explicit user action
    WHEN 'closed' THEN 'CLOSED'
    WHEN 'lost' THEN 'CLOSED'
    ELSE 'LEAD'
  END AS new_state,
  CASE p.state
    WHEN 'closed' THEN 'completed'
    WHEN 'lost' THEN 'lead_lost'
    ELSE null
  END AS new_closed_reason
SET p.state = new_state,
    p.closed_reason = new_closed_reason,
    p.state_at_closure = CASE WHEN new_state = 'CLOSED' THEN 'PRACTICAL_COMPLETION' ELSE null END;

// Drop the old `status` property or move to PAUSED overlay
MATCH (p:Project) WHERE p.status IN ['on_hold','suspended']
CREATE (p)-[:PAUSED {
  pause_type: p.status,
  reason: 'migrated_from_legacy_status',
  paused_at: datetime(),
  paused_by: 'migration'
}]->(p);

MATCH (p:Project) SET p.status = null;
```

### 1.4 Verification needed

- Confirm `backend/graph/schema.cypher` current Project state enum values.
- Confirm whether `status` is actively written anywhere in services (if so, remove the writes in service code).
- Confirm no production data exists at a `status = delayed` — that concept doesn't map to anything in the new model; if present, needs a policy call.

---

## 2. ContractVersion entity

### 2.1 Delta

**New entity.** Immutable snapshot captured at `QUOTED → ACCEPTED` transition.

### 2.2 Cypher

```cypher
// (:ContractVersion)
// properties:
//   id           string  (cv_{hex})
//   version      int     (1 for original; subsequent rare — see §3 Variation preferred path)
//   project_id   string
//   sum_cents    int
//   doc_hash     string   (sha256 of accepted document)
//   parties      json     ({contractor, client, certifier?})
//   dates        json     ({planned_start, planned_pc, signed_at})
//   payment_terms json    ({deposit_pct, interim_pct, final_pct, net_days})
//   retention_pct float   (0.0 if none)
//   jurisdiction string   (country-region, e.g. 'us-az')
//   governing_law string
//   accepted_by  string   (user or contact id)
//   accepted_at  datetime
//   accepted_method enum  ('magic_link' | 'verbal_recorded' | 'wet_signature')

CREATE CONSTRAINT constraint_contractversion_id IF NOT EXISTS
  FOR (cv:ContractVersion) REQUIRE cv.id IS UNIQUE;

CREATE CONSTRAINT constraint_contractversion_id_exists IF NOT EXISTS
  FOR (cv:ContractVersion) REQUIRE cv.id IS NOT NULL;

CREATE INDEX index_contractversion_project IF NOT EXISTS
  FOR (cv:ContractVersion) ON (cv.project_id);

// Relationship
// (Project)-[:HAS_CONTRACT_VERSION]->(ContractVersion)
```

### 2.3 Migration

For existing Projects in `active`/`completed`/`closed` state that never had a formal ContractVersion:

```cypher
MATCH (p:Project) WHERE p.state IN ['ACTIVE','PRACTICAL_COMPLETION','CLOSED']
  AND NOT (p)-[:HAS_CONTRACT_VERSION]->(:ContractVersion)
CREATE (cv:ContractVersion {
  id: 'cv_' + apoc.create.uuid(),
  version: 1,
  project_id: p.id,
  sum_cents: p.contract_sum_cents,  // assuming current Project has this
  doc_hash: 'legacy_pre_migration',
  parties: p.parties,                // best-effort from existing data
  dates: {signed_at: p.accepted_at}, // if we have it
  retention_pct: coalesce(p.retention_pct, 0.0),
  jurisdiction: p.jurisdiction_code,
  accepted_at: coalesce(p.accepted_at, p.created_at),
  accepted_method: 'legacy_migrated'
})
CREATE (p)-[:HAS_CONTRACT_VERSION]->(cv);
```

### 2.4 Validation

```cypher
// Every non-LEAD, non-QUOTED project must have a ContractVersion
MATCH (p:Project) WHERE p.state IN ['ACCEPTED','ACTIVE','PRACTICAL_COMPLETION','CLOSED']
  AND NOT (p)-[:HAS_CONTRACT_VERSION]->(:ContractVersion)
  AND p.closed_reason <> 'lead_lost'
RETURN p.id AS violation, 'Post-acceptance project missing ContractVersion' AS reason;
```

### 2.5 Verification needed

- Current Project entity — does it carry `contract_sum_cents`, `retention_pct`, `accepted_at`? If under different names, update migration.
- Does an existing `Contract` entity exist? Prior estimating-intelligence doc mentioned it. If so, decide: rename to ContractVersion, or keep existing shape and add `version`/`doc_hash`/`state_at_closure` fields.

---

## 3. Variation entity

### 3.1 Delta

**New first-class entity** with its own lifecycle. Variations are numbered addenda attached to `ContractVersion v1` — amendment-in-place, not new ContractVersions. Matches research #3 §1.2 and Decision 6.

### 3.2 Cypher

```cypher
// (:Variation)
// properties:
//   id             string (var_{hex})
//   number         int    (sequential per contract, gap-free)
//   state          enum   ('Draft' | 'Issued' | 'Approved' | 'Rejected' | 'Superseded')
//   subject        string
//   sum_delta_cents int
//   time_delta_days float
//   issued_at      datetime
//   issued_by      string (user id)
//   approved_at    datetime
//   approved_by    string (client contact id or user id for self-approval edge cases)
//   approval_method enum  ('magic_link' | 'email_reply' | 'verbal_recorded' | 'wet_signature')
//   client_visible_at datetime  (when client first viewed)
//   rationale      string (optional)

CREATE CONSTRAINT constraint_variation_id IF NOT EXISTS
  FOR (v:Variation) REQUIRE v.id IS UNIQUE;

CREATE CONSTRAINT constraint_variation_state_valid IF NOT EXISTS
  FOR (v:Variation) REQUIRE v.state IN ['Draft','Issued','Approved','Rejected','Superseded'];

CREATE INDEX index_variation_state IF NOT EXISTS
  FOR (v:Variation) ON (v.state);

CREATE INDEX index_variation_contract IF NOT EXISTS
  FOR ()-[r:HAS_VARIATION]->() ON (r.number);

// Relationships
// (ContractVersion)-[:HAS_VARIATION]->(Variation)
// (Variation)-[:HAS_LINE_ITEM]->(WorkItem)     // zero or more — new or modified WorkItems
// (Variation)-[:SUPERSEDES]->(Variation)       // when revised (V1.1 supersedes V1)
// (Variation)-[:EVIDENCE_FROM]->(DailyLog|Photo|TimeEntry|Conversation)
```

### 3.3 Validation

```cypher
// Variation numbers must be gap-free per contract
MATCH (cv:ContractVersion)-[:HAS_VARIATION]->(v:Variation)
WITH cv, collect(v.number) AS numbers
WITH cv, numbers, [n IN range(1, size(numbers)) | n] AS expected
WHERE numbers <> expected
RETURN cv.id AS violation, numbers, expected, 'Gap or duplicate in variation sequence' AS reason;

// A Superseded variation must SUPERSEDES another variation with the same number
MATCH (v:Variation {state: 'Superseded'})
WHERE NOT (v)<-[:SUPERSEDES]-(:Variation)
RETURN v.id AS violation, 'Superseded variation has no successor' AS reason;

// Approved variations must have approved_at + approved_by
MATCH (v:Variation {state: 'Approved'})
WHERE v.approved_at IS NULL OR v.approved_by IS NULL
RETURN v.id AS violation, 'Approved variation missing approval metadata' AS reason;
```

### 3.4 Derived property

Effective contract sum is **never stored** — always computed:

```cypher
MATCH (p:Project {id: $pid})-[:HAS_CONTRACT_VERSION]->(cv:ContractVersion)
OPTIONAL MATCH (cv)-[:HAS_VARIATION]->(v:Variation {state: 'Approved'})
WITH cv, collect(v.sum_delta_cents) AS deltas
RETURN cv.sum_cents + reduce(acc = 0, d IN deltas | acc + d) AS effective_sum_cents;
```

### 3.5 Verification needed

- Handoff mentioned Variation may already exist as a concept. Confirm: is there already a `ChangeOrder` or `Variation` entity in the graph? If yes, what's its shape? This spec assumes green-field.

---

## 4. Dispute entity

### 4.1 Delta

**New first-class entity** with its own lifecycle. Per Decision 12. Multiple disputes per Project supported.

### 4.2 Cypher

```cypher
// (:Dispute)
// properties:
//   id                    string (disp_{hex})
//   state                 enum ('Raised' | 'Negotiating' | 'Adjudication' | 'Mediation' | 'Arbitration' | 'Resolved')
//   subject               string
//   raised_by             string (user or contact id)
//   raised_at             datetime
//   amount_in_dispute_cents int
//   resolution_outcome    enum ('settled' | 'withdrawn' | 'adjudicated' | 'abandoned' | null)
//   resolved_at           datetime
//   resolved_by           string
//   resolution_amount_cents int (nullable)

CREATE CONSTRAINT constraint_dispute_id IF NOT EXISTS
  FOR (d:Dispute) REQUIRE d.id IS UNIQUE;

CREATE CONSTRAINT constraint_dispute_state_valid IF NOT EXISTS
  FOR (d:Dispute) REQUIRE d.state IN ['Raised','Negotiating','Adjudication','Mediation','Arbitration','Resolved'];

CREATE INDEX index_dispute_state IF NOT EXISTS
  FOR (d:Dispute) ON (d.state);

// Relationships
// (Project)-[:DISPUTE_OVER]->(Dispute)
// (Dispute)-[:HAS_EVIDENCE]->(Document|Photo|Conversation|EmailMessage)
// (Dispute)-[:HAS_ADJUDICATOR]->(Contact)
// (Dispute)-[:RESOLVED_BY]->(Adjudication|Settlement|Withdrawal)   // optional typed sub-entities; may collapse into Dispute properties if not needed
```

### 4.3 Derived overlay

`DISPUTE_OPEN` overlay is **derived**, not stored:

```cypher
MATCH (p:Project {id: $pid})
OPTIONAL MATCH (p)-[:DISPUTE_OVER]->(d:Dispute) WHERE d.state <> 'Resolved'
RETURN count(d) > 0 AS dispute_open;
```

### 4.4 Validation

```cypher
// Resolved disputes must have resolution_outcome
MATCH (d:Dispute {state: 'Resolved'})
WHERE d.resolution_outcome IS NULL
RETURN d.id AS violation, 'Resolved dispute missing outcome' AS reason;
```

---

## 5. Revival event entity

### 5.1 Delta

**New entity** capturing state reversal (per Decision 11).

### 5.2 Cypher

```cypher
// (:Revival)
// properties:
//   id                     string (rev_{hex})
//   revived_at             datetime
//   revived_by             string (user id)
//   prior_closed_reason    enum   (matches Project.closed_reason values)
//   state_before_revival   string ('CLOSED')
//   state_after_revival    string (any active state)
//   note                   string (optional contractor-added)

CREATE CONSTRAINT constraint_revival_id IF NOT EXISTS
  FOR (r:Revival) REQUIRE r.id IS UNIQUE;

// Relationship
// (Project)-[:HAS_REVIVAL]->(Revival)
```

### 5.3 Validation

```cypher
// Every Revival must reference a Project that went through CLOSED
MATCH (p:Project)-[:HAS_REVIVAL]->(r:Revival)
WHERE r.state_before_revival <> 'CLOSED'
RETURN r.id AS violation, 'Revival state_before must be CLOSED' AS reason;
```

---

## 6. Overlay relationships

### 6.1 `PAUSED` overlay

Per Decision 9 — single overlay with typed dimensions.

```cypher
// (Project)-[:PAUSED]->(Project)
// relationship properties:
//   pause_type          enum ('on_hold' | 'suspended')
//   reason              string (typed from a controlled list + extensible)
//   paused_at           datetime
//   paused_by           string (user id)
//   expected_resume_at  date (optional)
//   cure_deadline       date (optional; when pause_type = 'suspended')
//   client_request_ref  string (optional — email/conversation evidence)
//   resumed_at          datetime (null while active)
//   resumed_by          string (null while active)

// Note: self-loop pattern — relationship on the Project to itself with overlay properties.
// Alternative: (Project)-[:PAUSED]->(:PauseRecord) for a cleaner history.
// LEAN: use a PauseRecord node for clean history + audit.
```

**Revised design** — clean audit:

```cypher
// (:PauseRecord)
// properties:
//   id                  string (pause_{hex})
//   pause_type          enum
//   reason              string
//   paused_at           datetime
//   paused_by           string
//   expected_resume_at  date
//   cure_deadline       date
//   client_request_ref  string
//   resumed_at          datetime (null while active)
//   resumed_by          string (null while active)

// (Project)-[:HAS_PAUSE]->(PauseRecord)
// The "is paused" overlay query:
MATCH (p:Project {id: $pid})-[:HAS_PAUSE]->(pr:PauseRecord)
WHERE pr.resumed_at IS NULL
RETURN pr;
```

### 6.2 `DLP_OPEN`

```cypher
// (:DefectsLiabilityPeriod)
// properties:
//   id               string (dlp_{hex})
//   source           enum ('contract_clause' | 'statutory')
//   dlp_start        date
//   dlp_duration_days int
//   dlp_end          date (derived but stored for index efficiency)
//   closed_at        datetime (null while active)

// (Project)-[:HAS_DLP]->(DefectsLiabilityPeriod)
```

### 6.3 `RETENTION_HELD`

```cypher
// (:RetentionHolding)
// properties:
//   id                   string (rh_{hex})
//   retention_pct        float
//   held_in_trust        bool
//   trust_account_ref    string
//   amount_cents         int
//   scheduled_releases   json [{trigger: 'PC', pct: 2.5}, ...]
//   released_at          datetime (null while held)

// (Project)-[:HAS_RETENTION]->(RetentionHolding)
```

### 6.4 Notes

- **Overlays are first-class entities**, not relationship properties. Enables clean history, audit, and re-activation.
- The term "overlay" in the IA audit refers to the **conceptual** overlay on Project state — implemented as linked entities that can independently carry typed metadata.

---

## 7. WorkItem extensions

### 7.1 Delta

Per Decision 13.

**New property:** `state` — enum `not_started | in_progress | complete | de_scoped`.

**Existing property:** `percent_complete` (0-100) already exists per Domain 16. Keep.

### 7.2 Cypher

```cypher
CREATE CONSTRAINT constraint_workitem_state_valid IF NOT EXISTS
  FOR (wi:WorkItem) REQUIRE wi.state IN ['not_started','in_progress','complete','de_scoped'];

CREATE INDEX index_workitem_state IF NOT EXISTS
  FOR (wi:WorkItem) ON (wi.state);
```

### 7.3 Migration

```cypher
MATCH (wi:WorkItem)
SET wi.state = CASE
  WHEN wi.percent_complete = 0 THEN 'not_started'
  WHEN wi.percent_complete = 100 THEN 'complete'
  ELSE 'in_progress'
END;
```

**Note:** migration is lossy — it doesn't distinguish between "deliberately complete" and "100% of hours logged but not marked done". This is acceptable for legacy data; going forward the state enum captures explicit marking.

### 7.4 Validation

```cypher
// A WorkItem with state 'de_scoped' must be referenced by an Approved Variation
MATCH (wi:WorkItem {state: 'de_scoped'})
WHERE NOT (:Variation {state: 'Approved'})-[:HAS_LINE_ITEM]->(wi)
RETURN wi.id AS violation, 'de_scoped WorkItem not backed by approved Variation' AS reason;
```

### 7.5 PC precondition query

```cypher
// For the PC transition: all in-scope WorkItems must be complete or de_scoped
MATCH (p:Project {id: $pid})-[:HAS_WORK_ITEM]->(wi:WorkItem)
WHERE wi.state NOT IN ['complete','de_scoped']
RETURN wi.id AS blocker, wi.state AS current_state;
// If this returns any rows, block the PC transition.
```

---

## 8. Quote versioning

### 8.1 Delta

**New.** Quotes are first-class versionable documents attached to the Project in LEAD/QUOTED states.

### 8.2 Cypher

```cypher
// (:Quote)
// properties:
//   id              string (quote_{hex})
//   version         int    (1, 2, 3... per project)
//   project_id      string
//   state           enum   ('Draft' | 'Sent' | 'Accepted' | 'Rejected' | 'Superseded' | 'Withdrawn')
//   total_cents     int
//   labour_cents    int
//   items_cents     int
//   margin_pct      float
//   valid_until     date
//   sent_at         datetime (null for Draft)
//   viewed_at       datetime (first view via magic link)
//   view_count      int
//   doc_hash        string (sha256 of rendered proposal at send time)
//   scope_snapshot  json   (frozen WorkItem list at send time)

CREATE CONSTRAINT constraint_quote_id IF NOT EXISTS
  FOR (q:Quote) REQUIRE q.id IS UNIQUE;

CREATE CONSTRAINT constraint_quote_state_valid IF NOT EXISTS
  FOR (q:Quote) REQUIRE q.state IN ['Draft','Sent','Accepted','Rejected','Superseded','Withdrawn'];

// Relationships
// (Project)-[:HAS_QUOTE]->(Quote)
// (Quote)-[:SUPERSEDES]->(Quote)    // when revised
// (Quote)-[:ACCEPTED_INTO]->(ContractVersion)  // on acceptance
```

### 8.3 Validation

```cypher
// A project in QUOTED must have at least one non-superseded Quote in state Sent
MATCH (p:Project {state: 'QUOTED'})
WHERE NOT EXISTS {
  MATCH (p)-[:HAS_QUOTE]->(q:Quote {state: 'Sent'})
}
RETURN p.id AS violation, 'QUOTED project has no active Sent quote' AS reason;

// A project in ACCEPTED must have a Quote that ACCEPTED_INTO its ContractVersion
MATCH (p:Project {state: 'ACCEPTED'})-[:HAS_CONTRACT_VERSION]->(cv:ContractVersion)
WHERE NOT EXISTS {
  MATCH (p)-[:HAS_QUOTE]->(q:Quote)-[:ACCEPTED_INTO]->(cv)
}
RETURN p.id AS violation, 'Accepted project missing quote-to-contract link' AS reason;
```

---

## 9. DefectItem entity

### 9.1 Delta

**New.** Used for PC punch lists and DLP defects.

### 9.2 Cypher

```cypher
// (:DefectItem)
// properties:
//   id                string (def_{hex})
//   category          enum  ('cosmetic' | 'functional' | 'safety')
//   description       string
//   location          string
//   raised_at         datetime
//   raised_by         string (user or contact id)
//   origin            enum  ('punch_list_at_pc' | 'dlp_defect')
//   responsible_party enum  ('contractor' | 'client_supplied' | 'disputed')
//   status            enum  ('open' | 'resolved' | 'dismissed')
//   resolved_at       datetime
//   resolved_by       string
//   resolution_method string
//   resolution_hours  float

CREATE CONSTRAINT constraint_defectitem_id IF NOT EXISTS
  FOR (d:DefectItem) REQUIRE d.id IS UNIQUE;

// Relationships
// (Project)-[:HAS_DEFECT]->(DefectItem)
// (DefectItem)-[:AFFECTS_WORK_ITEM]->(WorkItem)   // optional
// (DefectItem)-[:HAS_PHOTO]->(Photo)
// (DefectItem)-[:RESOLVED_BY_TIME_ENTRY]->(TimeEntry)
```

---

## 10. Source provenance on Labour and Item

### 10.1 Delta

**Extends existing Labour and Item nodes** (Domain 16).

New properties per Labour node:
- `productivity_source` — enum `catalog | history | insight | stated | default`
- `rate_source` — enum `catalog | history | insight | stated | default`
- `rate_source_id` — string (reference to ResourceRate, if sourced from history/catalog)
- `productivity_source_id` — string (reference to ProductivityRate)
- `applied_insight_ids` — list of strings (Insight node ids)
- `base_hours` — float (pre-adjustment)
- `applied_adjustments` — json (list of `{insight_id, multiplier, addition_hours}`)

New properties per Item node:
- `price_source` — enum `catalog | history | insight | stated | default`
- `price_source_id` — string (reference to MaterialCatalogEntry or PurchaseOrderLine)
- `applied_insight_ids` — list of strings (rare for items but possible)

### 10.2 Cypher

```cypher
CREATE INDEX index_labour_rate_source IF NOT EXISTS
  FOR (l:Labour) ON (l.rate_source);

CREATE INDEX index_labour_productivity_source IF NOT EXISTS
  FOR (l:Labour) ON (l.productivity_source);

CREATE INDEX index_item_price_source IF NOT EXISTS
  FOR (i:Item) ON (i.price_source);
```

### 10.3 Validation

```cypher
// Every Labour with source != 'default' must have a source_id
MATCH (l:Labour)
WHERE l.rate_source IN ['catalog','history'] AND l.rate_source_id IS NULL
RETURN l.id AS violation, 'Labour rate sourced from catalog/history without source_id' AS reason;

// Every Labour with 'stated' source should be flagged for insight capture
MATCH (l:Labour {rate_source: 'stated'})
WHERE NOT EXISTS {
  MATCH (l)-[:CAPTURE_CANDIDATE]->(:InsightCandidate)
}
// This is informational, not a block.
RETURN l.id AS candidate, 'Stated labour rate — consider capturing as insight' AS note;
```

### 10.4 Verification needed

- Domain 16/17 current Labour and Item schemas — which of these properties might already exist under different names? Particularly `rate_source_id` vs. existing references to ResourceRate.
- Current handoff mentioned `rate_source_id` and `contractor_stated` tag exist in create_labour. Confirm and align nomenclature.

---

## 11. Email tracking

### 11.1 Delta

**New.** Supports `§3.14 Email as a Client Channel`.

### 11.2 Cypher

```cypher
// (:EmailThread)
// properties:
//   id            string (thr_{hex})
//   project_id    string
//   subject       string
//   initiated_by  enum  ('contractor' | 'client')
//   provider      enum  ('gmail' | 'outlook' | 'imap_generic')
//   provider_thread_id string
//   started_at    datetime
//   last_activity_at datetime

// (:EmailMessage)
// properties:
//   id            string (em_{hex})
//   thread_id     string
//   direction     enum  ('outbound' | 'inbound')
//   state         enum  ('draft' | 'sent' | 'received' | 'read' | 'replied' | 'bounced')
//   from_address  string
//   to_addresses  list<string>
//   cc_addresses  list<string>
//   body_text     string
//   body_html     string (nullable)
//   sent_at       datetime
//   received_at   datetime
//   drafted_by_agent bool
//   approved_by   string (user id; null when auto-sent)

CREATE CONSTRAINT constraint_emailthread_id IF NOT EXISTS
  FOR (t:EmailThread) REQUIRE t.id IS UNIQUE;

CREATE CONSTRAINT constraint_emailmessage_id IF NOT EXISTS
  FOR (m:EmailMessage) REQUIRE m.id IS UNIQUE;

CREATE INDEX index_emailthread_project IF NOT EXISTS
  FOR (t:EmailThread) ON (t.project_id);

// Relationships
// (Project)-[:HAS_EMAIL_THREAD]->(EmailThread)
// (EmailThread)-[:CONTAINS_MESSAGE]->(EmailMessage)
// (EmailMessage)-[:REGARDS_QUOTE]->(Quote)
// (EmailMessage)-[:REGARDS_VARIATION]->(Variation)
// (EmailMessage)-[:REGARDS_INVOICE]->(Invoice)
// (EmailMessage)-[:TRIGGERED_ACTION]->(action node — Variation draft, Quote v2, state proposal)
```

### 11.3 Validation

```cypher
// Outbound messages must be approved_by unless explicitly marked auto
MATCH (m:EmailMessage {direction: 'outbound', state: 'sent'})
WHERE m.approved_by IS NULL
RETURN m.id AS violation, 'Outbound email sent without explicit approval' AS reason;
```

---

## 12. MagicLink entity

### 12.1 Delta

**New.** Client-facing access tokens for quote view, variation approval, PC acknowledgment, invoice view.

### 12.2 Cypher

```cypher
// (:MagicLink)
// properties:
//   id            string (ml_{hex})
//   token         string (cryptographic, ~32 bytes, UNIQUE)
//   project_id    string
//   scope         enum  ('view_quote' | 'accept_quote' | 'approve_variation' | 'acknowledge_pc' | 'view_invoice' | 'pay_invoice')
//   target_id     string (quote id, variation id, etc)
//   issued_at     datetime
//   expires_at    datetime
//   used_at       datetime (null until used)
//   used_by_action string (e.g. 'accepted', 'rejected' — what the user did)
//   first_viewed_at datetime
//   last_viewed_at  datetime
//   view_count    int
//   allowed_emails list<string> (optional — restrict to specific recipients)

CREATE CONSTRAINT constraint_magiclink_token IF NOT EXISTS
  FOR (ml:MagicLink) REQUIRE ml.token IS UNIQUE;

CREATE CONSTRAINT constraint_magiclink_id IF NOT EXISTS
  FOR (ml:MagicLink) REQUIRE ml.id IS UNIQUE;

// Relationships
// (Project)-[:HAS_MAGIC_LINK]->(MagicLink)
// (MagicLink)-[:GRANTS_ACTION_ON]->(Quote|Variation|PracticalCompletion|Invoice)
```

### 12.3 Rules

- Single-use for `accept_quote`, `approve_variation`, `acknowledge_pc` — after used, `used_at` set and the token is invalidated server-side.
- Multi-use for `view_quote`, `view_invoice`, `pay_invoice` — tracked via `view_count` + `last_viewed_at`.
- Expired tokens return 410 Gone. Client can request a new link.
- Scope is strictly checked server-side — a `view_quote` token cannot accept the quote.

---

## 13. Methodology wiring

### 13.1 Delta

Methodology entity shape is fully speced in `docs/design/methodology.md` and noted in the 2026-04-17 handoff as "schema ready, service pending." No further schema changes here — only confirming:

- `(Project)-[:USES_METHODOLOGY]->(Methodology {scope_level: 'project'})`
- `(WorkPackage)-[:USES_METHODOLOGY]->(Methodology {scope_level: 'package'})`
- `(WorkItem)-[:USES_METHODOLOGY]->(Methodology {scope_level: 'item'})`
- `(Methodology)-[:CHILD_OF]->(Methodology)` for cascade
- `(Methodology)-[:APPLIES_TO_CATEGORY]->(WorkCategory:Canonical)`
- `(Insight)-[:APPLIES_TO_METHODOLOGY_WITH {approach_match: {...}}]->(Methodology)`

**What's still needed (from handoff):**
- `backend/app/services/methodology_service.py` — methods: `create`, `get`, `resolve_cascade`, `update`, `supersede`, `list_for_project`
- `backend/app/routers/methodology.py` — REST surface
- `backend/app/services/mcp_tools.py` — MCP tools: `create_methodology`, `resolve_methodology`, `update_methodology_approach`, `retrieve_past_methodologies_for_category`

---

## 14. Indexes summary (CI-enforced)

All the indexes above, consolidated:

```cypher
CREATE INDEX index_project_state IF NOT EXISTS FOR (p:Project) ON (p.state);
CREATE INDEX index_project_closed_reason IF NOT EXISTS FOR (p:Project) ON (p.closed_reason);
CREATE INDEX index_contractversion_project IF NOT EXISTS FOR (cv:ContractVersion) ON (cv.project_id);
CREATE INDEX index_variation_state IF NOT EXISTS FOR (v:Variation) ON (v.state);
CREATE INDEX index_variation_contract IF NOT EXISTS FOR ()-[r:HAS_VARIATION]->() ON (r.number);
CREATE INDEX index_dispute_state IF NOT EXISTS FOR (d:Dispute) ON (d.state);
CREATE INDEX index_workitem_state IF NOT EXISTS FOR (wi:WorkItem) ON (wi.state);
CREATE INDEX index_labour_rate_source IF NOT EXISTS FOR (l:Labour) ON (l.rate_source);
CREATE INDEX index_labour_productivity_source IF NOT EXISTS FOR (l:Labour) ON (l.productivity_source);
CREATE INDEX index_item_price_source IF NOT EXISTS FOR (i:Item) ON (i.price_source);
CREATE INDEX index_emailthread_project IF NOT EXISTS FOR (t:EmailThread) ON (t.project_id);
```

---

## 15. Constraints summary (CI-enforced)

```cypher
// Project
CREATE CONSTRAINT constraint_project_state_valid IF NOT EXISTS FOR (p:Project) REQUIRE p.state IN ['LEAD','QUOTED','ACCEPTED','ACTIVE','PRACTICAL_COMPLETION','CLOSED'];

// ContractVersion
CREATE CONSTRAINT constraint_contractversion_id IF NOT EXISTS FOR (cv:ContractVersion) REQUIRE cv.id IS UNIQUE;
CREATE CONSTRAINT constraint_contractversion_id_exists IF NOT EXISTS FOR (cv:ContractVersion) REQUIRE cv.id IS NOT NULL;

// Variation
CREATE CONSTRAINT constraint_variation_id IF NOT EXISTS FOR (v:Variation) REQUIRE v.id IS UNIQUE;
CREATE CONSTRAINT constraint_variation_state_valid IF NOT EXISTS FOR (v:Variation) REQUIRE v.state IN ['Draft','Issued','Approved','Rejected','Superseded'];

// Dispute
CREATE CONSTRAINT constraint_dispute_id IF NOT EXISTS FOR (d:Dispute) REQUIRE d.id IS UNIQUE;
CREATE CONSTRAINT constraint_dispute_state_valid IF NOT EXISTS FOR (d:Dispute) REQUIRE d.state IN ['Raised','Negotiating','Adjudication','Mediation','Arbitration','Resolved'];

// Revival
CREATE CONSTRAINT constraint_revival_id IF NOT EXISTS FOR (r:Revival) REQUIRE r.id IS UNIQUE;

// WorkItem
CREATE CONSTRAINT constraint_workitem_state_valid IF NOT EXISTS FOR (wi:WorkItem) REQUIRE wi.state IN ['not_started','in_progress','complete','de_scoped'];

// Quote
CREATE CONSTRAINT constraint_quote_id IF NOT EXISTS FOR (q:Quote) REQUIRE q.id IS UNIQUE;
CREATE CONSTRAINT constraint_quote_state_valid IF NOT EXISTS FOR (q:Quote) REQUIRE q.state IN ['Draft','Sent','Accepted','Rejected','Superseded','Withdrawn'];

// DefectItem
CREATE CONSTRAINT constraint_defectitem_id IF NOT EXISTS FOR (d:DefectItem) REQUIRE d.id IS UNIQUE;

// EmailThread / EmailMessage
CREATE CONSTRAINT constraint_emailthread_id IF NOT EXISTS FOR (t:EmailThread) REQUIRE t.id IS UNIQUE;
CREATE CONSTRAINT constraint_emailmessage_id IF NOT EXISTS FOR (m:EmailMessage) REQUIRE m.id IS UNIQUE;

// MagicLink
CREATE CONSTRAINT constraint_magiclink_token IF NOT EXISTS FOR (ml:MagicLink) REQUIRE ml.token IS UNIQUE;
CREATE CONSTRAINT constraint_magiclink_id IF NOT EXISTS FOR (ml:MagicLink) REQUIRE ml.id IS UNIQUE;
```

Append all of these to `backend/graph/schema.cypher`.

---

## 16. Validation queries summary (CI-enforced)

Append to `backend/fixtures/golden/validation-tests.cypher`:

```cypher
// --- Project state machine ---

// Post-acceptance project must have a ContractVersion
MATCH (p:Project) WHERE p.state IN ['ACCEPTED','ACTIVE','PRACTICAL_COMPLETION','CLOSED']
  AND NOT (p)-[:HAS_CONTRACT_VERSION]->(:ContractVersion)
  AND p.closed_reason <> 'lead_lost'
RETURN p.id AS violation, 'Post-acceptance project missing ContractVersion' AS reason;

// CLOSED project must have closed_reason and state_at_closure
MATCH (p:Project {state: 'CLOSED'})
WHERE p.closed_reason IS NULL OR p.state_at_closure IS NULL
RETURN p.id AS violation, 'CLOSED project missing closed_reason or state_at_closure' AS reason;

// --- Variations ---

// Variation numbers must be gap-free per contract
MATCH (cv:ContractVersion)-[:HAS_VARIATION]->(v:Variation)
WITH cv, collect(v.number) AS numbers
WITH cv, numbers, [n IN range(1, size(numbers)) | n] AS expected
WHERE numbers <> expected
RETURN cv.id AS violation, 'Gap or duplicate in variation sequence' AS reason;

// Approved variations must have approved_at + approved_by
MATCH (v:Variation {state: 'Approved'})
WHERE v.approved_at IS NULL OR v.approved_by IS NULL
RETURN v.id AS violation, 'Approved variation missing approval metadata' AS reason;

// --- Disputes ---

// Resolved disputes must have resolution_outcome
MATCH (d:Dispute {state: 'Resolved'})
WHERE d.resolution_outcome IS NULL
RETURN d.id AS violation, 'Resolved dispute missing outcome' AS reason;

// --- WorkItems ---

// de_scoped WorkItems must be backed by an Approved Variation
MATCH (wi:WorkItem {state: 'de_scoped'})
WHERE NOT (:Variation {state: 'Approved'})-[:HAS_LINE_ITEM]->(wi)
RETURN wi.id AS violation, 'de_scoped WorkItem not backed by approved Variation' AS reason;

// --- Quotes ---

// QUOTED project has no active Sent quote
MATCH (p:Project {state: 'QUOTED'})
WHERE NOT EXISTS { MATCH (p)-[:HAS_QUOTE]->(:Quote {state: 'Sent'}) }
RETURN p.id AS violation, 'QUOTED project has no active Sent quote' AS reason;

// Accepted project missing quote-to-contract link
MATCH (p:Project {state: 'ACCEPTED'})-[:HAS_CONTRACT_VERSION]->(cv:ContractVersion)
WHERE NOT EXISTS {
  MATCH (p)-[:HAS_QUOTE]->(q:Quote)-[:ACCEPTED_INTO]->(cv)
}
RETURN p.id AS violation, 'Accepted project missing quote-to-contract link' AS reason;

// --- Provenance ---

// Labour with catalog/history source but no source_id
MATCH (l:Labour)
WHERE l.rate_source IN ['catalog','history'] AND l.rate_source_id IS NULL
RETURN l.id AS violation, 'Labour rate sourced from catalog/history without source_id' AS reason;

// --- Email ---

// Outbound sent message without approval
MATCH (m:EmailMessage {direction: 'outbound', state: 'sent'})
WHERE m.approved_by IS NULL
RETURN m.id AS violation, 'Outbound email sent without explicit approval' AS reason;
```

---

## 17. Migration runbook

Order of operations for the backend team:

1. **Schema additions.** Apply §14 (indexes) and §15 (constraints) to `backend/graph/schema.cypher`. Run against dev, staging, production sequentially.
2. **Data audit.** Inventory existing Projects by current `state`, count variations-as-change-orders, count quotes (if existing entity), count closed projects. Size the migration.
3. **Project state migration** (§1.3). Idempotent.
4. **Create ContractVersion for legacy active projects** (§2.3). Idempotent.
5. **WorkItem state migration** (§7.3). Idempotent.
6. **Legacy `status` → PauseRecord migration** (if any data exists; §1.3 second block).
7. **Validation-query pass.** Run §16. Any violations are pre-existing data integrity issues — triage individually.
8. **Service updates** (separate vertical slices — not this doc's scope).

---

## 18. What's NOT in this delta (explicitly)

- **Canonical work categories** (done, per `canonical-work-categories.md`).
- **Methodology node shape** (speced in `methodology.md`; only wiring is pending).
- **Domain 16 Work Structure base entities** (WorkItem, Labour, Item, WorkPackage — extended here, not redefined).
- **Domain 17 Quoting commercial entities** (Assumption, Exclusion, ResourceRate, ProductivityRate — referenced, not redefined).
- **Canvas rendering** (post-MVP).
- **Home screen cross-project surface** (its own design pass + data model delta).
- **Scheduling engine evolution** (separate scope).
- **Sub-compliance tracking enhancements** (exists per §3.11; may need extension but not in this cut).

---

## 19. Verifications required before build

Items to validate against the actual `backend/graph/schema.cypher` and service code before writing any new migration / code:

1. Current `Project.state` enum values — confirm `lead | quoted | active | completed | closed | lost`.
2. Current `Project.status` field usage — is it written anywhere? Any production data?
3. Existing `Contract` entity (mentioned in `estimating-intelligence.md`) — does it exist? Shape? Decide: rename to `ContractVersion` or keep as separate concept.
4. Existing `ChangeOrder` or `Variation` entity — confirm green-field.
5. Existing `Quote` entity — confirm green-field (estimating-intelligence flagged it as the entity with versioning).
6. Existing `Labour.rate_source` / `rate_source_id` fields — naming alignment.
7. Existing `Item.price_source` / `price_source_id` fields — naming alignment.
8. `ProductivityRate` and `ResourceRate` — their current properties and how they're referenced.
9. `Insight` node — shape, particularly `applies_when` and `approach_match` properties.
10. `MaterialCatalogEntry` — confirm existence, shape, and which property is "current price."

Each gets a 10-minute spelunk before building starts.

---

*End of delta. Moves next to `docs/implementation/vertical-slices.md`.*
