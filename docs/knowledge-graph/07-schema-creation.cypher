// ============================================================================
// Kerf Construction Ontology — Neo4j Schema DDL v3.0
// ============================================================================
// Generated from ontology design phases 1-5.
// This file is idempotent — safe to run multiple times.
// All statements use IF NOT EXISTS.
//
// Structure:
//   - Two structural layers: Project → WorkItem
//   - WorkPackage is optional grouping
//   - Tenant isolation via (:Company) traversal root
//   - Regulatory nodes shared across tenants
//   - Vector indexes on Message and DocumentChunk
//   - Provenance fields on all mutable tenant-scoped entities (application-level)
// ============================================================================


// ============================================================================
// WORK MODEL
// ============================================================================

// -- Project --
CREATE CONSTRAINT constraint_project_id IF NOT EXISTS
  FOR (n:Project) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT constraint_project_id_exists IF NOT EXISTS
  FOR (n:Project) REQUIRE n.id IS NOT NULL;
CREATE INDEX index_project_status IF NOT EXISTS
  FOR (n:Project) ON (n.status);
CREATE INDEX index_project_type IF NOT EXISTS
  FOR (n:Project) ON (n.type);
CREATE INDEX index_project_jurisdiction IF NOT EXISTS
  FOR (n:Project) ON (n.jurisdiction_code);

// -- WorkItem --
CREATE CONSTRAINT constraint_work_item_id IF NOT EXISTS
  FOR (n:WorkItem) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT constraint_work_item_id_exists IF NOT EXISTS
  FOR (n:WorkItem) REQUIRE n.id IS NOT NULL;
CREATE INDEX index_work_item_state IF NOT EXISTS
  FOR (n:WorkItem) ON (n.state);
CREATE INDEX index_work_item_planned_start IF NOT EXISTS
  FOR (n:WorkItem) ON (n.planned_start);
CREATE INDEX index_work_item_planned_end IF NOT EXISTS
  FOR (n:WorkItem) ON (n.planned_end);

// -- WorkPackage --
CREATE CONSTRAINT constraint_work_package_id IF NOT EXISTS
  FOR (n:WorkPackage) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT constraint_work_package_id_exists IF NOT EXISTS
  FOR (n:WorkPackage) REQUIRE n.id IS NOT NULL;
CREATE INDEX index_work_package_status IF NOT EXISTS
  FOR (n:WorkPackage) ON (n.status);

// -- WorkCategory --
CREATE CONSTRAINT constraint_work_category_id IF NOT EXISTS
  FOR (n:WorkCategory) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT constraint_work_category_id_exists IF NOT EXISTS
  FOR (n:WorkCategory) REQUIRE n.id IS NOT NULL;

// -- Item (global shared catalogue) --
CREATE CONSTRAINT constraint_item_id IF NOT EXISTS
  FOR (n:Item) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT constraint_item_id_exists IF NOT EXISTS
  FOR (n:Item) REQUIRE n.id IS NOT NULL;
CREATE INDEX index_item_name IF NOT EXISTS
  FOR (n:Item) ON (n.name);
CREATE INDEX index_item_category IF NOT EXISTS
  FOR (n:Item) ON (n.category);

// -- Milestone --
CREATE CONSTRAINT constraint_milestone_id IF NOT EXISTS
  FOR (n:Milestone) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT constraint_milestone_id_exists IF NOT EXISTS
  FOR (n:Milestone) REQUIRE n.id IS NOT NULL;
CREATE INDEX index_milestone_planned_date IF NOT EXISTS
  FOR (n:Milestone) ON (n.planned_date);


// ============================================================================
// COMMERCIAL
// ============================================================================

// -- Contract --
CREATE CONSTRAINT constraint_contract_id IF NOT EXISTS
  FOR (n:Contract) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT constraint_contract_id_exists IF NOT EXISTS
  FOR (n:Contract) REQUIRE n.id IS NOT NULL;
CREATE INDEX index_contract_status IF NOT EXISTS
  FOR (n:Contract) ON (n.status);


// ============================================================================
// FINANCIAL
// ============================================================================

