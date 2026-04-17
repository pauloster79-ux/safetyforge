// ============================================================================
// Kerf Sample Data — Three Contractor Scenarios
// ============================================================================
// Run AFTER 07-schema-creation.cypher
// Covers: Jake (solo electrician), Sarah (45-person sub), Dave (GC)
// ============================================================================


// ============================================================================
// SHARED: Jurisdictions & Regulatory
// ============================================================================

CREATE (uk:Jurisdiction {code: "UK", name: "United Kingdom", languages: ["en", "pl", "ro"], default_currency: "GBP", measurement_system: "metric", date_format: "DD/MM/YYYY"})
CREATE (us:Jurisdiction {code: "US", name: "United States", languages: ["en", "es"], default_currency: "USD", measurement_system: "imperial", date_format: "MM/DD/YYYY"})

CREATE (ga:Region {code: "US-GA", name: "Georgia", jurisdiction_code: "US"})
CREATE (az:Region {code: "US-AZ", name: "Arizona", jurisdiction_code: "US"})

CREATE (tt_electrical:TradeType {id: "trade_electrical", name: "Electrical"})
CREATE (tt_concrete:TradeType {id: "trade_concrete", name: "Concrete"})
CREATE (tt_plumbing:TradeType {id: "trade_plumbing", name: "Plumbing"})
CREATE (tt_framing:TradeType {id: "trade_framing", name: "Framing"})

CREATE (act_wah:Activity {id: "act_working_at_height", name: "Working at height"})
CREATE (act_elec:Activity {id: "act_electrical_work", name: "Electrical work"})

CREATE (reg_wah:Regulation {reference: "WAH_2005", title: "Work at Height Regulations 2005", jurisdiction_code: "UK", source: "UK HSE", valid_from: date("2005-04-06"), valid_until: date("9999-12-31")})
CREATE (reg_osha_elec:Regulation {reference: "29CFR1926.405", title: "Wiring methods, components, and equipment", jurisdiction_code: "US", source: "OSHA", valid_from: date("2014-01-01"), valid_until: date("9999-12-31")})

CREATE (cert_wah:CertificationType {id: "cert_wah_uk", name: "Working at Height Trained", jurisdiction_code: "UK"})
CREATE (cert_osha30:CertificationType {id: "cert_osha30", name: "OSHA 30-Hour Construction", jurisdiction_code: "US"})
CREATE (cert_elec_uk:CertificationType {id: "cert_18th_edition", name: "18th Edition Wiring Regulations", jurisdiction_code: "UK"})

CREATE (act_wah)-[:REGULATED_BY]->(reg_wah)
CREATE (reg_wah)-[:REQUIRES_CONTROL {when: "height > 2m"}]->(cert_wah)

CREATE (insp_type_scaffold:InspectionType {id: "insp_scaffold", name: "Scaffold Inspection"})
CREATE (reg_wah)-[:REQUIRES_INSPECTION {frequency: "weekly"}]->(insp_type_scaffold)

// Shared items catalogue
CREATE (item_socket:Item {id: "item_001", name: "13A twin switched socket outlet", default_unit: "each", category: null, created_at: datetime()})
CREATE (item_cable:Item {id: "item_002", name: "2.5mm twin and earth cable", default_unit: "m", category: null, created_at: datetime()})
CREATE (item_cu:Item {id: "item_003", name: "18-way consumer unit", default_unit: "each", category: null, created_at: datetime()})
CREATE (item_led_panel:Item {id: "item_004", name: "600x600 LED panel light", default_unit: "each", category: null, created_at: datetime()})
CREATE (item_receptacle:Item {id: "item_005", name: "Standard duplex receptacle", default_unit: "each", category: null, created_at: datetime()})
CREATE (item_romex:Item {id: "item_006", name: "12/2 NM-B cable", default_unit: "ft", category: null, created_at: datetime()})


// ============================================================================
// SCENARIO 1: Jake — Solo Electrician, UK
// ============================================================================

