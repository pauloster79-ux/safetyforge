// ============================================================================
// Kerf Construction Ontology — Neo4j Schema DDL
// ============================================================================
// Schema v2.3 — Aligned with CONSTRUCTION_ONTOLOGY.md v2.3
// Added Quality domain nodes (NCR, Observation, ITP, MaterialTest)
// Renamed PunchList/PunchItem to DeficiencyList/DeficiencyItem
//
// This file is idempotent — safe to run multiple times.
// All statements use IF NOT EXISTS to avoid errors on re-run.
//
// Conventions:
//   - Tenant isolation is graph-native via (:Company)-[:HAS_*]->() edges
//   - Regulatory nodes are shared across tenants
//   - Node identity is via own .id property (unique constraint)
//   - FK _id properties are replaced by graph relationships
// ============================================================================


// ============================================================================
// DOMAIN 1: REGULATORY (shared across all tenants)
// ============================================================================
// Static knowledge base seeded per jurisdiction. Uses jurisdiction-neutral
// labels: Regulation (not Standard), ComplianceProgram (not SafetyProgram),
// RegulatoryGroup (not Subpart).

// -- Jurisdiction --
CREATE CONSTRAINT constraint_jurisdiction_code IF NOT EXISTS
  FOR (n:Jurisdiction) REQUIRE n.code IS UNIQUE;
CREATE CONSTRAINT constraint_jurisdiction_code_exists IF NOT EXISTS
  FOR (n:Jurisdiction) REQUIRE n.code IS NOT NULL;
CREATE CONSTRAINT constraint_jurisdiction_name_exists IF NOT EXISTS
  FOR (n:Jurisdiction) REQUIRE n.name IS NOT NULL;

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
CREATE INDEX index_regulatory_group_jurisdiction IF NOT EXISTS
  FOR (n:RegulatoryGroup) ON (n.jurisdiction_code);

// -- Regulation --
CREATE CONSTRAINT constraint_regulation_reference IF NOT EXISTS
  FOR (n:Regulation) REQUIRE n.reference IS UNIQUE;
CREATE CONSTRAINT constraint_regulation_reference_exists IF NOT EXISTS
  FOR (n:Regulation) REQUIRE n.reference IS NOT NULL;
CREATE INDEX index_regulation_jurisdiction IF NOT EXISTS
  FOR (n:Regulation) ON (n.jurisdiction_code);
CREATE INDEX index_regulation_group IF NOT EXISTS
  FOR (n:Regulation) ON (n.group_id);

// -- ComplianceProgram --
CREATE INDEX index_compliance_program_name IF NOT EXISTS
  FOR (n:ComplianceProgram) ON (n.name);
CREATE INDEX index_compliance_program_jurisdiction IF NOT EXISTS
  FOR (n:ComplianceProgram) ON (n.jurisdiction_code);
CREATE CONSTRAINT constraint_compliance_program_name_exists IF NOT EXISTS
  FOR (n:ComplianceProgram) REQUIRE n.name IS NOT NULL;

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
CREATE INDEX index_document_type_jurisdiction IF NOT EXISTS
  FOR (n:DocumentType) ON (n.jurisdiction_code);

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
CREATE INDEX index_violation_type_jurisdiction IF NOT EXISTS
  FOR (n:ViolationType) ON (n.jurisdiction_code);

// -- IncidentClassification --
CREATE CONSTRAINT constraint_incident_classification_id IF NOT EXISTS
  FOR (n:IncidentClassification) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT constraint_incident_classification_id_exists IF NOT EXISTS
  FOR (n:IncidentClassification) REQUIRE n.id IS NOT NULL;
CREATE INDEX index_incident_classification_jurisdiction IF NOT EXISTS
  FOR (n:IncidentClassification) ON (n.jurisdiction_code);

// -- RecordForm --
CREATE CONSTRAINT constraint_record_form_id IF NOT EXISTS
  FOR (n:RecordForm) REQUIRE n.form_id IS UNIQUE;
CREATE CONSTRAINT constraint_record_form_id_exists IF NOT EXISTS
  FOR (n:RecordForm) REQUIRE n.form_id IS NOT NULL;
CREATE INDEX index_record_form_jurisdiction IF NOT EXISTS
  FOR (n:RecordForm) ON (n.jurisdiction_code);