// -- TimeEntry --
CREATE CONSTRAINT constraint_time_entry_id IF NOT EXISTS
  FOR (n:TimeEntry) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT constraint_time_entry_id_exists IF NOT EXISTS
  FOR (n:TimeEntry) REQUIRE n.id IS NOT NULL;
CREATE INDEX index_time_entry_clock_in IF NOT EXISTS
  FOR (n:TimeEntry) ON (n.clock_in);
CREATE INDEX index_time_entry_status IF NOT EXISTS
  FOR (n:TimeEntry) ON (n.status);

// -- Variation --
CREATE CONSTRAINT constraint_variation_id IF NOT EXISTS
  FOR (n:Variation) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT constraint_variation_id_exists IF NOT EXISTS
  FOR (n:Variation) REQUIRE n.id IS NOT NULL;
CREATE INDEX index_variation_status IF NOT EXISTS
  FOR (n:Variation) ON (n.status);

// -- Invoice --
CREATE CONSTRAINT constraint_invoice_id IF NOT EXISTS
  FOR (n:Invoice) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT constraint_invoice_id_exists IF NOT EXISTS
  FOR (n:Invoice) REQUIRE n.id IS NOT NULL;
CREATE INDEX index_invoice_direction IF NOT EXISTS
  FOR (n:Invoice) ON (n.direction);
CREATE INDEX index_invoice_status IF NOT EXISTS
  FOR (n:Invoice) ON (n.status);
CREATE INDEX index_invoice_number IF NOT EXISTS
  FOR (n:Invoice) ON (n.number);
CREATE INDEX index_invoice_due_date IF NOT EXISTS
  FOR (n:Invoice) ON (n.due_date);

// -- InvoiceLine --
CREATE CONSTRAINT constraint_invoice_line_id IF NOT EXISTS
  FOR (n:InvoiceLine) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT constraint_invoice_line_id_exists IF NOT EXISTS
  FOR (n:InvoiceLine) REQUIRE n.id IS NOT NULL;

// -- Payment --
CREATE CONSTRAINT constraint_payment_id IF NOT EXISTS
  FOR (n:Payment) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT constraint_payment_id_exists IF NOT EXISTS
  FOR (n:Payment) REQUIRE n.id IS NOT NULL;
CREATE INDEX index_payment_received_date IF NOT EXISTS
  FOR (n:Payment) ON (n.received_date);

// -- PaymentApplication --
CREATE CONSTRAINT constraint_payment_application_id IF NOT EXISTS
  FOR (n:PaymentApplication) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT constraint_payment_application_id_exists IF NOT EXISTS
  FOR (n:PaymentApplication) REQUIRE n.id IS NOT NULL;
CREATE INDEX index_payment_application_status IF NOT EXISTS
  FOR (n:PaymentApplication) ON (n.status);


// ============================================================================
// ORGANISATIONAL
// ============================================================================

// -- Company --
CREATE CONSTRAINT constraint_company_id IF NOT EXISTS
  FOR (n:Company) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT constraint_company_id_exists IF NOT EXISTS
  FOR (n:Company) REQUIRE n.id IS NOT NULL;
CREATE INDEX index_company_jurisdiction IF NOT EXISTS
  FOR (n:Company) ON (n.jurisdiction_code);

// -- Member --
CREATE CONSTRAINT constraint_member_id IF NOT EXISTS
  FOR (n:Member) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT constraint_member_id_exists IF NOT EXISTS
  FOR (n:Member) REQUIRE n.id IS NOT NULL;
CREATE INDEX index_member_uid IF NOT EXISTS
  FOR (n:Member) ON (n.uid);
CREATE INDEX index_member_email IF NOT EXISTS
  FOR (n:Member) ON (n.email);
CREATE INDEX index_member_access_role IF NOT EXISTS
  FOR (n:Member) ON (n.access_role);

// -- Contact --
CREATE CONSTRAINT constraint_contact_id IF NOT EXISTS
  FOR (n:Contact) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT constraint_contact_id_exists IF NOT EXISTS
  FOR (n:Contact) REQUIRE n.id IS NOT NULL;
CREATE INDEX index_contact_email IF NOT EXISTS
  FOR (n:Contact) ON (n.email);


// ============================================================================
// WORKFORCE
// ============================================================================