CREATE (jake_co:Company {id: "comp_jake01", name: "Jake Torres Electrical", type: "contractor", jurisdiction_code: "UK", default_currency: "GBP", measurement_system: "metric", default_language: "en", status: "active", created_at: datetime(), updated_at: datetime()})

CREATE (jake:Member {id: "mem_jake01", uid: "uid_jake01", email: "jake@jtelectrical.co.uk", name: "Jake Torres", access_role: "owner", preferred_language: "en", status: "active", created_at: datetime(), updated_at: datetime()})

CREATE (jake_worker:Worker {id: "wkr_jake01", name: "Jake Torres", email: "jake@jtelectrical.co.uk", status: "active", preferred_language: "en", created_at: datetime(), updated_at: datetime()})

CREATE (jake_cert:Certification {id: "cert_jake_18th", status: "active", issue_date: date("2024-03-15"), expiry_date: date("2029-03-15"), certificate_number: "18TH-2024-4421", issuing_body: "City & Guilds", created_at: datetime(), updated_at: datetime()})

CREATE (mrs_johnson:Contact {id: "cont_johnson01", name: "Mrs Johnson", email: "sarah.johnson@gmail.com", phone: "+44 7700 900123", company_name: null, role_description: "client", created_at: datetime(), updated_at: datetime()})

// Jake's project — kitchen remodel
CREATE (jake_proj:Project {id: "proj_jake01", name: "Kitchen remodel electrics - Johnson", description: "Full rewire of kitchen, new consumer unit, 12 circuits", status: "active", type: "residential", pricing_model: "fixed_price", address: "14 Elm Street, Bristol BS1 4QT", jurisdiction_code: null, currency: null, planned_start: date("2026-04-14"), planned_end: date("2026-04-16"), contract_value: 240000, margin_pct: 35.0, quoted_at: datetime("2026-04-10T09:00:00"), won_at: datetime("2026-04-10T14:00:00"), created_at: datetime(), updated_at: datetime(), created_by: "mem_jake01", created_by_type: "human", updated_by: "mem_jake01", updated_by_type: "human"})

// Jake's work items — simple, flat, no work packages
CREATE (wi_jake_cu:WorkItem {id: "wi_jake01", description: "Supply and install 18-way consumer unit", state: "in_progress", status: null, labour_hours: 4.0, labour_rate: 5000, materials_allowance: 0, planned_start: date("2026-04-14"), planned_end: date("2026-04-14"), actual_start: date("2026-04-14"), notes: null, created_at: datetime(), updated_at: datetime(), created_by: "mem_jake01", created_by_type: "human", updated_by: "mem_jake01", updated_by_type: "human"})

CREATE (wi_jake_circuits:WorkItem {id: "wi_jake02", description: "First fix - run cables for 12 circuits", state: "draft", status: null, labour_hours: 8.0, labour_rate: 5000, materials_allowance: 5000, planned_start: date("2026-04-14"), planned_end: date("2026-04-15"), notes: null, created_at: datetime(), updated_at: datetime(), created_by: "mem_jake01", created_by_type: "human", updated_by: "mem_jake01", updated_by_type: "human"})

CREATE (wi_jake_second:WorkItem {id: "wi_jake03", description: "Second fix - fit sockets, switches, lights", state: "draft", status: null, labour_hours: 4.0, labour_rate: 5000, materials_allowance: 3000, planned_start: date("2026-04-16"), planned_end: date("2026-04-16"), notes: null, created_at: datetime(), updated_at: datetime(), created_by: "mem_jake01", created_by_type: "human", updated_by: "mem_jake01", updated_by_type: "human"})

