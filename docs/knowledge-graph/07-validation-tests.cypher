// ============================================================================
// Kerf Ontology — Validation Queries
// ============================================================================
// Run AFTER 06-sample-data.cypher
// Tests CQ coverage, structural integrity, and permission model
// ============================================================================


// ============================================================================
// CQ VALIDATION — Proving key questions are answerable
// ============================================================================

// CQ-001: Who is this client and what's our history?
MATCH (c:Company {id: "comp_jake01"})-[:OWNS_PROJECT]->(p:Project)-[:CLIENT_IS]->(contact:Contact)
RETURN contact.name, p.name, p.status, p.contract_value;
// Expected: Mrs Johnson, Kitchen remodel electrics, active, 240000

// CQ-023: What work remains on this job?
MATCH (p:Project {id: "proj_sarah01"})-[:HAS_WORK_PACKAGE]->(wp)-[:CONTAINS]->(wi:WorkItem)
WHERE wi.state IN ['draft', 'scheduled', 'in_progress', 'on_hold']
RETURN wi.description, wi.state, wi.status,
       wi.labour_hours * wi.labour_rate AS labour_cost;
// Expected: 3 work items, showing state and calculated cost

// CQ-024: How much of specific work is complete?
MATCH (wi:WorkItem {id: "wi_sarah01"})-[:HAS_TIME_ENTRY]->(te:TimeEntry)
WITH wi, sum(duration.between(te.clock_in, te.clock_out).hours - te.break_minutes / 60.0) AS actual_hours
RETURN wi.description, wi.labour_hours AS estimated_hours, actual_hours;
// Expected: receptacles work item with estimated vs actual hours

// CQ-028: Who was on site today?
MATCH (p:Project {id: "proj_sarah01"})-[:HAS_DAILY_LOG]->(dl:DailyLog {log_date: date("2026-04-21")})
MATCH (te:TimeEntry)-[:RECORDED_ON]->(dl)
MATCH (te)-[:LOGGED_BY]->(w:Worker)
RETURN w.name, te.clock_in, te.clock_out;
// Expected: Marco, 06:00 to 15:30

// CQ-036: Is this job on budget?
MATCH (p:Project {id: "proj_sarah01"})-[:HAS_WORK_PACKAGE]->(wp)-[:CONTAINS]->(wi:WorkItem)
OPTIONAL MATCH (wi)-[ui:USES_ITEM]->()
WITH wi, sum(ui.quantity * ui.unit_cost) AS item_costs
RETURN
  sum(wi.labour_hours * wi.labour_rate + coalesce(wi.materials_allowance, 0) + coalesce(item_costs, 0)) AS total_estimated;
// Expected: sum of all work item costs

// CQ-043: What deficiency items are open? (Would work once DeficiencyList data added)
// MATCH (p:Project)-[:HAS_DEFICIENCY_LIST]->(dl)-[:HAS_DEFICIENCY]->(di:DeficiencyItem)
// WHERE di.status <> 'closed'
// RETURN di.description, di.status;

// CQ-050: Did we make money? (Simplified — shows contract value vs estimated cost)
MATCH (p:Project {id: "proj_dave01"})
MATCH (p)-[:HAS_WORK_PACKAGE]->(wp)-[:CONTAINS]->(wi:WorkItem)
RETURN p.name, p.contract_value,
       sum(coalesce(wi.labour_hours * wi.labour_rate, 0) + coalesce(wi.materials_allowance, 0)) AS total_cost;
// Note: Dave's sub work items have null labour (lump sum subs) — cost comes from sub contracts

// CQ-054: Which subs perform best?
MATCH (c:Company)-[:GC_OVER]->(sub:Company)
OPTIONAL MATCH (sub)<-[:PERFORMED_BY]-(wi:WorkItem)
RETURN sub.name, count(wi) AS work_items_assigned;

// CQ-055: What regulations apply to this activity?
MATCH (a:Activity {id: "act_working_at_height"})-[:REGULATED_BY]->(reg:Regulation)
WHERE reg.valid_until > date()
RETURN reg.reference, reg.title, reg.source;
// Expected: WAH_2005

// CQ-056: What certs does a worker need?
MATCH (a:Activity {id: "act_working_at_height"})-[:REGULATED_BY]->(reg)-[:REQUIRES_CONTROL]->(cert:CertificationType)
RETURN cert.name, reg.reference;
// Expected: Working at Height Trained, WAH_2005

// CQ-070: What jurisdiction is this company in?
MATCH (c:Company {id: "comp_jake01"})-[:IN_JURISDICTION]->(j:Jurisdiction)
RETURN j.code, j.name, j.default_currency, j.measurement_system, j.languages;
// Expected: UK, GBP, metric, [en, pl, ro]