// -- Worker --
CREATE CONSTRAINT constraint_worker_id IF NOT EXISTS
  FOR (n:Worker) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT constraint_worker_id_exists IF NOT EXISTS
  FOR (n:Worker) REQUIRE n.id IS NOT NULL;
CREATE INDEX index_worker_status IF NOT EXISTS
  FOR (n:Worker) ON (n.status);
CREATE INDEX index_worker_email IF NOT EXISTS
  FOR (n:Worker) ON (n.email);

// -- Certification --
CREATE CONSTRAINT constraint_certification_id IF NOT EXISTS
  FOR (n:Certification) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT constraint_certification_id_exists IF NOT EXISTS
  FOR (n:Certification) REQUIRE n.id IS NOT NULL;
CREATE INDEX index_certification_status IF NOT EXISTS
  FOR (n:Certification) ON (n.status);
CREATE INDEX index_certification_expiry IF NOT EXISTS
  FOR (n:Certification) ON (n.expiry_date);

// -- Crew --
CREATE CONSTRAINT constraint_crew_id IF NOT EXISTS
  FOR (n:Crew) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT constraint_crew_id_exists IF NOT EXISTS
  FOR (n:Crew) REQUIRE n.id IS NOT NULL;


// ============================================================================
// SAFETY
// ============================================================================

// -- Inspection --
CREATE CONSTRAINT constraint_inspection_id IF NOT EXISTS
  FOR (n:Inspection) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT constraint_inspection_id_exists IF NOT EXISTS
  FOR (n:Inspection) REQUIRE n.id IS NOT NULL;
CREATE INDEX index_inspection_category IF NOT EXISTS
  FOR (n:Inspection) ON (n.category);
CREATE INDEX index_inspection_date IF NOT EXISTS
  FOR (n:Inspection) ON (n.inspection_date);
CREATE INDEX index_inspection_status IF NOT EXISTS
  FOR (n:Inspection) ON (n.overall_status);

// -- InspectionItem --
CREATE CONSTRAINT constraint_inspection_item_id IF NOT EXISTS
  FOR (n:InspectionItem) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT constraint_inspection_item_id_exists IF NOT EXISTS
  FOR (n:InspectionItem) REQUIRE n.id IS NOT NULL;

// -- Incident --
CREATE CONSTRAINT constraint_incident_id IF NOT EXISTS
  FOR (n:Incident) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT constraint_incident_id_exists IF NOT EXISTS
  FOR (n:Incident) REQUIRE n.id IS NOT NULL;
CREATE INDEX index_incident_date IF NOT EXISTS
  FOR (n:Incident) ON (n.incident_date);
CREATE INDEX index_incident_severity IF NOT EXISTS
  FOR (n:Incident) ON (n.severity);
CREATE INDEX index_incident_status IF NOT EXISTS
  FOR (n:Incident) ON (n.status);

// -- HazardReport --
CREATE CONSTRAINT constraint_hazard_report_id IF NOT EXISTS
  FOR (n:HazardReport) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT constraint_hazard_report_id_exists IF NOT EXISTS
  FOR (n:HazardReport) REQUIRE n.id IS NOT NULL;
CREATE INDEX index_hazard_report_status IF NOT EXISTS
  FOR (n:HazardReport) ON (n.status);

// -- HazardObservation --
CREATE CONSTRAINT constraint_hazard_observation_id IF NOT EXISTS
  FOR (n:HazardObservation) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT constraint_hazard_observation_id_exists IF NOT EXISTS
  FOR (n:HazardObservation) REQUIRE n.id IS NOT NULL;

// -- CorrectiveAction --
CREATE CONSTRAINT constraint_corrective_action_id IF NOT EXISTS
  FOR (n:CorrectiveAction) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT constraint_corrective_action_id_exists IF NOT EXISTS
  FOR (n:CorrectiveAction) REQUIRE n.id IS NOT NULL;
CREATE INDEX index_corrective_action_status IF NOT EXISTS
  FOR (n:CorrectiveAction) ON (n.status);
CREATE INDEX index_corrective_action_due_date IF NOT EXISTS
  FOR (n:CorrectiveAction) ON (n.due_date);