// Relationships
CREATE (jake_co)-[:HAS_MEMBER]->(jake)
CREATE (jake_co)-[:EMPLOYS]->(jake_worker)
CREATE (jake_co)-[:OWNS_PROJECT]->(jake_proj)
CREATE (jake_co)-[:HAS_CONTACT]->(mrs_johnson)
CREATE (jake_co)-[:IN_JURISDICTION]->(uk)
CREATE (jake_proj)-[:CLIENT_IS]->(mrs_johnson)
CREATE (jake_proj)-[:HAS_WORK_ITEM]->(wi_jake_cu)
CREATE (jake_proj)-[:HAS_WORK_ITEM]->(wi_jake_circuits)
CREATE (jake_proj)-[:HAS_WORK_ITEM]->(wi_jake_second)
CREATE (wi_jake_cu)-[:ASSIGNED_TO_WORKER]->(jake_worker)
CREATE (wi_jake_circuits)-[:ASSIGNED_TO_WORKER]->(jake_worker)
CREATE (wi_jake_second)-[:ASSIGNED_TO_WORKER]->(jake_worker)
CREATE (jake_worker)-[:HOLDS_CERT]->(jake_cert)
CREATE (jake_cert)-[:OF_TYPE]->(cert_elec_uk)
CREATE (jake_worker)-[:HAS_TRADE]->(tt_electrical)
CREATE (jake_worker)-[:ASSIGNED_TO_PROJECT {role: "electrician", start_date: date("2026-04-14")}]->(jake_proj)

// Items on work items
CREATE (wi_jake_cu)-[:USES_ITEM {quantity: 1, unit: "each", unit_cost: 18500, actual_cost: null}]->(item_cu)
CREATE (wi_jake_circuits)-[:USES_ITEM {quantity: 120, unit: "m", unit_cost: 85, actual_cost: null}]->(item_cable)
CREATE (wi_jake_second)-[:USES_ITEM {quantity: 14, unit: "each", unit_cost: 350, actual_cost: null}]->(item_socket)


// ============================================================================
// SCENARIO 2: Sarah — 45-Person Electrical Contractor, US
// ============================================================================

CREATE (sarah_co:Company {id: "comp_sarah01", name: "Chen Electrical Inc", type: "contractor", jurisdiction_code: "US", default_currency: "USD", measurement_system: "imperial", default_language: "en", additional_languages: ["es"], status: "active", created_at: datetime(), updated_at: datetime()})

CREATE (sarah:Member {id: "mem_sarah01", uid: "uid_sarah01", email: "sarah@chenelectrical.com", name: "Sarah Chen", access_role: "owner", status: "active", created_at: datetime(), updated_at: datetime()})

CREATE (peterson:Contact {id: "cont_peterson01", name: "Tom Peterson", email: "tom@petersonbuilders.com", phone: "+1 404 555 0123", company_name: "Peterson Builders", role_description: "GC project manager", created_at: datetime(), updated_at: datetime()})

// Sarah's project — medical office fit-out
CREATE (sarah_proj:Project {id: "proj_sarah01", name: "4th Street Medical Office - Electrical", description: "Complete electrical fit-out, two floors, 4000 sq ft", status: "active", type: "commercial", pricing_model: "fixed_price", address: "412 4th Street NE, Atlanta, GA 30308", jurisdiction_code: "US", currency: "USD", planned_start: date("2026-04-21"), planned_end: date("2026-06-13"), contract_value: 14820000, margin_pct: 14.2, quoted_at: datetime("2026-04-08T16:00:00"), won_at: datetime("2026-04-11T10:00:00"), created_at: datetime(), updated_at: datetime(), created_by: "mem_sarah01", created_by_type: "human", updated_by: "mem_sarah01", updated_by_type: "human"})

// Work packages
CREATE (wp_roughin:WorkPackage {id: "wp_sarah01", name: "Electrical Rough-In", description: "First fix wiring, conduit, boxes", sort_order: 1, status: "active", created_at: datetime(), updated_at: datetime(), created_by: "mem_sarah01", created_by_type: "human", updated_by: "mem_sarah01", updated_by_type: "human"})

CREATE (wp_trim:WorkPackage {id: "wp_sarah02", name: "Electrical Trim", description: "Device installation, panel terminations", sort_order: 2, status: "active", created_at: datetime(), updated_at: datetime(), created_by: "mem_sarah01", created_by_type: "human", updated_by: "mem_sarah01", updated_by_type: "human"})