// ============================================================================
// STRUCTURAL VALIDATION — Data integrity checks
// ============================================================================

// Every Project must be owned by a Company
MATCH (p:Project)
WHERE NOT (p)<-[:OWNS_PROJECT]-(:Company)
RETURN p.id AS orphan_project, "Project not owned by any Company" AS violation;
// Expected: empty (no orphans)

// Every WorkItem must belong to a Project (directly or via WorkPackage)
MATCH (wi:WorkItem)
WHERE NOT (wi)<-[:HAS_WORK_ITEM]-(:Project)
  AND NOT (wi)<-[:CONTAINS]-(:WorkPackage)<-[:HAS_WORK_PACKAGE]-(:Project)
RETURN wi.id AS orphan_work_item, "WorkItem not linked to any Project" AS violation;
// Expected: empty

// No cross-tenant paths (companies should not reach each other's data)
MATCH (c1:Company)-[:OWNS_PROJECT]->(p1:Project)-[:HAS_WORK_ITEM|HAS_WORK_PACKAGE*1..2]->(wi:WorkItem)<-[:HAS_WORK_ITEM|CONTAINS*1..2]-(p2:Project)<-[:OWNS_PROJECT]-(c2:Company)
WHERE c1 <> c2
RETURN c1.name, c2.name, "Cross-tenant work item detected" AS violation;
// Expected: empty

// Every Inspection has a conductor
MATCH (i:Inspection)
WHERE NOT (i)-[:CONDUCTED_BY]->()
RETURN i.id AS inspection_without_conductor, "Inspection missing CONDUCTED_BY" AS violation;
// Expected: empty

// Every WorkItem has a required state
MATCH (wi:WorkItem)
WHERE wi.state IS NULL OR NOT wi.state IN ['draft', 'scheduled', 'in_progress', 'complete', 'invoiced', 'on_hold', 'cancelled']
RETURN wi.id, wi.state, "Invalid or missing WorkItem state" AS violation;
// Expected: empty

// Every Invoice has a direction
MATCH (inv:Invoice)
WHERE inv.direction IS NULL OR NOT inv.direction IN ['receivable', 'payable']
RETURN inv.id, "Invoice missing direction" AS violation;
// Expected: empty

// Regulations have valid temporal data
MATCH (r:Regulation)
WHERE r.valid_from IS NULL OR r.valid_until IS NULL
RETURN r.reference, "Regulation missing temporal validity" AS violation;
// Expected: empty


// ============================================================================
// PERMISSION MODEL VALIDATION
// ============================================================================

// Can Jake reach his own project?
MATCH (m:Member {id: "mem_jake01"})<-[:HAS_MEMBER]-(c:Company)-[:OWNS_PROJECT]->(p:Project)
RETURN m.name, m.access_role, p.name;
// Expected: Jake, owner, Kitchen remodel

// Can Jake reach Sarah's project? (Should return nothing)
MATCH (m:Member {id: "mem_jake01"})<-[:HAS_MEMBER]-(c:Company)-[:OWNS_PROJECT]->(p:Project {id: "proj_sarah01"})
RETURN p.name AS should_be_empty;
// Expected: empty (no cross-tenant access)

// Can Dave see ABC Electric's insurance? (Via GC_OVER relationship)
MATCH (dave_co:Company {id: "comp_dave01"})-[:GC_OVER]->(sub:Company)-[:HAS_INSURANCE]->(cert:InsuranceCertificate)
RETURN sub.name, cert.carrier, cert.expiration_date;
// Expected: ABC Electric, State Farm, 2027-01-01


// ============================================================================
// WORK MODEL VALIDATION — Two-layer spine
// ============================================================================

// Jake: flat structure (Project → WorkItem directly)
MATCH (p:Project {id: "proj_jake01"})-[:HAS_WORK_ITEM]->(wi:WorkItem)
RETURN p.name, count(wi) AS work_items, "flat (no work packages)" AS structure;
// Expected: 3 work items, flat

// Sarah: grouped structure (Project → WorkPackage → WorkItem)
MATCH (p:Project {id: "proj_sarah01"})-[:HAS_WORK_PACKAGE]->(wp:WorkPackage)-[:CONTAINS]->(wi:WorkItem)
RETURN p.name, wp.name, count(wi) AS items_in_package;
// Expected: Rough-In: 2 items, Trim: 1 item

// Dave: grouped with sub-performed items
MATCH (p:Project {id: "proj_dave01"})-[:HAS_WORK_PACKAGE]->(wp)-[:CONTAINS]->(wi:WorkItem)
OPTIONAL MATCH (wi)-[:PERFORMED_BY]->(sub:Company)
RETURN wp.name, wi.description, wi.state, sub.name AS performed_by;
// Expected: framing by own crew (null), electrical by ABC Electric, plumbing by Reliable Plumbing