// -- ToolboxTalk --
CREATE CONSTRAINT constraint_toolbox_talk_id IF NOT EXISTS
  FOR (n:ToolboxTalk) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT constraint_toolbox_talk_id_exists IF NOT EXISTS
  FOR (n:ToolboxTalk) REQUIRE n.id IS NOT NULL;
CREATE INDEX index_toolbox_talk_status IF NOT EXISTS
  FOR (n:ToolboxTalk) ON (n.status);

// -- ExposureRecord --
CREATE CONSTRAINT constraint_exposure_record_id IF NOT EXISTS
  FOR (n:ExposureRecord) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT constraint_exposure_record_id_exists IF NOT EXISTS
  FOR (n:ExposureRecord) REQUIRE n.id IS NOT NULL;

// -- MorningBrief --
CREATE CONSTRAINT constraint_morning_brief_id IF NOT EXISTS
  FOR (n:MorningBrief) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT constraint_morning_brief_id_exists IF NOT EXISTS
  FOR (n:MorningBrief) REQUIRE n.id IS NOT NULL;
CREATE INDEX index_morning_brief_date IF NOT EXISTS
  FOR (n:MorningBrief) ON (n.date);

// -- IncidentLogEntry --
CREATE CONSTRAINT constraint_incident_log_entry_id IF NOT EXISTS
  FOR (n:IncidentLogEntry) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT constraint_incident_log_entry_id_exists IF NOT EXISTS
  FOR (n:IncidentLogEntry) REQUIRE n.id IS NOT NULL;
CREATE INDEX index_incident_log_entry_date IF NOT EXISTS
  FOR (n:IncidentLogEntry) ON (n.entry_date);
CREATE INDEX index_incident_log_entry_year IF NOT EXISTS
  FOR (n:IncidentLogEntry) ON (n.year);


// ============================================================================
// QUALITY
// ============================================================================

// -- DeficiencyList --
CREATE CONSTRAINT constraint_deficiency_list_id IF NOT EXISTS
  FOR (n:DeficiencyList) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT constraint_deficiency_list_id_exists IF NOT EXISTS
  FOR (n:DeficiencyList) REQUIRE n.id IS NOT NULL;

// -- DeficiencyItem --
CREATE CONSTRAINT constraint_deficiency_item_id IF NOT EXISTS
  FOR (n:DeficiencyItem) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT constraint_deficiency_item_id_exists IF NOT EXISTS
  FOR (n:DeficiencyItem) REQUIRE n.id IS NOT NULL;
CREATE INDEX index_deficiency_item_status IF NOT EXISTS
  FOR (n:DeficiencyItem) ON (n.status);


// ============================================================================
// DAILY OPERATIONS
// ============================================================================

// -- DailyLog --
CREATE CONSTRAINT constraint_daily_log_id IF NOT EXISTS
  FOR (n:DailyLog) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT constraint_daily_log_id_exists IF NOT EXISTS
  FOR (n:DailyLog) REQUIRE n.id IS NOT NULL;
CREATE INDEX index_daily_log_date IF NOT EXISTS
  FOR (n:DailyLog) ON (n.log_date);
CREATE INDEX index_daily_log_status IF NOT EXISTS
  FOR (n:DailyLog) ON (n.status);

// -- MaterialDelivery --
CREATE CONSTRAINT constraint_material_delivery_id IF NOT EXISTS
  FOR (n:MaterialDelivery) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT constraint_material_delivery_id_exists IF NOT EXISTS
  FOR (n:MaterialDelivery) REQUIRE n.id IS NOT NULL;

// -- DelayRecord --
CREATE CONSTRAINT constraint_delay_record_id IF NOT EXISTS
  FOR (n:DelayRecord) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT constraint_delay_record_id_exists IF NOT EXISTS
  FOR (n:DelayRecord) REQUIRE n.id IS NOT NULL;

// -- VisitorRecord --
CREATE CONSTRAINT constraint_visitor_record_id IF NOT EXISTS
  FOR (n:VisitorRecord) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT constraint_visitor_record_id_exists IF NOT EXISTS
  FOR (n:VisitorRecord) REQUIRE n.id IS NOT NULL;