// Work items in rough-in package
CREATE (wi_sarah_recep:WorkItem {id: "wi_sarah01", description: "Standard duplex receptacles - all areas", state: "in_progress", status: null, labour_hours: 29.4, labour_rate: 8500, materials_allowance: 0, planned_start: date("2026-04-21"), planned_end: date("2026-05-02"), actual_start: date("2026-04-21"), created_at: datetime(), updated_at: datetime(), created_by: "mem_sarah01", created_by_type: "human", updated_by: "mem_sarah01", updated_by_type: "human"})

CREATE (wi_sarah_lights:WorkItem {id: "wi_sarah02", description: "LED panel lights - all areas", state: "draft", status: null, labour_hours: 16.0, labour_rate: 8500, materials_allowance: 0, planned_start: date("2026-05-05"), planned_end: date("2026-05-09"), created_at: datetime(), updated_at: datetime(), created_by: "mem_sarah01", created_by_type: "human", updated_by: "mem_sarah01", updated_by_type: "human"})

CREATE (wi_sarah_panels:WorkItem {id: "wi_sarah03", description: "Panel installation and terminations", state: "draft", status: null, labour_hours: 12.0, labour_rate: 9500, materials_allowance: 50000, planned_start: date("2026-05-26"), planned_end: date("2026-05-30"), created_at: datetime(), updated_at: datetime(), created_by: "mem_sarah01", created_by_type: "human", updated_by: "mem_sarah01", updated_by_type: "human"})

// Workers and crew
CREATE (marco:Worker {id: "wkr_marco01", name: "Marco Gutierrez", status: "active", preferred_language: "es", created_at: datetime(), updated_at: datetime()})
CREATE (carlos:Worker {id: "wkr_carlos01", name: "Carlos Mendoza", status: "active", preferred_language: "es", created_at: datetime(), updated_at: datetime()})

CREATE (marco_cert:Certification {id: "cert_marco_osha", status: "active", issue_date: date("2023-06-01"), expiry_date: date("2028-06-01"), certificate_number: "OSHA30-2023-8842", issuing_body: "OSHA Training Institute", created_at: datetime(), updated_at: datetime()})

CREATE (crew_a:Crew {id: "crew_sarah01", name: "Marco's Crew", status: "active", created_at: datetime(), updated_at: datetime()})

// Relationships
CREATE (sarah_co)-[:HAS_MEMBER]->(sarah)
CREATE (sarah_co)-[:EMPLOYS]->(marco)
CREATE (sarah_co)-[:EMPLOYS]->(carlos)
CREATE (sarah_co)-[:OWNS_PROJECT]->(sarah_proj)
CREATE (sarah_co)-[:HAS_CONTACT]->(peterson)
CREATE (sarah_co)-[:IN_JURISDICTION]->(us)
CREATE (sarah_co)-[:IN_REGION]->(ga)
CREATE (sarah_proj)-[:CLIENT_IS]->(peterson)
CREATE (sarah_proj)-[:CLIENT_COMPANY]->(sarah_co) // Peterson is the GC; Sarah is sub
CREATE (sarah_proj)-[:HAS_WORK_PACKAGE]->(wp_roughin)
CREATE (sarah_proj)-[:HAS_WORK_PACKAGE]->(wp_trim)
CREATE (wp_roughin)-[:CONTAINS]->(wi_sarah_recep)
CREATE (wp_roughin)-[:CONTAINS]->(wi_sarah_lights)
CREATE (wp_trim)-[:CONTAINS]->(wi_sarah_panels)
CREATE (wi_sarah_recep)-[:ASSIGNED_TO_CREW]->(crew_a)
CREATE (wi_sarah_lights)-[:ASSIGNED_TO_CREW]->(crew_a)
CREATE (marco)-[:MEMBER_OF]->(crew_a)
CREATE (carlos)-[:MEMBER_OF]->(crew_a)
CREATE (crew_a)-[:LED_BY]->(marco)
CREATE (marco)-[:HOLDS_CERT]->(marco_cert)
CREATE (marco_cert)-[:OF_TYPE]->(cert_osha30)
CREATE (marco)-[:HAS_TRADE]->(tt_electrical)
CREATE (carlos)-[:HAS_TRADE]->(tt_electrical)
CREATE (marco)-[:ASSIGNED_TO_PROJECT {role: "foreman", start_date: date("2026-04-21")}]->(sarah_proj)
CREATE (carlos)-[:ASSIGNED_TO_PROJECT {role: "electrician", start_date: date("2026-04-21")}]->(sarah_proj)