// -- RegulatoryVersion --
CREATE CONSTRAINT constraint_regulatory_version_id IF NOT EXISTS
  FOR (n:RegulatoryVersion) REQUIRE n.version_id IS UNIQUE;
CREATE CONSTRAINT constraint_regulatory_version_id_exists IF NOT EXISTS
  FOR (n:RegulatoryVersion) REQUIRE n.version_id IS NOT NULL;
CREATE INDEX index_regulatory_version_jurisdiction IF NOT EXISTS
  FOR (n:RegulatoryVersion) ON (n.jurisdiction_code);


// ============================================================================
// DOMAIN 2: ORGANISATIONAL (tenant-scoped)
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

// -- Project --
CREATE CONSTRAINT constraint_project_id IF NOT EXISTS
  FOR (n:Project) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT constraint_project_id_exists IF NOT EXISTS
  FOR (n:Project) REQUIRE n.id IS NOT NULL;
CREATE INDEX index_project_status IF NOT EXISTS
  FOR (n:Project) ON (n.status);


// ============================================================================
// DOMAIN 3: HUMAN RESOURCES (tenant-scoped)
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

// -- Certification (instance, not type) --
CREATE CONSTRAINT constraint_certification_id IF NOT EXISTS
  FOR (n:Certification) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT constraint_certification_id_exists IF NOT EXISTS
  FOR (n:Certification) REQUIRE n.id IS NOT NULL;
CREATE INDEX index_certification_status IF NOT EXISTS
  FOR (n:Certification) ON (n.status);
CREATE INDEX index_certification_expiry IF NOT EXISTS
  FOR (n:Certification) ON (n.expiry_date);


// ============================================================================
// DOMAIN 4: EQUIPMENT (tenant-scoped)
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


// ============================================================================
// DOMAIN 5: SAFETY (tenant-scoped)
// ============================================================================

// -- Inspection --
CREATE CONSTRAINT constraint_inspection_id IF NOT EXISTS
  FOR (n:Inspection) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT constraint_inspection_id_exists IF NOT EXISTS
  FOR (n:Inspection) REQUIRE n.id IS NOT NULL;
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

// -- IdentifiedHazard --
CREATE CONSTRAINT constraint_identified_hazard_id IF NOT EXISTS
  FOR (n:IdentifiedHazard) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT constraint_identified_hazard_id_exists IF NOT EXISTS
  FOR (n:IdentifiedHazard) REQUIRE n.id IS NOT NULL;

// -- ToolboxTalk --
CREATE CONSTRAINT constraint_toolbox_talk_id IF NOT EXISTS
  FOR (n:ToolboxTalk) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT constraint_toolbox_talk_id_exists IF NOT EXISTS
  FOR (n:ToolboxTalk) REQUIRE n.id IS NOT NULL;
CREATE INDEX index_toolbox_talk_status IF NOT EXISTS
  FOR (n:ToolboxTalk) ON (n.status);

// -- CorrectiveAction --
CREATE CONSTRAINT constraint_corrective_action_id IF NOT EXISTS
  FOR (n:CorrectiveAction) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT constraint_corrective_action_id_exists IF NOT EXISTS
  FOR (n:CorrectiveAction) REQUIRE n.id IS NOT NULL;
CREATE INDEX index_corrective_action_status IF NOT EXISTS
  FOR (n:CorrectiveAction) ON (n.status);

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

// -- MockInspectionResult --
CREATE CONSTRAINT constraint_mock_inspection_result_id IF NOT EXISTS
  FOR (n:MockInspectionResult) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT constraint_mock_inspection_result_id_exists IF NOT EXISTS
  FOR (n:MockInspectionResult) REQUIRE n.id IS NOT NULL;


// ============================================================================
// DOMAIN 6: SPATIAL / LOCATION (tenant-scoped)
// ============================================================================

// -- Location --
CREATE CONSTRAINT constraint_location_id IF NOT EXISTS
  FOR (n:Location) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT constraint_location_id_exists IF NOT EXISTS
  FOR (n:Location) REQUIRE n.id IS NOT NULL;
CREATE INDEX index_location_type IF NOT EXISTS
  FOR (n:Location) ON (n.location_type);
CREATE INDEX index_location_qr IF NOT EXISTS
  FOR (n:Location) ON (n.qr_code_id);