// ============================================================================
// PROJECT COORDINATION
// ============================================================================

// -- ProjectQuery --
CREATE CONSTRAINT constraint_project_query_id IF NOT EXISTS
  FOR (n:ProjectQuery) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT constraint_project_query_id_exists IF NOT EXISTS
  FOR (n:ProjectQuery) REQUIRE n.id IS NOT NULL;
CREATE INDEX index_project_query_status IF NOT EXISTS
  FOR (n:ProjectQuery) ON (n.status);
CREATE INDEX index_project_query_due_date IF NOT EXISTS
  FOR (n:ProjectQuery) ON (n.due_date);

// -- QueryResponse --
CREATE CONSTRAINT constraint_query_response_id IF NOT EXISTS
  FOR (n:QueryResponse) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT constraint_query_response_id_exists IF NOT EXISTS
  FOR (n:QueryResponse) REQUIRE n.id IS NOT NULL;

// -- ReviewSubmission --
CREATE CONSTRAINT constraint_review_submission_id IF NOT EXISTS
  FOR (n:ReviewSubmission) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT constraint_review_submission_id_exists IF NOT EXISTS
  FOR (n:ReviewSubmission) REQUIRE n.id IS NOT NULL;
CREATE INDEX index_review_submission_status IF NOT EXISTS
  FOR (n:ReviewSubmission) ON (n.status);

// -- Warranty --
CREATE CONSTRAINT constraint_warranty_id IF NOT EXISTS
  FOR (n:Warranty) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT constraint_warranty_id_exists IF NOT EXISTS
  FOR (n:Warranty) REQUIRE n.id IS NOT NULL;
CREATE INDEX index_warranty_end_date IF NOT EXISTS
  FOR (n:Warranty) ON (n.end_date);


// ============================================================================
// SUBCONTRACTOR MANAGEMENT
// ============================================================================

// -- GcRelationship --
CREATE CONSTRAINT constraint_gc_relationship_id IF NOT EXISTS
  FOR (n:GcRelationship) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT constraint_gc_relationship_id_exists IF NOT EXISTS
  FOR (n:GcRelationship) REQUIRE n.id IS NOT NULL;

// -- InsuranceCertificate --
CREATE CONSTRAINT constraint_insurance_certificate_id IF NOT EXISTS
  FOR (n:InsuranceCertificate) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT constraint_insurance_certificate_id_exists IF NOT EXISTS
  FOR (n:InsuranceCertificate) REQUIRE n.id IS NOT NULL;
CREATE INDEX index_insurance_certificate_status IF NOT EXISTS
  FOR (n:InsuranceCertificate) ON (n.status);
CREATE INDEX index_insurance_certificate_expiry IF NOT EXISTS
  FOR (n:InsuranceCertificate) ON (n.expiration_date);

// -- PrequalPackage --
CREATE CONSTRAINT constraint_prequal_package_id IF NOT EXISTS
  FOR (n:PrequalPackage) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT constraint_prequal_package_id_exists IF NOT EXISTS
  FOR (n:PrequalPackage) REQUIRE n.id IS NOT NULL;

// -- PaymentRelease --
CREATE CONSTRAINT constraint_payment_release_id IF NOT EXISTS
  FOR (n:PaymentRelease) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT constraint_payment_release_id_exists IF NOT EXISTS
  FOR (n:PaymentRelease) REQUIRE n.id IS NOT NULL;


// ============================================================================
// CONVERSATION & MEMORY
// ============================================================================

// -- Conversation --
CREATE CONSTRAINT constraint_conversation_id IF NOT EXISTS
  FOR (n:Conversation) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT constraint_conversation_id_exists IF NOT EXISTS
  FOR (n:Conversation) REQUIRE n.id IS NOT NULL;

// -- Message --
CREATE CONSTRAINT constraint_message_id IF NOT EXISTS
  FOR (n:Message) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT constraint_message_id_exists IF NOT EXISTS
  FOR (n:Message) REQUIRE n.id IS NOT NULL;
CREATE INDEX index_message_timestamp IF NOT EXISTS
  FOR (n:Message) ON (n.timestamp);