// Items
CREATE (wi_sarah_recep)-[:USES_ITEM {quantity: 84, unit: "each", unit_cost: 235, actual_cost: null}]->(item_receptacle)
CREATE (wi_sarah_recep)-[:USES_ITEM {quantity: 2500, unit: "ft", unit_cost: 45, actual_cost: null}]->(item_romex)
CREATE (wi_sarah_lights)-[:USES_ITEM {quantity: 48, unit: "each", unit_cost: 4200, actual_cost: null}]->(item_led_panel)

// Time entries
CREATE (te_marco_day1:TimeEntry {id: "te_marco01", clock_in: datetime("2026-04-21T06:00:00"), clock_out: datetime("2026-04-21T15:30:00"), break_minutes: 30, source: "worker_self", status: "approved", clock_in_latitude: 33.7756, clock_in_longitude: -84.3820, created_at: datetime(), updated_at: datetime(), created_by: "wkr_marco01", created_by_type: "human", updated_by: "mem_sarah01", updated_by_type: "human"})

CREATE (wi_sarah_recep)-[:HAS_TIME_ENTRY]->(te_marco_day1)
CREATE (te_marco_day1)-[:LOGGED_BY]->(marco)
CREATE (te_marco_day1)-[:FOR_PROJECT]->(sarah_proj)

// Contract
CREATE (sarah_contract:Contract {id: "ctr_sarah01", status: "active", value: 14820000, currency: "USD", retention_pct: 10.0, payment_terms: "net 30", payment_schedule: "monthly progress", scope_description: "Complete electrical fit-out per plans dated 2026-03-15", start_date: date("2026-04-21"), end_date: date("2026-06-13"), created_at: datetime(), updated_at: datetime(), created_by: "mem_sarah01", created_by_type: "human", updated_by: "mem_sarah01", updated_by_type: "human"})

CREATE (sarah_proj)-[:HAS_CONTRACT]->(sarah_contract)

// Safety inspection
CREATE (insp_sarah01:Inspection {id: "insp_sarah01", category: "safety", inspection_date: date("2026-04-21"), overall_status: "pass", score: 92.0, notes: "Minor debris in corridor, corrective action issued", created_at: datetime(), updated_at: datetime(), created_by: "wkr_marco01", created_by_type: "human", updated_by: "wkr_marco01", updated_by_type: "human"})

CREATE (sarah_proj)-[:HAS_INSPECTION]->(insp_sarah01)
CREATE (insp_sarah01)-[:CONDUCTED_BY]->(marco)

// Daily log
CREATE (dlog_sarah01:DailyLog {id: "dlog_sarah01", log_date: date("2026-04-21"), status: "submitted", weather_summary: "Clear, 72F", crew_count_own: 6, work_performed: "Started rough-in on ground floor. Ran home runs from panel location. Installed boxes for reception area receptacles.", submitted_at: datetime("2026-04-21T16:30:00"), submitted_by: "wkr_marco01", created_at: datetime(), updated_at: datetime(), created_by: "wkr_marco01", created_by_type: "human", updated_by: "wkr_marco01", updated_by_type: "human"})

CREATE (sarah_proj)-[:HAS_DAILY_LOG]->(dlog_sarah01)
CREATE (te_marco_day1)-[:RECORDED_ON]->(dlog_sarah01)
CREATE (insp_sarah01)-[:RECORDED_ON]->(dlog_sarah01)


// ============================================================================
// SCENARIO 3: Dave — GC Building a House, US
// ============================================================================