// -- SafetyZone --
CREATE CONSTRAINT constraint_safety_zone_id IF NOT EXISTS
  FOR (n:SafetyZone) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT constraint_safety_zone_id_exists IF NOT EXISTS
  FOR (n:SafetyZone) REQUIRE n.id IS NOT NULL;
CREATE INDEX index_safety_zone_type IF NOT EXISTS
  FOR (n:SafetyZone) ON (n.zone_type);


// ============================================================================
// DOMAIN 7: DOCUMENTS (tenant-scoped)
// ============================================================================

// -- Document --
CREATE CONSTRAINT constraint_document_id IF NOT EXISTS
  FOR (n:Document) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT constraint_document_id_exists IF NOT EXISTS
  FOR (n:Document) REQUIRE n.id IS NOT NULL;
CREATE INDEX index_document_type IF NOT EXISTS
  FOR (n:Document) ON (n.document_type);
CREATE INDEX index_document_status IF NOT EXISTS
  FOR (n:Document) ON (n.status);

// -- OshaLogEntry --
CREATE CONSTRAINT constraint_osha_log_entry_id IF NOT EXISTS
  FOR (n:OshaLogEntry) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT constraint_osha_log_entry_id_exists IF NOT EXISTS
  FOR (n:OshaLogEntry) REQUIRE n.id IS NOT NULL;
CREATE INDEX index_osha_log_entry_year IF NOT EXISTS
  FOR (n:OshaLogEntry) ON (n.year);
CREATE INDEX index_osha_log_entry_case IF NOT EXISTS
  FOR (n:OshaLogEntry) ON (n.case_number);

// -- EnvironmentalProgram --
CREATE CONSTRAINT constraint_environmental_program_id IF NOT EXISTS
  FOR (n:EnvironmentalProgram) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT constraint_environmental_program_id_exists IF NOT EXISTS
  FOR (n:EnvironmentalProgram) REQUIRE n.id IS NOT NULL;
CREATE INDEX index_environmental_program_status IF NOT EXISTS
  FOR (n:EnvironmentalProgram) ON (n.status);


// ============================================================================
// DOMAIN 8: DAILY OPERATIONS (tenant-scoped)
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

// -- VoiceSession --
CREATE CONSTRAINT constraint_voice_session_id IF NOT EXISTS
  FOR (n:VoiceSession) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT constraint_voice_session_id_exists IF NOT EXISTS
  FOR (n:VoiceSession) REQUIRE n.id IS NOT NULL;


// ============================================================================
// DOMAIN 9: SUB MANAGEMENT (tenant-scoped)
// ============================================================================

// -- GcRelationship --
// Note: Materialised as (Company)-[:GC_OVER]->(Company) edges in the graph.
// The GcRelationship node is kept for audit/permission metadata.
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

// -- LienWaiver --
CREATE CONSTRAINT constraint_lien_waiver_id IF NOT EXISTS
  FOR (n:LienWaiver) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT constraint_lien_waiver_id_exists IF NOT EXISTS
  FOR (n:LienWaiver) REQUIRE n.id IS NOT NULL;


// ============================================================================
// AGENTIC: AGENT IDENTITY (P0 — cannot retrofit)
// ============================================================================
// Agent identities are first-class graph citizens with cost control fields.
// Permission = traversability: (AgentIdentity)-[:BELONGS_TO]->(Company)

// -- AgentIdentity --
CREATE CONSTRAINT constraint_agent_identity_id IF NOT EXISTS
  FOR (n:AgentIdentity) REQUIRE n.agent_id IS UNIQUE;
CREATE CONSTRAINT constraint_agent_identity_id_exists IF NOT EXISTS
  FOR (n:AgentIdentity) REQUIRE n.agent_id IS NOT NULL;
CREATE INDEX index_agent_identity_type IF NOT EXISTS
  FOR (n:AgentIdentity) ON (n.agent_type);
CREATE INDEX index_agent_identity_status IF NOT EXISTS
  FOR (n:AgentIdentity) ON (n.status);


// ============================================================================
// DOMAINS 10-15: RESERVED (design only — build when validated)
// ============================================================================
// Domain 10: Time & Workforce
// Domain 11: Quality
// Domain 12: Schedule
// Domain 13: Financial
// Domain 14: Project Coordination
// Domain 15: Procurement
// Constraints for these domains will be added when code is built.