// -- Decision --
CREATE CONSTRAINT constraint_decision_id IF NOT EXISTS
  FOR (n:Decision) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT constraint_decision_id_exists IF NOT EXISTS
  FOR (n:Decision) REQUIRE n.id IS NOT NULL;

// -- Insight --
CREATE CONSTRAINT constraint_insight_id IF NOT EXISTS
  FOR (n:Insight) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT constraint_insight_id_exists IF NOT EXISTS
  FOR (n:Insight) REQUIRE n.id IS NOT NULL;


// ============================================================================
// DOCUMENTS & INTELLIGENCE
// ============================================================================

// -- Document --
CREATE CONSTRAINT constraint_document_id IF NOT EXISTS
  FOR (n:Document) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT constraint_document_id_exists IF NOT EXISTS
  FOR (n:Document) REQUIRE n.id IS NOT NULL;
CREATE INDEX index_document_type IF NOT EXISTS
  FOR (n:Document) ON (n.type);
CREATE INDEX index_document_status IF NOT EXISTS
  FOR (n:Document) ON (n.status);

// -- DocumentChunk --
CREATE CONSTRAINT constraint_document_chunk_id IF NOT EXISTS
  FOR (n:DocumentChunk) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT constraint_document_chunk_id_exists IF NOT EXISTS
  FOR (n:DocumentChunk) REQUIRE n.id IS NOT NULL;


// ============================================================================
// EQUIPMENT & SPATIAL
// ============================================================================

// -- Equipment --
CREATE CONSTRAINT constraint_equipment_id IF NOT EXISTS
  FOR (n:Equipment) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT constraint_equipment_id_exists IF NOT EXISTS
  FOR (n:Equipment) REQUIRE n.id IS NOT NULL;
CREATE INDEX index_equipment_status IF NOT EXISTS
  FOR (n:Equipment) ON (n.status);
CREATE INDEX index_equipment_serial IF NOT EXISTS
  FOR (n:Equipment) ON (n.serial_number);

// -- EquipmentInspectionLog --
CREATE CONSTRAINT constraint_equipment_inspection_log_id IF NOT EXISTS
  FOR (n:EquipmentInspectionLog) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT constraint_equipment_inspection_log_id_exists IF NOT EXISTS
  FOR (n:EquipmentInspectionLog) REQUIRE n.id IS NOT NULL;
CREATE INDEX index_equipment_inspection_log_date IF NOT EXISTS
  FOR (n:EquipmentInspectionLog) ON (n.inspection_date);

// -- Location --
CREATE CONSTRAINT constraint_location_id IF NOT EXISTS
  FOR (n:Location) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT constraint_location_id_exists IF NOT EXISTS
  FOR (n:Location) REQUIRE n.id IS NOT NULL;
CREATE INDEX index_location_type IF NOT EXISTS
  FOR (n:Location) ON (n.location_type);

// -- SafetyZone --
CREATE CONSTRAINT constraint_safety_zone_id IF NOT EXISTS
  FOR (n:SafetyZone) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT constraint_safety_zone_id_exists IF NOT EXISTS
  FOR (n:SafetyZone) REQUIRE n.id IS NOT NULL;
CREATE INDEX index_safety_zone_type IF NOT EXISTS
  FOR (n:SafetyZone) ON (n.zone_type);


// ============================================================================
// ACCESS & PERMISSIONS
// ============================================================================

// -- AccessGrant --
CREATE CONSTRAINT constraint_access_grant_id IF NOT EXISTS
  FOR (n:AccessGrant) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT constraint_access_grant_id_exists IF NOT EXISTS
  FOR (n:AccessGrant) REQUIRE n.id IS NOT NULL;


// ============================================================================
// AGENTIC
// ============================================================================

// -- AgentIdentity --
CREATE CONSTRAINT constraint_agent_identity_id IF NOT EXISTS
  FOR (n:AgentIdentity) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT constraint_agent_identity_id_exists IF NOT EXISTS
  FOR (n:AgentIdentity) REQUIRE n.id IS NOT NULL;
CREATE INDEX index_agent_identity_type IF NOT EXISTS
  FOR (n:AgentIdentity) ON (n.agent_type);
CREATE INDEX index_agent_identity_status IF NOT EXISTS
  FOR (n:AgentIdentity) ON (n.status);