CREATE (dave_co:Company {id: "comp_dave01", name: "Morrison Construction LLC", type: "gc", jurisdiction_code: "US", default_currency: "USD", measurement_system: "imperial", default_language: "en", status: "active", created_at: datetime(), updated_at: datetime()})

CREATE (dave:Member {id: "mem_dave01", uid: "uid_dave01", email: "dave@morrisonconstruction.com", name: "Dave Morrison", access_role: "owner", status: "active", created_at: datetime(), updated_at: datetime()})

CREATE (homeowner:Contact {id: "cont_williams01", name: "James Williams", email: "james.williams@email.com", phone: "+1 602 555 0456", role_description: "client", created_at: datetime(), updated_at: datetime()})

// Sub companies
CREATE (abc_electric:Company {id: "comp_abc01", name: "ABC Electric", type: "sub", jurisdiction_code: "US", default_currency: "USD", measurement_system: "imperial", default_language: "en", status: "active", created_at: datetime(), updated_at: datetime()})

CREATE (reliable_plumb:Company {id: "comp_rel01", name: "Reliable Plumbing", type: "sub", jurisdiction_code: "US", default_currency: "USD", measurement_system: "imperial", default_language: "en", status: "active", created_at: datetime(), updated_at: datetime()})

// Dave's project — custom home
CREATE (dave_proj:Project {id: "proj_dave01", name: "Williams Custom Home", description: "4-bed custom home, 3200 sq ft", status: "active", type: "residential", pricing_model: "fixed_price", address: "Lot 14, Desert Ridge, Scottsdale, AZ 85255", jurisdiction_code: "US", currency: "USD", planned_start: date("2026-03-01"), planned_end: date("2026-10-31"), contract_value: 65000000, margin_pct: 18.0, quoted_at: datetime("2026-01-15T10:00:00"), won_at: datetime("2026-02-01T09:00:00"), created_at: datetime(), updated_at: datetime(), created_by: "mem_dave01", created_by_type: "human", updated_by: "mem_dave01", updated_by_type: "human"})

// Work packages by trade
CREATE (wp_framing:WorkPackage {id: "wp_dave01", name: "Framing", sort_order: 1, status: "active", created_at: datetime(), updated_at: datetime(), created_by: "mem_dave01", created_by_type: "human", updated_by: "mem_dave01", updated_by_type: "human"})

CREATE (wp_electrical:WorkPackage {id: "wp_dave02", name: "Electrical", sort_order: 2, status: "active", created_at: datetime(), updated_at: datetime(), created_by: "mem_dave01", created_by_type: "human", updated_by: "mem_dave01", updated_by_type: "human"})

CREATE (wp_plumbing:WorkPackage {id: "wp_dave03", name: "Plumbing", sort_order: 3, status: "active", created_at: datetime(), updated_at: datetime(), created_by: "mem_dave01", created_by_type: "human", updated_by: "mem_dave01", updated_by_type: "human"})

// Work items — mix of own crew and sub-performed
CREATE (wi_dave_frame:WorkItem {id: "wi_dave01", description: "Frame entire structure", state: "complete", status: null, labour_hours: 320.0, labour_rate: 4500, materials_allowance: 2800000, actual_start: date("2026-03-15"), actual_end: date("2026-04-12"), created_at: datetime(), updated_at: datetime(), created_by: "mem_dave01", created_by_type: "human", updated_by: "mem_dave01", updated_by_type: "human"})

CREATE (wi_dave_elec:WorkItem {id: "wi_dave02", description: "Complete electrical fit-out", state: "in_progress", status: null, labour_hours: null, labour_rate: null, materials_allowance: 0, planned_start: date("2026-04-14"), planned_end: date("2026-05-16"), actual_start: date("2026-04-14"), created_at: datetime(), updated_at: datetime(), created_by: "mem_dave01", created_by_type: "human", updated_by: "mem_dave01", updated_by_type: "human"})

CREATE (wi_dave_plumb:WorkItem {id: "wi_dave03", description: "Complete plumbing rough-in and finish", state: "in_progress", status: "Waiting on fixtures selection", labour_hours: null, labour_rate: null, materials_allowance: 0, planned_start: date("2026-04-14"), planned_end: date("2026-05-23"), actual_start: date("2026-04-14"), created_at: datetime(), updated_at: datetime(), created_by: "mem_dave01", created_by_type: "human", updated_by: "mem_dave01", updated_by_type: "human"})

// Relationships
CREATE (dave_co)-[:HAS_MEMBER]->(dave)
CREATE (dave_co)-[:OWNS_PROJECT]->(dave_proj)
CREATE (dave_co)-[:HAS_CONTACT]->(homeowner)
CREATE (dave_co)-[:IN_JURISDICTION]->(us)
CREATE (dave_co)-[:IN_REGION]->(az)
CREATE (dave_proj)-[:CLIENT_IS]->(homeowner)
CREATE (dave_proj)-[:HAS_WORK_PACKAGE]->(wp_framing)
CREATE (dave_proj)-[:HAS_WORK_PACKAGE]->(wp_electrical)
CREATE (dave_proj)-[:HAS_WORK_PACKAGE]->(wp_plumbing)
CREATE (wp_framing)-[:CONTAINS]->(wi_dave_frame)
CREATE (wp_electrical)-[:CONTAINS]->(wi_dave_elec)
CREATE (wp_plumbing)-[:CONTAINS]->(wi_dave_plumb)

// Sub-performed work items
CREATE (wi_dave_elec)-[:PERFORMED_BY]->(abc_electric)
CREATE (wi_dave_plumb)-[:PERFORMED_BY]->(reliable_plumb)

// Sub contracts
CREATE (ctr_abc:Contract {id: "ctr_abc01", status: "active", value: 5200000, currency: "USD", retention_pct: 10.0, payment_terms: "net 30", payment_schedule: "monthly progress", scope_description: "Complete electrical per plans", start_date: date("2026-04-14"), end_date: date("2026-05-16"), created_at: datetime(), updated_at: datetime(), created_by: "mem_dave01", created_by_type: "human", updated_by: "mem_dave01", updated_by_type: "human"})
CREATE (wi_dave_elec)-[:HAS_CONTRACT]->(ctr_abc)

// GC relationship
CREATE (gc_rel:GcRelationship {id: "gcrel_dave_abc", status: "active", created_at: datetime(), updated_at: datetime()})
CREATE (dave_co)-[:GC_OVER]->(abc_electric)

// Insurance cert for sub
CREATE (abc_insurance:InsuranceCertificate {id: "icert_abc01", carrier: "State Farm", policy_number: "SF-2026-44821", coverage_type: "general_liability", coverage_limit: 100000000, effective_date: date("2026-01-01"), expiration_date: date("2027-01-01"), status: "active", additional_insured: true, created_at: datetime(), updated_at: datetime()})
CREATE (abc_electric)-[:HAS_INSURANCE]->(abc_insurance)

// Milestones
CREATE (ms_watertight:Milestone {id: "ms_dave01", name: "Watertight", planned_date: date("2026-05-30"), actual_date: null, status: "upcoming", created_at: datetime(), updated_at: datetime(), created_by: "mem_dave01", created_by_type: "human", updated_by: "mem_dave01", updated_by_type: "human"})
CREATE (dave_proj)-[:HAS_MILESTONE]->(ms_watertight)

// Variation — client wants upgraded lighting
CREATE (var_lights:Variation {id: "var_dave01", number: 1, description: "Client requested upgraded recessed LED lighting throughout in place of standard fixtures", status: "approved", amount: 420000, created_at: datetime(), updated_at: datetime(), created_by: "mem_dave01", created_by_type: "human", updated_by: "mem_dave01", updated_by_type: "human"})
CREATE (dave_proj)-[:HAS_VARIATION]->(var_lights)
CREATE (var_lights)-[:VARIES]->(wi_dave_elec)