// -- ComplianceAlert --
CREATE CONSTRAINT constraint_compliance_alert_id IF NOT EXISTS
  FOR (n:ComplianceAlert) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT constraint_compliance_alert_id_exists IF NOT EXISTS
  FOR (n:ComplianceAlert) REQUIRE n.id IS NOT NULL;
CREATE INDEX index_compliance_alert_severity IF NOT EXISTS
  FOR (n:ComplianceAlert) ON (n.severity);
CREATE INDEX index_compliance_alert_created_at IF NOT EXISTS
  FOR (n:ComplianceAlert) ON (n.created_at);

// -- BriefingSummary --
CREATE CONSTRAINT constraint_briefing_summary_id IF NOT EXISTS
  FOR (n:BriefingSummary) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT constraint_briefing_summary_id_exists IF NOT EXISTS
  FOR (n:BriefingSummary) REQUIRE n.id IS NOT NULL;
CREATE INDEX index_briefing_summary_date IF NOT EXISTS
  FOR (n:BriefingSummary) ON (n.date);


// ============================================================================
// REGULATORY (shared across tenants)
// ============================================================================

// -- Jurisdiction --
CREATE CONSTRAINT constraint_jurisdiction_code IF NOT EXISTS
  FOR (n:Jurisdiction) REQUIRE n.code IS UNIQUE;
CREATE CONSTRAINT constraint_jurisdiction_code_exists IF NOT EXISTS
  FOR (n:Jurisdiction) REQUIRE n.code IS NOT NULL;

// -- Region --
CREATE CONSTRAINT constraint_region_code IF NOT EXISTS
  FOR (n:Region) REQUIRE n.code IS UNIQUE;
CREATE CONSTRAINT constraint_region_code_exists IF NOT EXISTS
  FOR (n:Region) REQUIRE n.code IS NOT NULL;
CREATE INDEX index_region_jurisdiction_code IF NOT EXISTS
  FOR (n:Region) ON (n.jurisdiction_code);

// -- RegulatoryGroup --
CREATE CONSTRAINT constraint_regulatory_group_id IF NOT EXISTS
  FOR (n:RegulatoryGroup) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT constraint_regulatory_group_id_exists IF NOT EXISTS
  FOR (n:RegulatoryGroup) REQUIRE n.id IS NOT NULL;

// -- Regulation --
CREATE CONSTRAINT constraint_regulation_reference IF NOT EXISTS
  FOR (n:Regulation) REQUIRE n.reference IS UNIQUE;
CREATE CONSTRAINT constraint_regulation_reference_exists IF NOT EXISTS
  FOR (n:Regulation) REQUIRE n.reference IS NOT NULL;
CREATE INDEX index_regulation_jurisdiction IF NOT EXISTS
  FOR (n:Regulation) ON (n.jurisdiction_code);
CREATE INDEX index_regulation_valid_from IF NOT EXISTS
  FOR (n:Regulation) ON (n.valid_from);
CREATE INDEX index_regulation_valid_until IF NOT EXISTS
  FOR (n:Regulation) ON (n.valid_until);

// -- CertificationType --
CREATE CONSTRAINT constraint_certification_type_id IF NOT EXISTS
  FOR (n:CertificationType) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT constraint_certification_type_id_exists IF NOT EXISTS
  FOR (n:CertificationType) REQUIRE n.id IS NOT NULL;
CREATE INDEX index_certification_type_jurisdiction IF NOT EXISTS
  FOR (n:CertificationType) ON (n.jurisdiction_code);

// -- TradeType --
CREATE CONSTRAINT constraint_trade_type_id IF NOT EXISTS
  FOR (n:TradeType) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT constraint_trade_type_id_exists IF NOT EXISTS
  FOR (n:TradeType) REQUIRE n.id IS NOT NULL;

// -- Role --
CREATE CONSTRAINT constraint_role_id IF NOT EXISTS
  FOR (n:Role) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT constraint_role_id_exists IF NOT EXISTS
  FOR (n:Role) REQUIRE n.id IS NOT NULL;