// Invoice — progress claim
CREATE (inv_dave01:Invoice {id: "inv_dave01", direction: "receivable", number: "MC-2026-001", status: "sent", amount: 19500000, due_date: date("2026-05-15"), sent_date: date("2026-04-15"), notes: "Progress claim #1 - 30% complete", created_at: datetime(), updated_at: datetime(), created_by: "mem_dave01", created_by_type: "human", updated_by: "mem_dave01", updated_by_type: "human"})
CREATE (dave_proj)-[:HAS_INVOICE]->(inv_dave01)

// Sub invoice — payable
CREATE (inv_abc01:Invoice {id: "inv_abc01", direction: "payable", number: "ABC-4421", status: "sent", amount: 1560000, due_date: date("2026-05-14"), sent_date: date("2026-04-14"), created_at: datetime(), updated_at: datetime(), created_by: "mem_dave01", created_by_type: "human", updated_by: "mem_dave01", updated_by_type: "human"})
CREATE (dave_proj)-[:HAS_INVOICE]->(inv_abc01)


// ============================================================================
// CONVERSATION & MEMORY EXAMPLE
// ============================================================================

CREATE (conv01:Conversation {id: "conv_jake01", mode: "voice", title: "Quoting Johnson kitchen job", started_at: datetime("2026-04-10T08:45:00"), ended_at: datetime("2026-04-10T08:52:00"), created_at: datetime(), updated_at: datetime(), created_by: "mem_jake01", created_by_type: "human", updated_by: "mem_jake01", updated_by_type: "human"})

CREATE (msg01:Message {id: "msg_jake01", role: "user", content: "I'm at the Johnson kitchen, need to quote a full rewire. New consumer unit, 12 circuits, about 14 sockets, 6 lights, couple of spurs for the appliances.", timestamp: datetime("2026-04-10T08:45:30")})

CREATE (msg02:Message {id: "msg_jake02", role: "assistant", content: "Got it. Based on your last 3 kitchen rewires, you're averaging about 16 hours labour. A new 18-way consumer unit is running about £185. Cable for 12 circuits is roughly 120m at 85p per metre. Sockets and switches about £350 total. That puts your cost around £1,540. At your usual 35% margin, that's £2,370. Want to round to £2,400?", timestamp: datetime("2026-04-10T08:46:15")})

CREATE (msg03:Message {id: "msg_jake03", role: "user", content: "Yeah, make it 2400. Mrs Johnson pays quick, she's good for it.", timestamp: datetime("2026-04-10T08:46:45")})

CREATE (insight01:Insight {id: "ins_jake01", content: "Kitchen rewires average 16 hours labour. Typical cost structure: consumer unit + cable + accessories.", confidence: 0.85, applicability_tags: ["kitchen", "rewire", "residential", "labour_estimate"], created_at: datetime()})

CREATE (decision01:Decision {id: "dec_jake01", description: "Quoted Johnson kitchen rewire at £2,400 including all materials", reasoning: "Based on 16 hours average from past kitchen rewires, 35% margin, rounded up for clean number", confidence: 0.9, created_at: datetime()})

CREATE (jake_co)-[:HAS_CONVERSATION]->(conv01)
CREATE (conv01)-[:ABOUT_PROJECT]->(jake_proj)
CREATE (msg01)-[:PART_OF]->(conv01)
CREATE (msg02)-[:PART_OF]->(conv01)
CREATE (msg03)-[:PART_OF]->(conv01)
CREATE (msg01)-[:FOLLOWS]->(msg02)
CREATE (msg02)-[:FOLLOWS]->(msg03)
CREATE (msg01)-[:SENT_BY]->(jake)
CREATE (msg02)-[:SENT_BY]->(jake) // agent would be AgentIdentity in production
CREATE (msg03)-[:SENT_BY]->(jake)
CREATE (msg03)-[:REFERENCES]->(mrs_johnson)
CREATE (conv01)-[:PRODUCED_DECISION]->(decision01)
CREATE (decision01)-[:AFFECTS]->(jake_proj)
CREATE (conv01)-[:EXPRESSED_KNOWLEDGE]->(insight01)