// -- Activity --
CREATE CONSTRAINT constraint_activity_id IF NOT EXISTS
  FOR (n:Activity) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT constraint_activity_id_exists IF NOT EXISTS
  FOR (n:Activity) REQUIRE n.id IS NOT NULL;

// -- HazardCategory --
CREATE CONSTRAINT constraint_hazard_category_id IF NOT EXISTS
  FOR (n:HazardCategory) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT constraint_hazard_category_id_exists IF NOT EXISTS
  FOR (n:HazardCategory) REQUIRE n.id IS NOT NULL;

// -- Substance --
CREATE INDEX index_substance_name IF NOT EXISTS
  FOR (n:Substance) ON (n.name);
CREATE INDEX index_substance_jurisdiction IF NOT EXISTS
  FOR (n:Substance) ON (n.jurisdiction_code);

// -- DocumentType --
CREATE CONSTRAINT constraint_document_type_id IF NOT EXISTS
  FOR (n:DocumentType) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT constraint_document_type_id_exists IF NOT EXISTS
  FOR (n:DocumentType) REQUIRE n.id IS NOT NULL;

// -- InspectionType --
CREATE CONSTRAINT constraint_inspection_type_id IF NOT EXISTS
  FOR (n:InspectionType) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT constraint_inspection_type_id_exists IF NOT EXISTS
  FOR (n:InspectionType) REQUIRE n.id IS NOT NULL;

// -- RegionalRequirement --
CREATE CONSTRAINT constraint_regional_requirement_id IF NOT EXISTS
  FOR (n:RegionalRequirement) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT constraint_regional_requirement_id_exists IF NOT EXISTS
  FOR (n:RegionalRequirement) REQUIRE n.id IS NOT NULL;
CREATE INDEX index_regional_requirement_region IF NOT EXISTS
  FOR (n:RegionalRequirement) ON (n.region_code);

// -- ViolationType --
CREATE CONSTRAINT constraint_violation_type_code IF NOT EXISTS
  FOR (n:ViolationType) REQUIRE n.code IS UNIQUE;
CREATE CONSTRAINT constraint_violation_type_code_exists IF NOT EXISTS
  FOR (n:ViolationType) REQUIRE n.code IS NOT NULL;

// -- IncidentClassification --
CREATE CONSTRAINT constraint_incident_classification_id IF NOT EXISTS
  FOR (n:IncidentClassification) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT constraint_incident_classification_id_exists IF NOT EXISTS
  FOR (n:IncidentClassification) REQUIRE n.id IS NOT NULL;

// -- RecordForm --
CREATE CONSTRAINT constraint_record_form_id IF NOT EXISTS
  FOR (n:RecordForm) REQUIRE n.form_id IS UNIQUE;
CREATE CONSTRAINT constraint_record_form_id_exists IF NOT EXISTS
  FOR (n:RecordForm) REQUIRE n.form_id IS NOT NULL;

// -- RegulatoryVersion --
CREATE CONSTRAINT constraint_regulatory_version_id IF NOT EXISTS
  FOR (n:RegulatoryVersion) REQUIRE n.version_id IS UNIQUE;
CREATE CONSTRAINT constraint_regulatory_version_id_exists IF NOT EXISTS
  FOR (n:RegulatoryVersion) REQUIRE n.version_id IS NOT NULL;

// -- ComplianceProgram --
CREATE INDEX index_compliance_program_name IF NOT EXISTS
  FOR (n:ComplianceProgram) ON (n.name);
CREATE INDEX index_compliance_program_jurisdiction IF NOT EXISTS
  FOR (n:ComplianceProgram) ON (n.jurisdiction_code);


// ============================================================================
// VECTOR INDEXES (Neo4j 5.11+)
// ============================================================================

CREATE VECTOR INDEX message_embeddings IF NOT EXISTS
FOR (m:Message) ON (m.embedding)
OPTIONS {
  indexConfig: {
    `vector.dimensions`: 1536,
    `vector.similarity_function`: 'cosine'
  }
};

CREATE VECTOR INDEX chunk_embeddings IF NOT EXISTS
FOR (c:DocumentChunk) ON (c.embedding)
OPTIONS {
  indexConfig: {
    `vector.dimensions`: 1536,
    `vector.similarity_function`: 'cosine'
  }
};
