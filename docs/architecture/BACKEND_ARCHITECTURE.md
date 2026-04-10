# Kerf Backend Architecture

*Version 1.0 -- 2026-03-31*

This document is the definitive backend blueprint for Kerf through Phase 4. Engineers build from this. Every schema, endpoint, and service is specified to the level of detail needed to write code.

---

## 1. DATA MODEL (Firestore)

### 1.1 Collection Hierarchy

```
companies/{company_id}
  /projects/{project_id}
    /documents/{document_id}
    /inspections/{inspection_id}
    /toolbox_talks/{talk_id}
    /hazard_reports/{report_id}
    /incidents/{incident_id}
  /workers/{worker_id}
    /certifications/{cert_id}
    /training_records/{record_id}
  /equipment/{equipment_id}
  /mock_inspections/{inspection_id}

regulatory_standards/{standard_id}
templates/{template_id}
```

### 1.2 companies/{company_id}

```json
{
  "id": "comp_a1b2c3d4e5f6g7h8",
  "name": "Chen Electrical Contractors LLC",
  "address": "1234 Industrial Blvd, Atlanta, GA 30301",
  "license_number": "EC-2019-04521",
  "trade_type": "electrical",
  "secondary_trades": ["fire_protection"],
  "owner_name": "Sarah Chen",
  "phone": "+1-404-555-0192",
  "email": "sarah@chenelectric.com",
  "ein": null,
  "logo_url": null,
  "employee_count": 45,
  "emr_current": 1.12,
  "emr_history": [
    {"year": 2025, "value": 1.15},
    {"year": 2024, "value": 1.22}
  ],
  "naics_code": "238210",
  "states_of_operation": ["GA", "SC", "NC"],
  "insurance_carrier": "Hartford",
  "insurance_policy_number": null,
  "insurance_expiry": null,
  "prequalification_ids": {
    "isnetworld": null,
    "avetta": null,
    "browz": null
  },
  "settings": {
    "default_language": "en",
    "timezone": "America/New_York",
    "morning_brief_time": "05:45",
    "mock_inspection_frequency": "monthly",
    "notification_preferences": {
      "cert_expiry_days": [30, 14, 7, 1],
      "inspection_reminder": true,
      "morning_brief": true
    }
  },
  "subscription_status": "active",
  "subscription_id": "ls_sub_abc123",
  "subscription_tier": "professional",
  "subscription_period_end": "2026-04-30T23:59:59Z",
  "max_active_projects": 8,
  "feature_flags": {
    "mock_inspection": true,
    "morning_brief": true,
    "photo_hazard": true,
    "voice_input": true,
    "predictive_risk": false,
    "gc_portal": false,
    "prequalification_auto": false
  },
  "created_at": "2026-01-15T10:30:00Z",
  "created_by": "firebase_uid_abc",
  "updated_at": "2026-03-30T14:22:00Z",
  "updated_by": "firebase_uid_abc",
  "deleted": false
}
```

**Indexes:**
- `subscription_status` + `subscription_tier` (billing queries)
- `trade_type` (anonymized analytics aggregation)
- `deleted` + `created_at` (admin listing)

**Security rules:** Only users whose `uid` matches `created_by` or who appear in a `members` subcollection (Phase 4 multi-user) can read/write. Firestore rules enforce company-level isolation.

**Retention:** Active companies retained indefinitely. Soft-deleted companies purged after 90 days by a scheduled Cloud Function.

---

### 1.3 companies/{company_id}/projects/{project_id}

```json
{
  "id": "proj_b2c3d4e5f6g7h8i9",
  "company_id": "comp_a1b2c3d4e5f6g7h8",
  "name": "Elm Street Office Renovation",
  "project_number": "2026-014",
  "status": "active",
  "site_address": "456 Elm Street, Atlanta, GA 30302",
  "site_coordinates": {"lat": 33.749, "lng": -84.388},
  "scope_of_work": "Complete electrical rough-in and finish for 3-story office renovation. 45,000 sq ft.",
  "project_type": "commercial_renovation",
  "start_date": "2026-02-01",
  "estimated_end_date": "2026-07-15",
  "actual_end_date": null,
  "general_contractor": {
    "name": "Morrison & Associates",
    "contact_name": "Dave Morrison",
    "contact_phone": "+1-404-555-0300",
    "contact_email": "dave@morrisonassoc.com",
    "gc_company_id": null
  },
  "assigned_workers": ["wkr_c3d4e5f6g7h8i9j0", "wkr_d4e5f6g7h8i9j0k1"],
  "foreman_uid": "firebase_uid_marco",
  "superintendent_uid": null,
  "applicable_standards": ["1926.400-449", "1926.500-503", "1910.147"],
  "hazard_profile": {
    "primary_hazards": ["electrocution", "fall", "arc_flash"],
    "risk_score": 6.8,
    "risk_score_updated_at": "2026-03-30T05:45:00Z"
  },
  "compliance_score": 78,
  "compliance_score_updated_at": "2026-03-28T10:00:00Z",
  "weather_location_id": "ATL",
  "nearest_hospital": {
    "name": "Grady Memorial Hospital",
    "address": "80 Jesse Hill Jr Dr SE, Atlanta, GA 30303",
    "phone": "+1-404-616-1000",
    "distance_miles": 2.3
  },
  "emergency_assembly_point": "Southeast corner parking lot, near dumpster enclosure",
  "created_at": "2026-02-01T09:00:00Z",
  "created_by": "firebase_uid_abc",
  "updated_at": "2026-03-30T14:22:00Z",
  "updated_by": "firebase_uid_abc",
  "deleted": false
}
```

**Status enum:** `active`, `on_hold`, `completed`, `archived`

**Project type enum:** `commercial_new`, `commercial_renovation`, `residential_new`, `residential_renovation`, `industrial`, `infrastructure`, `demolition`, `other`

**Indexes:**
- `company_id` + `status` + `created_at` (active project listing)
- `status` + `compliance_score` (dashboard sorting)
- `foreman_uid` (foreman's project list)

**Retention:** Completed projects retained for 7 years (OSHA recordkeeping requirement). Archived after 30 days of completion.

---

### 1.4 companies/{company_id}/projects/{project_id}/documents/{document_id}

```json
{
  "id": "doc_e5f6g7h8i9j0k1l2",
  "company_id": "comp_a1b2c3d4e5f6g7h8",
  "project_id": "proj_b2c3d4e5f6g7h8i9",
  "title": "Fall Protection Plan - Elm Street Office Renovation",
  "document_type": "fall_protection",
  "status": "final",
  "content": {},
  "project_info": {
    "site_address": "456 Elm Street, Atlanta, GA 30302",
    "scope_of_work": "Electrical rough-in, 3-story office building",
    "max_working_height_feet": 35,
    "number_of_workers": 12
  },
  "language": "en",
  "version": 2,
  "version_history": [
    {"version": 1, "generated_at": "2026-02-01T10:00:00Z", "generated_by": "firebase_uid_abc"}
  ],
  "applicable_standards": ["1926.500", "1926.501", "1926.502", "1926.503"],
  "ai_model_version": "claude-sonnet-4-20250514",
  "ai_prompt_version": "fall_protection_v2",
  "confidence_score": 0.92,
  "review_status": "reviewed",
  "reviewed_by": "firebase_uid_abc",
  "reviewed_at": "2026-02-02T08:15:00Z",
  "generated_at": "2026-02-01T10:00:32Z",
  "pdf_url": "gs://kerf-documents/comp_a1b2c3d4e5f6g7h8/proj_b2c3d4e5f6g7h8i9/doc_e5f6g7h8i9j0k1l2/v2.pdf",
  "created_at": "2026-02-01T10:00:00Z",
  "created_by": "firebase_uid_abc",
  "updated_at": "2026-02-02T08:15:00Z",
  "updated_by": "firebase_uid_abc",
  "deleted": false
}
```

**Document type enum (expanded):** `sssp`, `jha`, `toolbox_talk`, `incident_report`, `fall_protection`, `hazcom`, `excavation_safety`, `scaffolding`, `ppe_program`, `electrical_safety`, `lockout_tagout`, `confined_space`, `hot_work_permit`, `crane_lift_plan`, `respiratory_protection`, `hearing_conservation`, `heat_illness_prevention`, `silica_exposure`, `lead_compliance`, `osha_300_log`

**Review status enum:** `pending_review`, `reviewed`, `needs_revision`

**Indexes:**
- `project_id` + `document_type` + `deleted` (type filtering per project)
- `project_id` + `status` + `created_at` (project document listing)
- `company_id` + `created_at` + `deleted` (company-wide document count)

**Retention:** 7 years from creation. Version history kept inline (max 10 versions; older versions stored in Cloud Storage as JSON).

---

### 1.5 companies/{company_id}/projects/{project_id}/inspections/{inspection_id}

```json
{
  "id": "insp_f6g7h8i9j0k1l2m3",
  "company_id": "comp_a1b2c3d4e5f6g7h8",
  "project_id": "proj_b2c3d4e5f6g7h8i9",
  "inspection_type": "daily_safety",
  "inspection_date": "2026-03-30",
  "inspector_uid": "firebase_uid_marco",
  "inspector_name": "Marco Gutierrez",
  "status": "completed",
  "started_at": "2026-03-30T06:15:00Z",
  "completed_at": "2026-03-30T06:22:00Z",
  "location": {
    "description": "Building A, Floors 1-3",
    "coordinates": {"lat": 33.749, "lng": -84.388}
  },
  "weather_conditions": {
    "temperature_f": 68,
    "conditions": "partly_cloudy",
    "wind_mph": 8,
    "precipitation": false
  },
  "checklist_items": [
    {
      "item_id": "chk_001",
      "category": "fall_protection",
      "question": "Are all guardrails and toeboards in place and secure?",
      "response": "pass",
      "notes": "",
      "photo_urls": [],
      "osha_standard": "1926.502(b)"
    },
    {
      "item_id": "chk_002",
      "category": "electrical",
      "question": "Are all temporary electrical panels properly grounded and covered?",
      "response": "fail",
      "notes": "Panel on 2nd floor missing cover plate. Tagged out.",
      "photo_urls": [
        "gs://kerf-photos/comp_a1b2c3d4e5f6g7h8/insp_f6g7h8i9j0k1l2m3/chk_002_001.jpg"
      ],
      "osha_standard": "1926.405(b)"
    }
  ],
  "corrective_actions": [
    {
      "action_id": "ca_001",
      "checklist_item_id": "chk_002",
      "description": "Install cover plate on 2nd floor temporary panel",
      "assigned_to": "firebase_uid_marco",
      "due_date": "2026-03-30",
      "status": "open",
      "completed_at": null
    }
  ],
  "summary": {
    "total_items": 24,
    "pass": 22,
    "fail": 1,
    "na": 1,
    "score_percent": 95.6
  },
  "voice_notes": [
    {
      "note_id": "vn_001",
      "audio_url": "gs://kerf-audio/comp_a1b2c3d4e5f6g7h8/insp_f6g7h8i9j0k1l2m3/vn_001.webm",
      "transcript": "Second floor panel cover is missing, I tagged it out and will get a replacement from the truck.",
      "duration_seconds": 8
    }
  ],
  "offline_created": false,
  "synced_at": "2026-03-30T06:22:05Z",
  "created_at": "2026-03-30T06:15:00Z",
  "created_by": "firebase_uid_marco",
  "updated_at": "2026-03-30T06:22:00Z",
  "updated_by": "firebase_uid_marco"
}
```

**Inspection type enum:** `daily_safety`, `weekly_safety`, `pre_task`, `equipment`, `excavation`, `scaffold`, `crane`, `confined_space`, `electrical`, `fire_prevention`

**Checklist response enum:** `pass`, `fail`, `na`, `not_inspected`

**Indexes:**
- `project_id` + `inspection_date` (daily log lookup)
- `project_id` + `inspection_type` + `inspection_date` (type-specific history)
- `inspector_uid` + `inspection_date` (foreman's inspection list)
- `project_id` + `corrective_actions.status` (open corrective actions)

**Retention:** 7 years (OSHA recordkeeping).

---

### 1.6 companies/{company_id}/projects/{project_id}/toolbox_talks/{talk_id}

```json
{
  "id": "talk_g7h8i9j0k1l2m3n4",
  "company_id": "comp_a1b2c3d4e5f6g7h8",
  "project_id": "proj_b2c3d4e5f6g7h8i9",
  "topic": "Trench Safety for Foundation Excavation",
  "topic_category": "excavation",
  "scheduled_date": "2026-03-30",
  "delivered_date": "2026-03-30",
  "status": "completed",
  "presenter_uid": "firebase_uid_marco",
  "presenter_name": "Marco Gutierrez",
  "content": {
    "topic_overview": "...",
    "key_points": [],
    "osha_requirements": [],
    "discussion_questions": []
  },
  "content_language": "en",
  "translated_content": {
    "es": {
      "topic_overview": "...",
      "key_points": [],
      "osha_requirements": [],
      "discussion_questions": []
    }
  },
  "ai_generated": true,
  "ai_model_version": "claude-sonnet-4-20250514",
  "ai_prompt_version": "toolbox_talk_v2",
  "duration_minutes": 8,
  "attendance": [
    {
      "worker_id": "wkr_c3d4e5f6g7h8i9j0",
      "worker_name": "Carlos Mendoza",
      "signature_url": "gs://kerf-signatures/talk_g7h8i9j0k1l2m3n4/carlos.png",
      "signed_at": "2026-03-30T06:08:00Z",
      "language_preference": "es"
    }
  ],
  "attendance_count": 14,
  "location": {
    "coordinates": {"lat": 33.749, "lng": -84.388}
  },
  "applicable_standards": ["1926.650", "1926.651", "1926.652"],
  "weather_triggered": false,
  "incident_triggered": false,
  "created_at": "2026-03-30T05:45:00Z",
  "created_by": "system",
  "updated_at": "2026-03-30T06:10:00Z",
  "updated_by": "firebase_uid_marco"
}
```

**Topic category enum:** `fall_protection`, `electrical`, `excavation`, `scaffolding`, `hazcom`, `ppe`, `heat_illness`, `cold_stress`, `housekeeping`, `struck_by`, `caught_in`, `fire_prevention`, `confined_space`, `lockout_tagout`, `crane_rigging`, `silica`, `lead`, `noise`, `ergonomics`, `general`

**Indexes:**
- `project_id` + `scheduled_date` (daily talk lookup)
- `project_id` + `status` + `scheduled_date` (incomplete talk tracking)
- `company_id` + `topic_category` (topic usage analytics)

**Retention:** 5 years.

---

### 1.7 companies/{company_id}/projects/{project_id}/hazard_reports/{report_id}

```json
{
  "id": "haz_h8i9j0k1l2m3n4o5",
  "company_id": "comp_a1b2c3d4e5f6g7h8",
  "project_id": "proj_b2c3d4e5f6g7h8i9",
  "reporter_uid": "firebase_uid_carlos",
  "reporter_name": "Carlos Mendoza",
  "anonymous": false,
  "report_type": "hazard_observation",
  "severity": "serious",
  "status": "corrective_action",
  "reported_at": "2026-03-30T09:15:00Z",
  "location": {
    "description": "Scaffold, Building A, 3rd level, north side",
    "coordinates": {"lat": 33.749, "lng": -84.388}
  },
  "description_text": "Scaffold missing guardrails on third level north side.",
  "voice_note": {
    "audio_url": "gs://kerf-audio/comp_a1b2c3d4e5f6g7h8/haz_h8i9j0k1l2m3n4o5/voice.webm",
    "transcript": "Andamio en el tercer nivel lado norte no tiene barandillas.",
    "source_language": "es",
    "translated_transcript": "Scaffold on the third level north side does not have guardrails."
  },
  "photos": [
    {
      "photo_id": "ph_001",
      "url": "gs://kerf-photos/comp_a1b2c3d4e5f6g7h8/haz_h8i9j0k1l2m3n4o5/ph_001.jpg",
      "thumbnail_url": "gs://kerf-photos/comp_a1b2c3d4e5f6g7h8/haz_h8i9j0k1l2m3n4o5/ph_001_thumb.jpg",
      "uploaded_at": "2026-03-30T09:15:12Z"
    }
  ],
  "ai_analysis": {
    "hazard_identified": "Missing guardrail system on scaffold platform",
    "osha_standards": [
      {
        "standard": "1926.451(g)(1)",
        "description": "Guardrails required on all open sides and ends of platforms more than 10 feet above the next lower level"
      }
    ],
    "risk_level": "high",
    "recommended_actions": [
      "Stop work in area immediately",
      "Install standard guardrail system (42-inch top rail, 21-inch mid rail, toeboard)",
      "Inspect all scaffold levels for similar deficiencies"
    ],
    "confidence_score": 0.95,
    "model_version": "claude-sonnet-4-20250514",
    "analyzed_at": "2026-03-30T09:15:18Z"
  },
  "corrective_action": {
    "description": "Install guardrails on 3rd level north side. Inspect all scaffold levels.",
    "assigned_to": "firebase_uid_marco",
    "due_date": "2026-03-30",
    "completed_at": null,
    "verification_photo_url": null
  },
  "created_at": "2026-03-30T09:15:00Z",
  "created_by": "firebase_uid_carlos",
  "updated_at": "2026-03-30T09:20:00Z",
  "updated_by": "firebase_uid_marco"
}
```

**Report type enum:** `hazard_observation`, `near_miss`, `unsafe_condition`, `unsafe_act`, `environmental`

**Severity enum:** `imminent_danger`, `serious`, `moderate`, `low`

**Status enum:** `reported`, `under_review`, `corrective_action`, `resolved`, `closed`

**Indexes:**
- `project_id` + `reported_at` (chronological listing)
- `project_id` + `status` (open hazard tracking)
- `project_id` + `severity` + `status` (critical hazard filtering)
- `reporter_uid` + `reported_at` (worker's report history)

**Retention:** 7 years.

---

### 1.8 companies/{company_id}/projects/{project_id}/incidents/{incident_id}

```json
{
  "id": "inc_i9j0k1l2m3n4o5p6",
  "company_id": "comp_a1b2c3d4e5f6g7h8",
  "project_id": "proj_b2c3d4e5f6g7h8i9",
  "incident_number": "INC-2026-003",
  "incident_type": "injury",
  "severity": "first_aid",
  "incident_date": "2026-03-30",
  "incident_time": "13:45",
  "reported_at": "2026-03-30T13:50:00Z",
  "reported_by_uid": "firebase_uid_marco",
  "status": "investigation",
  "location": {
    "description": "Building B, north side, ground level",
    "coordinates": {"lat": 33.749, "lng": -84.388}
  },
  "description": "Worker stepped on protruding nail during debris cleanup.",
  "injured_worker": {
    "worker_id": "wkr_d4e5f6g7h8i9j0k1",
    "name": "Luis Mendoza",
    "trade": "laborer",
    "body_part": "right_foot",
    "injury_nature": "puncture",
    "treatment": "first_aid_on_site",
    "medical_facility": null,
    "lost_time": false,
    "days_away": 0,
    "days_restricted": 0
  },
  "witnesses": [
    {
      "worker_id": "wkr_c3d4e5f6g7h8i9j0",
      "name": "Carlos Mendoza",
      "statement": null
    }
  ],
  "voice_report": {
    "audio_url": "gs://kerf-audio/comp_a1b2c3d4e5f6g7h8/inc_i9j0k1l2m3n4o5p6/voice.webm",
    "transcript": "Luis Mendoza stepped on a protruding nail near building B...",
    "source_language": "en"
  },
  "photos": [
    {
      "photo_id": "ph_001",
      "url": "gs://kerf-photos/comp_a1b2c3d4e5f6g7h8/inc_i9j0k1l2m3n4o5p6/ph_001.jpg",
      "caption": "Nail protruding from debris pile"
    }
  ],
  "ai_analysis": {
    "content": {},
    "osha_recordable": true,
    "osha_recordable_reasoning": "Puncture wound requiring medical treatment beyond first aid (tetanus shot at clinic) is recordable per 29 CFR 1904.7(a).",
    "osha_reporting_required": false,
    "osha_reporting_reasoning": "No hospitalization, amputation, or loss of eye. 8-hour/24-hour reporting not triggered per 29 CFR 1904.39.",
    "forms_required": ["OSHA 301", "OSHA 300"],
    "model_version": "claude-sonnet-4-20250514",
    "analyzed_at": "2026-03-30T13:52:00Z"
  },
  "investigation": {
    "investigator_uid": "firebase_uid_abc",
    "investigation_date": null,
    "immediate_cause": "Protruding nail in debris pile",
    "contributing_factors": [],
    "root_causes": [],
    "methodology": "5_whys",
    "corrective_actions": [
      {
        "action_id": "ca_001",
        "description": "Establish debris cleanup protocol for demolition areas",
        "type": "short_term",
        "responsible_uid": "firebase_uid_marco",
        "target_date": "2026-04-01",
        "status": "pending",
        "completed_at": null
      }
    ]
  },
  "osha_forms": {
    "form_301_generated": false,
    "form_300_logged": false,
    "form_301_content": null,
    "form_300_entry": null
  },
  "created_at": "2026-03-30T13:50:00Z",
  "created_by": "firebase_uid_marco",
  "updated_at": "2026-03-30T14:00:00Z",
  "updated_by": "firebase_uid_abc"
}
```

**Incident type enum:** `injury`, `illness`, `near_miss`, `property_damage`, `environmental`, `vehicle`, `theft`, `fire`

**Severity enum:** `fatality`, `hospitalization`, `lost_time`, `restricted_duty`, `first_aid`, `near_miss`, `property_only`

**Status enum:** `reported`, `investigation`, `corrective_action`, `management_review`, `closed`

**Investigation methodology enum:** `5_whys`, `fishbone`, `taproot`, `barrier_analysis`

**Indexes:**
- `project_id` + `incident_date` (chronological listing)
- `company_id` + `incident_date` (company-wide incident log)
- `company_id` + `status` (open investigations)
- `company_id` + `severity` + `incident_date` (OSHA 300 log queries)
- `injured_worker.lost_time` + `incident_date` (EMR calculation)

**Retention:** 7 years (OSHA 300 log requirement is 5 years; retain 7 for margin).

---

### 1.9 companies/{company_id}/workers/{worker_id}

```json
{
  "id": "wkr_c3d4e5f6g7h8i9j0",
  "company_id": "comp_a1b2c3d4e5f6g7h8",
  "firebase_uid": null,
  "first_name": "Carlos",
  "last_name": "Mendoza",
  "preferred_language": "es",
  "phone": "+1-404-555-0444",
  "email": null,
  "trade": "framing",
  "hire_date": "2024-06-15",
  "termination_date": null,
  "status": "active",
  "emergency_contact": {
    "name": "Maria Mendoza",
    "phone": "+1-404-555-0445",
    "relationship": "wife"
  },
  "assigned_projects": ["proj_b2c3d4e5f6g7h8i9"],
  "compliance_score": 85,
  "certifications_summary": {
    "total": 4,
    "current": 3,
    "expiring_soon": 1,
    "expired": 0
  },
  "created_at": "2024-06-15T09:00:00Z",
  "created_by": "firebase_uid_abc",
  "updated_at": "2026-03-30T14:00:00Z",
  "updated_by": "firebase_uid_abc",
  "deleted": false
}
```

**Status enum:** `active`, `inactive`, `terminated`

**Trade enum:** Same as company `TradeType` plus `laborer`, `ironworker`, `operator`, `teamster`, `superintendent`, `foreman`, `safety_officer`

**Indexes:**
- `company_id` + `status` (active worker listing)
- `company_id` + `trade` + `status` (trade-filtered listing)
- `assigned_projects` + `status` (project crew roster -- array-contains query)
- `certifications_summary.expired` (workers with expired certs)

**Retention:** 7 years after termination.

---

### 1.10 companies/{company_id}/workers/{worker_id}/certifications/{cert_id}

```json
{
  "id": "cert_j0k1l2m3n4o5p6q7",
  "worker_id": "wkr_c3d4e5f6g7h8i9j0",
  "certification_type": "osha_10",
  "certification_name": "OSHA 10-Hour Construction",
  "issuing_body": "OSHA / Authorized Trainer",
  "certificate_number": "OT-2024-881234",
  "issue_date": "2024-07-01",
  "expiry_date": "2029-07-01",
  "status": "current",
  "proof_document_url": "gs://kerf-documents/comp_a1b2c3d4e5f6g7h8/certs/cert_j0k1l2m3n4o5p6q7.pdf",
  "notes": "",
  "created_at": "2024-07-05T10:00:00Z",
  "created_by": "firebase_uid_abc",
  "updated_at": "2024-07-05T10:00:00Z",
  "updated_by": "firebase_uid_abc"
}
```

**Certification type enum:** `osha_10`, `osha_30`, `first_aid_cpr`, `fall_protection_competent`, `scaffolding_competent`, `excavation_competent`, `confined_space`, `hazwoper_40`, `hazwoper_8_refresher`, `forklift_operator`, `crane_operator`, `rigging_signal`, `electrical_qualified`, `aerial_lift`, `fire_watch`, `hot_work`, `lead_awareness`, `silica_competent`, `asbestos_awareness`, `dot_medical`, `welding`, `other`

**Status enum:** `current`, `expiring_soon`, `expired`, `revoked`

**Indexes:**
- `worker_id` + `status` (worker cert overview)
- `expiry_date` (expiry alert batch job)

**Retention:** 7 years after cert expiry or worker termination.

---

### 1.11 companies/{company_id}/workers/{worker_id}/training_records/{record_id}

```json
{
  "id": "trn_k1l2m3n4o5p6q7r8",
  "worker_id": "wkr_c3d4e5f6g7h8i9j0",
  "training_type": "toolbox_talk",
  "training_topic": "Trench Safety for Foundation Excavation",
  "training_date": "2026-03-30",
  "duration_minutes": 8,
  "trainer_name": "Marco Gutierrez",
  "trainer_uid": "firebase_uid_marco",
  "project_id": "proj_b2c3d4e5f6g7h8i9",
  "source_record_id": "talk_g7h8i9j0k1l2m3n4",
  "source_record_type": "toolbox_talk",
  "language": "es",
  "assessment_score": null,
  "documentation_url": null,
  "created_at": "2026-03-30T06:10:00Z",
  "created_by": "system"
}
```

**Training type enum:** `toolbox_talk`, `formal_classroom`, `online_course`, `orientation`, `hands_on`, `drill`, `certification_course`, `osha_outreach`, `vendor_specific`

**Indexes:**
- `worker_id` + `training_date` (worker training history)
- `worker_id` + `training_type` (type-filtered history)
- `project_id` + `training_date` (project training log)

**Retention:** 7 years.

---

### 1.12 companies/{company_id}/equipment/{equipment_id}

```json
{
  "id": "equip_l2m3n4o5p6q7r8s9",
  "company_id": "comp_a1b2c3d4e5f6g7h8",
  "name": "Boom Lift #3",
  "equipment_type": "aerial_lift",
  "make": "JLG",
  "model": "600S",
  "serial_number": "JLG-2021-88431",
  "year": 2021,
  "status": "in_service",
  "assigned_project_id": "proj_b2c3d4e5f6g7h8i9",
  "last_inspection_date": "2026-03-29",
  "next_inspection_due": "2026-03-30",
  "inspection_frequency_days": 1,
  "annual_inspection_due": "2026-09-15",
  "certifications": [
    {
      "cert_type": "annual_inspection",
      "inspector": "CraneWorks LLC",
      "date": "2025-09-15",
      "expiry": "2026-09-15",
      "document_url": "gs://kerf-documents/comp_a1b2c3d4e5f6g7h8/equip/annual_2025.pdf"
    }
  ],
  "applicable_standards": ["1926.453"],
  "inspection_history_count": 47,
  "created_at": "2025-03-10T10:00:00Z",
  "created_by": "firebase_uid_abc",
  "updated_at": "2026-03-29T06:30:00Z",
  "updated_by": "firebase_uid_marco",
  "deleted": false
}
```

**Equipment type enum:** `aerial_lift`, `scaffold`, `crane_mobile`, `crane_tower`, `forklift`, `excavator`, `loader`, `compactor`, `generator`, `welder`, `compressor`, `saw`, `ladder`, `harness`, `vehicle`, `trailer`, `other`

**Status enum:** `in_service`, `out_of_service`, `maintenance`, `retired`

**Indexes:**
- `company_id` + `status` (active equipment listing)
- `company_id` + `equipment_type` + `status` (type-filtered listing)
- `assigned_project_id` + `status` (project equipment roster)
- `next_inspection_due` (overdue inspection alerts)

**Retention:** 5 years after retirement.

---

### 1.13 companies/{company_id}/mock_inspections/{inspection_id}

```json
{
  "id": "mock_m3n4o5p6q7r8s9t0",
  "company_id": "comp_a1b2c3d4e5f6g7h8",
  "project_id": "proj_b2c3d4e5f6g7h8i9",
  "inspection_scope": "project",
  "triggered_by": "scheduled",
  "status": "completed",
  "started_at": "2026-03-01T02:00:00Z",
  "completed_at": "2026-03-01T02:04:32Z",
  "overall_score": 78,
  "previous_score": 72,
  "score_trend": "improving",
  "grade": "B-",
  "findings": [
    {
      "finding_id": "find_001",
      "category": "documentation",
      "severity": "serious",
      "osha_standard": "1926.503(b)",
      "observed_condition": "Fall protection training certifications missing for 2 of 12 workers assigned to elevated work areas.",
      "standard_requirement": "The employer shall verify compliance with paragraph (a) of this section by preparing a written certification record.",
      "recommended_action": "Obtain and file fall protection training certificates for workers J. Ramirez and P. Hernandez before assigning elevated work.",
      "estimated_penalty": "$16,131",
      "priority": "high",
      "auto_resolved": false
    }
  ],
  "categories_assessed": [
    {
      "category": "fall_protection",
      "score": 72,
      "findings_count": 3,
      "standards_checked": ["1926.500", "1926.501", "1926.502", "1926.503"]
    },
    {
      "category": "electrical",
      "score": 90,
      "findings_count": 1,
      "standards_checked": ["1926.400", "1926.404", "1926.405"]
    }
  ],
  "data_sources": [
    "documents", "inspections", "training_records", "certifications",
    "hazard_reports", "incidents", "equipment"
  ],
  "ai_model_version": "claude-sonnet-4-20250514",
  "ai_prompt_version": "mock_inspection_v1",
  "report_pdf_url": null,
  "created_at": "2026-03-01T02:00:00Z",
  "created_by": "system",
  "updated_at": "2026-03-01T02:04:32Z",
  "updated_by": "system"
}
```

**Inspection scope enum:** `project`, `company_wide`

**Triggered by enum:** `scheduled`, `manual`, `on_demand`

**Finding severity enum:** `willful`, `repeat`, `serious`, `other_than_serious`, `de_minimis`

**Indexes:**
- `company_id` + `completed_at` (inspection history)
- `project_id` + `completed_at` (project-scoped history)
- `company_id` + `overall_score` (score tracking)

**Retention:** 5 years.

---

### 1.14 regulatory_standards/{standard_id}

This is a shared, read-only collection maintained by Kerf operations. Not scoped to any company.

```json
{
  "id": "std_1926_501",
  "cfr_number": "1926.501",
  "title": "Duty to Have Fall Protection",
  "subpart": "M",
  "subpart_title": "Fall Protection",
  "part": "1926",
  "full_text_summary": "Requires employers to assess the workplace to determine if surfaces have the strength and structural integrity to support workers. Requires fall protection at 6 feet in construction.",
  "key_requirements": [
    {
      "subsection": "(b)(1)",
      "requirement": "Each employee on a walking/working surface with an unprotected side or edge which is 6 feet or more above a lower level shall be protected by guardrail, safety net, or personal fall arrest system.",
      "applicable_trades": ["general", "roofing", "steel", "concrete", "electrical", "carpentry"],
      "applicable_project_types": ["commercial_new", "commercial_renovation", "residential_new", "industrial"]
    }
  ],
  "penalty_range": {
    "serious": "$16,131",
    "other_than_serious": "$16,131",
    "willful": "$161,323",
    "repeat": "$161,323"
  },
  "effective_date": "1998-02-06",
  "last_amended": "2023-01-15",
  "related_standards": ["1926.500", "1926.502", "1926.503"],
  "frequently_cited_rank": 1,
  "keywords": ["fall protection", "guardrail", "safety net", "personal fall arrest", "6 feet", "unprotected edge"],
  "version": 3,
  "updated_at": "2026-01-15T00:00:00Z"
}
```

**Indexes:**
- `part` + `subpart` (browse by subpart)
- `keywords` (array-contains for search)
- `applicable_trades` (trade-specific standard lookup, within key_requirements -- use collection group query or denormalize)
- `frequently_cited_rank` (top-N queries)

**Retention:** Permanent. Version-controlled; old versions archived.

---

### 1.15 templates/{template_id}

Existing collection, no structural change. Already defined in `app/models/template.py`. Extended with:

```json
{
  "template_id": "fall_protection",
  "name": "Fall Protection Plan",
  "description": "...",
  "document_type": "fall_protection",
  "required_fields": [],
  "sections": [],
  "osha_references": ["1926.500", "1926.501", "1926.502", "1926.503"],
  "estimated_generation_time_seconds": 45,
  "available_languages": ["en", "es"],
  "phase_introduced": 1,
  "tier_required": "starter",
  "version": 2,
  "updated_at": "2026-03-15T00:00:00Z"
}
```

---

### 1.16 Firestore Security Rules (Summary)

```
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {

    // Shared collections — read-only for authenticated users
    match /regulatory_standards/{docId} {
      allow read: if request.auth != null;
      allow write: if false; // admin-only, deployed via CI
    }
    match /templates/{docId} {
      allow read: if request.auth != null;
      allow write: if false;
    }

    // Company-scoped — owner or member access only
    match /companies/{companyId} {
      allow read, write: if request.auth != null
        && (resource.data.created_by == request.auth.uid
            || exists(/databases/$(database)/documents/companies/$(companyId)/members/$(request.auth.uid)));

      // All subcollections inherit company access check
      match /{subcollection=**} {
        allow read, write: if request.auth != null
          && (get(/databases/$(database)/documents/companies/$(companyId)).data.created_by == request.auth.uid
              || exists(/databases/$(database)/documents/companies/$(companyId)/members/$(request.auth.uid)));
      }
    }
  }
}
```

Note: The backend API enforces access control in application code (the `_verify_company_access` pattern). Firestore rules are a defense-in-depth layer, not the primary access control mechanism.

---

## 2. API DESIGN

All endpoints are prefixed with `/api/v1`. Authentication is required on all endpoints except `/health`, `/api/v1/auth/signup`, and `/api/v1/billing/webhook`.

### 2.1 Auth Endpoints

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| POST | `/auth/signup` | Register a new user (creates Firebase user + company) | None (Firebase token created client-side) |
| GET | `/auth/me` | Get current user profile and company association | Bearer |
| POST | `/auth/refresh` | Validate and refresh session | Bearer |

**POST /auth/signup**

```
Request:
{
  "firebase_token": "eyJhbG...",
  "company": { <CompanyCreate fields> }
}

Response 201:
{
  "user": {"uid": "...", "email": "..."},
  "company": { <Company> }
}
```

---

### 2.2 Company Management

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| GET | `/companies/{company_id}` | Get company profile | Bearer + owner |
| PATCH | `/companies/{company_id}` | Update company profile | Bearer + owner |
| DELETE | `/companies/{company_id}` | Soft-delete company | Bearer + owner |
| GET | `/companies/{company_id}/dashboard` | Get compliance dashboard summary | Bearer + owner |
| GET | `/companies/{company_id}/settings` | Get company settings | Bearer + owner |
| PATCH | `/companies/{company_id}/settings` | Update company settings | Bearer + owner |

**GET /companies/{company_id}/dashboard**

```
Response 200:
{
  "company_id": "comp_...",
  "overall_compliance_score": 78,
  "active_projects": [
    {
      "project_id": "proj_...",
      "name": "Elm Street Office Renovation",
      "status": "active",
      "compliance_score": 78,
      "compliance_status": "yellow",
      "open_corrective_actions": 2,
      "last_inspection_date": "2026-03-30",
      "days_since_last_toolbox_talk": 0,
      "risk_score": 6.8
    }
  ],
  "alerts": [
    {
      "type": "cert_expiring",
      "message": "Juan Ramirez: Fall Protection Competent Person expires in 4 days",
      "severity": "warning",
      "action_url": "/workers/wkr_.../certifications/cert_..."
    }
  ],
  "stats": {
    "total_workers": 45,
    "workers_fully_certified": 38,
    "documents_generated_this_month": 12,
    "inspections_completed_this_week": 18,
    "hazard_reports_this_month": 7,
    "days_since_last_incident": 47
  },
  "emr_projection": {
    "current": 1.12,
    "projected": 1.05,
    "savings_estimate_dollars": 12400
  }
}
```

---

### 2.3 Project Management (NEW)

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| POST | `/companies/{cid}/projects` | Create a project | Bearer + owner |
| GET | `/companies/{cid}/projects` | List projects (with status filter) | Bearer + owner |
| GET | `/companies/{cid}/projects/{pid}` | Get project details | Bearer + member |
| PATCH | `/companies/{cid}/projects/{pid}` | Update project | Bearer + owner |
| DELETE | `/companies/{cid}/projects/{pid}` | Soft-delete project | Bearer + owner |
| GET | `/companies/{cid}/projects/{pid}/compliance` | Get project compliance summary | Bearer + member |
| POST | `/companies/{cid}/projects/{pid}/morning-brief` | Generate morning safety brief | Bearer + member |

**POST /companies/{cid}/projects**

```
Request:
{
  "name": "Elm Street Office Renovation",
  "project_number": "2026-014",
  "site_address": "456 Elm Street, Atlanta, GA 30302",
  "scope_of_work": "Complete electrical rough-in and finish for 3-story office renovation.",
  "project_type": "commercial_renovation",
  "start_date": "2026-02-01",
  "estimated_end_date": "2026-07-15",
  "general_contractor": {
    "name": "Morrison & Associates",
    "contact_name": "Dave Morrison",
    "contact_phone": "+1-404-555-0300",
    "contact_email": "dave@morrisonassoc.com"
  },
  "assigned_worker_ids": ["wkr_c3d4...", "wkr_d4e5..."],
  "nearest_hospital": {
    "name": "Grady Memorial Hospital",
    "address": "80 Jesse Hill Jr Dr SE, Atlanta, GA 30303",
    "phone": "+1-404-616-1000"
  }
}

Response 201: { <Project> }
```

**POST /companies/{cid}/projects/{pid}/morning-brief**

```
Response 200:
{
  "project_id": "proj_...",
  "date": "2026-03-31",
  "risk_score": 7.2,
  "risk_level": "elevated",
  "weather": {
    "temperature_f": 38,
    "conditions": "rain_expected",
    "high_f": 52,
    "low_f": 34,
    "alerts": ["Rain expected by noon"]
  },
  "risk_factors": [
    {
      "factor": "Cold weather concrete procedures required (ACI 306)",
      "severity": "high",
      "osha_standard": null,
      "action_required": true
    },
    {
      "factor": "Slip/fall risk elevated due to incoming rain",
      "severity": "medium",
      "osha_standard": "1926.501",
      "action_required": true
    }
  ],
  "certification_alerts": [
    {
      "worker_id": "wkr_...",
      "worker_name": "Juan Ramirez",
      "certification": "Fall Protection Competent Person",
      "expires_in_days": 4
    }
  ],
  "recommended_toolbox_talk": {
    "topic": "Cold Weather Concrete Safety",
    "available_languages": ["en", "es"]
  },
  "open_corrective_actions": 2,
  "yesterday_highlights": {
    "inspections_completed": 1,
    "hazard_reports": 0,
    "incidents": 0
  }
}
```

---

### 2.4 Document Generation (existing, expanded)

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| POST | `/companies/{cid}/projects/{pid}/documents` | Create document in project | Bearer + member |
| GET | `/companies/{cid}/projects/{pid}/documents` | List project documents | Bearer + member |
| GET | `/companies/{cid}/projects/{pid}/documents/{did}` | Get document | Bearer + member |
| PATCH | `/companies/{cid}/projects/{pid}/documents/{did}` | Update document | Bearer + member |
| DELETE | `/companies/{cid}/projects/{pid}/documents/{did}` | Soft-delete document | Bearer + member |
| POST | `/companies/{cid}/projects/{pid}/documents/{did}/generate` | Generate AI content for existing doc | Bearer + member |
| POST | `/companies/{cid}/projects/{pid}/documents/generate` | Create + generate in one step | Bearer + member |
| POST | `/companies/{cid}/projects/{pid}/documents/{did}/regenerate` | Re-generate (creates new version) | Bearer + member |
| POST | `/companies/{cid}/projects/{pid}/documents/{did}/translate` | Translate to target language | Bearer + member |
| PATCH | `/companies/{cid}/projects/{pid}/documents/{did}/review` | Mark as reviewed | Bearer + owner |

**POST /companies/{cid}/projects/{pid}/documents/{did}/translate**

```
Request:
{
  "target_language": "es"
}

Response 200: { <Document with translated_content> }
```

**Backward compatibility:** The existing `/companies/{cid}/documents` endpoints continue to work during migration (see Section 9). Documents created at the old path are treated as unassigned to any project.

---

### 2.5 Inspection Logs (NEW)

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| POST | `/companies/{cid}/projects/{pid}/inspections` | Create inspection log | Bearer + member |
| GET | `/companies/{cid}/projects/{pid}/inspections` | List inspections (date range, type) | Bearer + member |
| GET | `/companies/{cid}/projects/{pid}/inspections/{iid}` | Get inspection detail | Bearer + member |
| PATCH | `/companies/{cid}/projects/{pid}/inspections/{iid}` | Update inspection (add items, notes) | Bearer + member |
| POST | `/companies/{cid}/projects/{pid}/inspections/{iid}/complete` | Mark inspection completed | Bearer + member |
| POST | `/companies/{cid}/projects/{pid}/inspections/{iid}/photos` | Upload inspection photo | Bearer + member |
| POST | `/companies/{cid}/projects/{pid}/inspections/{iid}/voice-notes` | Upload voice note | Bearer + member |
| GET | `/companies/{cid}/projects/{pid}/inspections/checklists` | Get checklist templates for project | Bearer + member |

**POST /companies/{cid}/projects/{pid}/inspections/{iid}/photos**

```
Request: multipart/form-data
  - file: JPEG/PNG, max 10MB
  - checklist_item_id: "chk_002" (optional, associates photo with a checklist item)

Response 201:
{
  "photo_url": "gs://kerf-photos/...",
  "thumbnail_url": "gs://kerf-photos/.../thumb.jpg"
}
```

---

### 2.6 Toolbox Talks (NEW)

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| POST | `/companies/{cid}/projects/{pid}/toolbox-talks` | Create/generate a toolbox talk | Bearer + member |
| GET | `/companies/{cid}/projects/{pid}/toolbox-talks` | List talks (date range) | Bearer + member |
| GET | `/companies/{cid}/projects/{pid}/toolbox-talks/{tid}` | Get talk detail with attendance | Bearer + member |
| POST | `/companies/{cid}/projects/{pid}/toolbox-talks/{tid}/deliver` | Start delivery (changes status) | Bearer + member |
| POST | `/companies/{cid}/projects/{pid}/toolbox-talks/{tid}/attendance` | Record attendance (batch) | Bearer + member |
| POST | `/companies/{cid}/projects/{pid}/toolbox-talks/{tid}/complete` | Complete talk, trigger training records | Bearer + member |
| POST | `/companies/{cid}/projects/{pid}/toolbox-talks/suggest` | Get AI-suggested topic for today | Bearer + member |

**POST /companies/{cid}/projects/{pid}/toolbox-talks/{tid}/attendance**

```
Request:
{
  "attendees": [
    {
      "worker_id": "wkr_c3d4...",
      "signature_data": "data:image/png;base64,...",
      "language_preference": "es"
    }
  ]
}

Response 200:
{
  "recorded": 14,
  "training_records_created": 14
}
```

---

### 2.7 Hazard Reporting (NEW)

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| POST | `/companies/{cid}/projects/{pid}/hazard-reports` | Create hazard report | Bearer + member |
| GET | `/companies/{cid}/projects/{pid}/hazard-reports` | List reports (status, severity filter) | Bearer + member |
| GET | `/companies/{cid}/projects/{pid}/hazard-reports/{rid}` | Get report detail | Bearer + member |
| PATCH | `/companies/{cid}/projects/{pid}/hazard-reports/{rid}` | Update report (corrective action) | Bearer + member |
| POST | `/companies/{cid}/projects/{pid}/hazard-reports/{rid}/photos` | Upload photo (up to 5 per report) | Bearer + member |
| POST | `/companies/{cid}/projects/{pid}/hazard-reports/{rid}/voice-note` | Upload voice note | Bearer + member |
| POST | `/companies/{cid}/projects/{pid}/hazard-reports/{rid}/analyze` | Trigger AI photo analysis | Bearer + member |
| POST | `/companies/{cid}/projects/{pid}/hazard-reports/{rid}/resolve` | Mark resolved with verification | Bearer + member |

**POST /companies/{cid}/projects/{pid}/hazard-reports**

```
Request: multipart/form-data
  - report_type: "hazard_observation"
  - severity: "serious" (optional -- AI will suggest if omitted)
  - description_text: "..." (optional)
  - photo: JPEG/PNG file (optional)
  - voice_note: WEBM/M4A file (optional)
  - anonymous: false
  - location_lat: 33.749 (optional)
  - location_lng: -84.388 (optional)
  - location_description: "Scaffold, Building A, 3rd level"

Response 201: { <HazardReport with ai_analysis if photo provided> }
```

---

### 2.8 Incident Management (NEW)

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| POST | `/companies/{cid}/projects/{pid}/incidents` | Report incident | Bearer + member |
| GET | `/companies/{cid}/projects/{pid}/incidents` | List incidents | Bearer + member |
| GET | `/companies/{cid}/projects/{pid}/incidents/{iid}` | Get incident detail | Bearer + member |
| PATCH | `/companies/{cid}/projects/{pid}/incidents/{iid}` | Update incident | Bearer + owner |
| POST | `/companies/{cid}/projects/{pid}/incidents/{iid}/voice-report` | Upload voice report | Bearer + member |
| POST | `/companies/{cid}/projects/{pid}/incidents/{iid}/photos` | Upload incident photos | Bearer + member |
| POST | `/companies/{cid}/projects/{pid}/incidents/{iid}/investigate` | Start/update investigation | Bearer + owner |
| POST | `/companies/{cid}/projects/{pid}/incidents/{iid}/generate-forms` | Generate OSHA 301/300 entries | Bearer + owner |
| GET | `/companies/{cid}/osha-300-log` | Get OSHA 300 log for calendar year | Bearer + owner |
| GET | `/companies/{cid}/osha-300a-summary` | Generate OSHA 300A annual summary | Bearer + owner |

---

### 2.9 Worker/Certification Management (NEW)

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| POST | `/companies/{cid}/workers` | Add worker | Bearer + owner |
| GET | `/companies/{cid}/workers` | List workers (status, trade filter) | Bearer + member |
| GET | `/companies/{cid}/workers/{wid}` | Get worker profile | Bearer + member |
| PATCH | `/companies/{cid}/workers/{wid}` | Update worker | Bearer + owner |
| DELETE | `/companies/{cid}/workers/{wid}` | Soft-delete worker | Bearer + owner |
| POST | `/companies/{cid}/workers/{wid}/certifications` | Add certification | Bearer + owner |
| GET | `/companies/{cid}/workers/{wid}/certifications` | List certifications | Bearer + member |
| PATCH | `/companies/{cid}/workers/{wid}/certifications/{certid}` | Update certification | Bearer + owner |
| DELETE | `/companies/{cid}/workers/{wid}/certifications/{certid}` | Remove certification | Bearer + owner |
| POST | `/companies/{cid}/workers/{wid}/certifications/{certid}/upload` | Upload proof document | Bearer + owner |
| GET | `/companies/{cid}/workers/{wid}/training-records` | Get training history | Bearer + member |
| GET | `/companies/{cid}/training-matrix` | Get company-wide training matrix | Bearer + owner |
| GET | `/companies/{cid}/cert-expiry-report` | Get upcoming expiration report | Bearer + owner |

---

### 2.10 Equipment Management (NEW)

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| POST | `/companies/{cid}/equipment` | Add equipment | Bearer + owner |
| GET | `/companies/{cid}/equipment` | List equipment (type, status filter) | Bearer + member |
| GET | `/companies/{cid}/equipment/{eid}` | Get equipment detail | Bearer + member |
| PATCH | `/companies/{cid}/equipment/{eid}` | Update equipment | Bearer + owner |
| DELETE | `/companies/{cid}/equipment/{eid}` | Soft-delete equipment | Bearer + owner |
| POST | `/companies/{cid}/equipment/{eid}/inspections` | Log equipment inspection | Bearer + member |
| GET | `/companies/{cid}/equipment/{eid}/inspections` | Get inspection history | Bearer + member |
| POST | `/companies/{cid}/equipment/{eid}/certifications` | Upload equipment cert | Bearer + owner |

---

### 2.11 Mock OSHA Inspection (NEW)

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| POST | `/companies/{cid}/mock-inspections` | Trigger a mock inspection (async) | Bearer + owner |
| GET | `/companies/{cid}/mock-inspections` | List past mock inspections | Bearer + owner |
| GET | `/companies/{cid}/mock-inspections/{mid}` | Get inspection results | Bearer + owner |
| GET | `/companies/{cid}/mock-inspections/{mid}/status` | Poll generation status | Bearer + owner |
| POST | `/companies/{cid}/mock-inspections/{mid}/pdf` | Generate PDF report | Bearer + owner |

**POST /companies/{cid}/mock-inspections**

```
Request:
{
  "scope": "project",
  "project_id": "proj_...",
  "categories": ["fall_protection", "electrical", "excavation"]
}

Response 202:
{
  "mock_inspection_id": "mock_...",
  "status": "processing",
  "estimated_completion_seconds": 120
}
```

This is an async operation. The client polls `/status` or receives a push notification on completion.

---

### 2.12 Morning Safety Brief (NEW)

The morning brief endpoint is under projects (Section 2.3). The brief is generated on-demand or pre-generated by a scheduled job.

---

### 2.13 Analytics/Dashboard (NEW)

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| GET | `/companies/{cid}/analytics/compliance-trend` | Compliance score over time | Bearer + owner |
| GET | `/companies/{cid}/analytics/incident-rates` | Incident frequency/severity rates | Bearer + owner |
| GET | `/companies/{cid}/analytics/inspection-activity` | Inspection completion rates | Bearer + owner |
| GET | `/companies/{cid}/analytics/training-coverage` | Training/cert coverage rates | Bearer + owner |
| GET | `/companies/{cid}/analytics/emr-projection` | EMR impact modeling | Bearer + owner |
| GET | `/companies/{cid}/analytics/risk-trends` | Predictive risk scoring (Phase 3) | Bearer + owner |

All analytics endpoints accept `?from=YYYY-MM-DD&to=YYYY-MM-DD&project_id=proj_...` query parameters.

---

### 2.14 Billing/Subscription

Existing endpoints, no structural change:

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| GET | `/companies/{cid}/billing/status` | Get subscription info | Bearer + owner |
| POST | `/billing/webhook` | Lemon Squeezy webhook | Signature verification |
| POST | `/companies/{cid}/billing/checkout` | Create checkout URL | Bearer + owner |
| POST | `/companies/{cid}/billing/portal` | Create customer portal URL | Bearer + owner |

Extended: the `checkout` endpoint now accepts a `tier` parameter (`starter`, `professional`, `business`).

---

### 2.15 PDF Export

Existing endpoint, extended scope:

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| POST | `/companies/{cid}/projects/{pid}/documents/{did}/pdf` | Generate PDF for document | Bearer + member |
| GET | `/companies/{cid}/projects/{pid}/documents/{did}/pdf` | Download generated PDF | Bearer + member |
| POST | `/companies/{cid}/projects/{pid}/inspections/{iid}/pdf` | Generate inspection PDF | Bearer + member |
| POST | `/companies/{cid}/projects/{pid}/toolbox-talks/{tid}/pdf` | Generate talk PDF with attendance | Bearer + member |
| POST | `/companies/{cid}/projects/{pid}/incidents/{iid}/pdf` | Generate incident report PDF | Bearer + owner |
| POST | `/companies/{cid}/mock-inspections/{mid}/pdf` | Generate mock inspection PDF | Bearer + owner |

---

### 2.16 File Upload (Shared)

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| POST | `/upload/photo` | Upload a photo, returns URL | Bearer |
| POST | `/upload/voice` | Upload a voice recording, returns URL + transcript | Bearer |
| POST | `/upload/document` | Upload a PDF/document, returns URL | Bearer |

All upload endpoints use `multipart/form-data`. The `company_id` is embedded in the upload path for storage isolation.

---

## 3. SERVICE ARCHITECTURE

### 3.1 Service Inventory

```
app/services/
  company_service.py          -- Company CRUD, settings, dashboard aggregation
  project_service.py          -- Project CRUD, compliance scoring
  document_service.py         -- Document CRUD, versioning
  generation_service.py       -- AI document generation (Claude)
  inspection_service.py       -- Inspection log CRUD, checklist management
  toolbox_talk_service.py     -- Talk CRUD, attendance, training record creation
  hazard_report_service.py    -- Hazard report CRUD, photo management
  incident_service.py         -- Incident CRUD, investigation workflow, OSHA forms
  worker_service.py           -- Worker CRUD, cert tracking, training matrix
  equipment_service.py        -- Equipment CRUD, inspection logs
  mock_inspection_service.py  -- Mock inspection orchestration and scoring
  morning_brief_service.py    -- Brief assembly from multiple data sources
  photo_analysis_service.py   -- Claude Vision hazard analysis
  voice_service.py            -- Whisper transcription + structuring
  translation_service.py      -- Document/content translation
  risk_scoring_service.py     -- Predictive risk scoring engine
  weather_service.py          -- Weather API integration
  pdf_service.py              -- PDF generation (WeasyPrint)
  billing_service.py          -- Subscription management (Lemon Squeezy)
  template_service.py         -- Template management
  analytics_service.py        -- Dashboard and analytics aggregation
  notification_service.py     -- Push notifications, email alerts
  storage_service.py          -- Cloud Storage file management
  audit_service.py            -- Audit logging
```

### 3.2 Service Dependency Graph

```
                            ┌──────────────────┐
                            │  API Routers      │
                            └────────┬─────────┘
                                     │
            ┌────────────────────────┼────────────────────────┐
            │                        │                        │
     ┌──────▼──────┐         ┌──────▼──────┐         ┌──────▼──────┐
     │  Company     │         │  Project     │         │  Billing    │
     │  Service     │         │  Service     │         │  Service    │
     └──────┬──────┘         └──────┬──────┘         └─────────────┘
            │                        │
   ┌────────┼─────────┬──────────────┼──────────┬───────────┐
   │        │         │              │          │           │
┌──▼──┐  ┌──▼──┐  ┌───▼───┐  ┌──────▼──┐  ┌───▼───┐  ┌───▼───┐
│Doc  │  │Insp │  │Toolbox│  │Hazard   │  │Inci-  │  │Worker │
│Svc  │  │Svc  │  │Talk   │  │Report   │  │dent   │  │Svc    │
└──┬──┘  └──┬──┘  │Svc    │  │Svc      │  │Svc    │  └───┬───┘
   │        │     └───┬───┘  └────┬────┘  └───┬───┘      │
   │        │         │           │            │          │
   │     ┌──┴─────────┴───────────┴────────────┴──┐       │
   │     │         Shared Infrastructure          │       │
   │     │  ┌────────────┐  ┌───────────────┐     │       │
   ├─────┤  │Generation  │  │Photo Analysis │     │       │
   │     │  │Service     │  │Service        │     │       │
   │     │  └────────────┘  └───────────────┘     │       │
   │     │  ┌────────────┐  ┌───────────────┐     │       │
   │     │  │Voice       │  │Translation    │     ├───────┘
   │     │  │Service     │  │Service        │     │
   │     │  └────────────┘  └───────────────┘     │
   │     │  ┌────────────┐  ┌───────────────┐     │
   │     │  │Storage     │  │Notification   │     │
   │     │  │Service     │  │Service        │     │
   │     │  └────────────┘  └───────────────┘     │
   │     │  ┌────────────┐  ┌───────────────┐     │
   │     │  │Weather     │  │Audit          │     │
   │     │  │Service     │  │Service        │     │
   │     │  └────────────┘  └───────────────┘     │
   │     └────────────────────────────────────────┘
   │
┌──▼──────────┐     ┌──────────────────┐     ┌─────────────┐
│ PDF Service │     │Mock Inspection   │     │Morning Brief│
│             │     │Service           │     │Service      │
└─────────────┘     └──────────────────┘     └─────────────┘
```

**Key dependency rules:**
- Domain services (Document, Inspection, etc.) depend only on Firestore and shared infrastructure services.
- Mock Inspection Service reads from ALL domain services (documents, inspections, training, certs, equipment, hazard reports, incidents).
- Morning Brief Service reads from: project, worker, certification, inspection, hazard report, incident, weather, and toolbox talk services.
- No circular dependencies. Services never depend on routers.

### 3.3 Service Class Signatures

```python
class ProjectService:
    def __init__(self, db: firestore.Client) -> None: ...
    def create(self, company_id: str, data: ProjectCreate, user_id: str) -> Project: ...
    def get(self, company_id: str, project_id: str) -> Project: ...
    def list_projects(self, company_id: str, status: ProjectStatus | None = None) -> list[Project]: ...
    def update(self, company_id: str, project_id: str, data: ProjectUpdate, user_id: str) -> Project: ...
    def delete(self, company_id: str, project_id: str) -> None: ...
    def update_compliance_score(self, company_id: str, project_id: str) -> float: ...
    def assign_workers(self, company_id: str, project_id: str, worker_ids: list[str]) -> None: ...


class InspectionService:
    def __init__(self, db: firestore.Client) -> None: ...
    def create(self, company_id: str, project_id: str, data: InspectionCreate, user_id: str) -> Inspection: ...
    def get(self, company_id: str, project_id: str, inspection_id: str) -> Inspection: ...
    def list_inspections(self, company_id: str, project_id: str, date_from: date | None = None, date_to: date | None = None, inspection_type: InspectionType | None = None) -> list[Inspection]: ...
    def add_checklist_response(self, company_id: str, project_id: str, inspection_id: str, item: ChecklistItem, user_id: str) -> Inspection: ...
    def complete(self, company_id: str, project_id: str, inspection_id: str, user_id: str) -> Inspection: ...
    def get_checklist_template(self, project_type: str, inspection_type: str, trade: str) -> list[ChecklistItem]: ...


class ToolboxTalkService:
    def __init__(self, db: firestore.Client, generation_service: GenerationService) -> None: ...
    def create(self, company_id: str, project_id: str, data: ToolboxTalkCreate, user_id: str) -> ToolboxTalk: ...
    def generate_talk(self, company_id: str, project_id: str, topic: str, language: str = "en") -> ToolboxTalk: ...
    def record_attendance(self, company_id: str, project_id: str, talk_id: str, attendees: list[AttendanceRecord]) -> int: ...
    def complete(self, company_id: str, project_id: str, talk_id: str, user_id: str) -> ToolboxTalk: ...
    def suggest_topic(self, company_id: str, project_id: str) -> str: ...


class HazardReportService:
    def __init__(self, db: firestore.Client, photo_analysis_service: PhotoAnalysisService, storage_service: StorageService) -> None: ...
    def create(self, company_id: str, project_id: str, data: HazardReportCreate, user_id: str) -> HazardReport: ...
    def add_photo(self, company_id: str, project_id: str, report_id: str, file: UploadFile) -> str: ...
    def add_voice_note(self, company_id: str, project_id: str, report_id: str, file: UploadFile) -> VoiceNote: ...
    def analyze_photos(self, company_id: str, project_id: str, report_id: str) -> AIAnalysis: ...
    def resolve(self, company_id: str, project_id: str, report_id: str, resolution: ResolutionData, user_id: str) -> HazardReport: ...


class IncidentService:
    def __init__(self, db: firestore.Client, generation_service: GenerationService) -> None: ...
    def create(self, company_id: str, project_id: str, data: IncidentCreate, user_id: str) -> Incident: ...
    def start_investigation(self, company_id: str, project_id: str, incident_id: str, user_id: str) -> Incident: ...
    def update_investigation(self, company_id: str, project_id: str, incident_id: str, data: InvestigationUpdate, user_id: str) -> Incident: ...
    def generate_osha_forms(self, company_id: str, project_id: str, incident_id: str) -> OshaForms: ...
    def get_osha_300_log(self, company_id: str, year: int) -> Osha300Log: ...


class WorkerService:
    def __init__(self, db: firestore.Client) -> None: ...
    def create(self, company_id: str, data: WorkerCreate, user_id: str) -> Worker: ...
    def get(self, company_id: str, worker_id: str) -> Worker: ...
    def list_workers(self, company_id: str, status: WorkerStatus | None = None, trade: str | None = None) -> list[Worker]: ...
    def add_certification(self, company_id: str, worker_id: str, data: CertificationCreate, user_id: str) -> Certification: ...
    def get_training_matrix(self, company_id: str) -> TrainingMatrix: ...
    def get_expiring_certifications(self, company_id: str, days_ahead: int = 30) -> list[CertificationAlert]: ...
    def create_training_record(self, company_id: str, worker_id: str, data: TrainingRecordCreate) -> TrainingRecord: ...


class MockInspectionService:
    def __init__(
        self,
        db: firestore.Client,
        generation_service: GenerationService,
        document_service: DocumentService,
        inspection_service: InspectionService,
        worker_service: WorkerService,
        equipment_service: EquipmentService,
        hazard_report_service: HazardReportService,
        incident_service: IncidentService,
    ) -> None: ...
    def run_inspection(self, company_id: str, project_id: str | None, scope: str, categories: list[str] | None = None) -> str: ...
    def get_status(self, company_id: str, inspection_id: str) -> MockInspectionStatus: ...
    def get_results(self, company_id: str, inspection_id: str) -> MockInspection: ...


class MorningBriefService:
    def __init__(
        self,
        db: firestore.Client,
        project_service: ProjectService,
        worker_service: WorkerService,
        inspection_service: InspectionService,
        hazard_report_service: HazardReportService,
        incident_service: IncidentService,
        weather_service: WeatherService,
        toolbox_talk_service: ToolboxTalkService,
        risk_scoring_service: RiskScoringService,
    ) -> None: ...
    def generate_brief(self, company_id: str, project_id: str) -> MorningBrief: ...


class PhotoAnalysisService:
    def __init__(self, settings: Settings) -> None: ...
    def analyze_hazard(self, image_bytes: bytes, context: dict[str, Any] | None = None) -> AIAnalysis: ...


class VoiceService:
    def __init__(self, settings: Settings) -> None: ...
    def transcribe(self, audio_bytes: bytes, source_language: str | None = None) -> Transcript: ...
    def structure_report(self, transcript: str, report_type: str) -> dict[str, Any]: ...


class TranslationService:
    def __init__(self, settings: Settings) -> None: ...
    def translate_content(self, content: dict[str, Any], source_language: str, target_language: str) -> dict[str, Any]: ...


class StorageService:
    def __init__(self, settings: Settings) -> None: ...
    def upload_photo(self, company_id: str, path_prefix: str, file: UploadFile) -> tuple[str, str]: ...
    def upload_audio(self, company_id: str, path_prefix: str, file: UploadFile) -> str: ...
    def upload_document(self, company_id: str, path_prefix: str, file: UploadFile) -> str: ...
    def generate_signed_url(self, gcs_path: str, expiry_minutes: int = 60) -> str: ...
    def delete_file(self, gcs_path: str) -> None: ...


class WeatherService:
    def __init__(self, settings: Settings) -> None: ...
    def get_forecast(self, lat: float, lng: float) -> WeatherForecast: ...
    def get_current(self, lat: float, lng: float) -> CurrentWeather: ...
    def get_alerts(self, lat: float, lng: float) -> list[WeatherAlert]: ...
```

### 3.4 The AI Generation Pipeline

The current `GenerationService` handles 5 document types with hardcoded system prompts. The expanded architecture:

```
GenerationService
  ├── PromptRegistry           (loads versioned prompts from files/Firestore)
  ├── DocumentGenerator        (generates safety documents)
  ├── ToolboxTalkGenerator     (generates talks with bilingual support)
  ├── InspectionChecklistGen   (generates trade/project-specific checklists)
  ├── IncidentReportGenerator  (structures voice/text into formal report)
  ├── MockInspectionGenerator  (analyzes data, produces findings)
  ├── MorningBriefGenerator    (assembles risk factors into brief)
  └── OshaFormGenerator        (generates 300/301 form content)
```

Each generator:
1. Loads the prompt template from `PromptRegistry`
2. Assembles context from relevant services
3. Calls Claude API with appropriate model and parameters
4. Validates the response against a JSON schema
5. Logs the generation metadata (model, prompt version, token usage, latency)

### 3.5 The Photo Analysis Pipeline

```
User takes photo
  → POST /hazard-reports/{rid}/photos
    → StorageService.upload_photo()          (stores original + generates thumbnail)
    → PhotoAnalysisService.analyze_hazard()  (Claude Vision API)
      → Prompt includes: photo, project context, trade type, applicable standards
      → Returns: hazard identification, OSHA references, risk level, recommendations
    → HazardReportService.update_ai_analysis()
    → NotificationService.notify_supervisor()
```

### 3.6 The Mock Inspection Engine

The mock inspection is the most complex AI operation. It:

1. **Gathers data** from all domain services for the target scope (project or company):
   - Documents: which written programs exist, their review status, their age
   - Inspections: frequency, completion rate, findings, open corrective actions
   - Training records: coverage by worker, by certification type
   - Certifications: current vs expired vs missing
   - Equipment: inspection currency, certification validity
   - Hazard reports: open/closed ratio, response times
   - Incidents: recordability, investigation completeness

2. **Checks against regulatory standards:**
   - Queries `regulatory_standards` collection for applicable standards based on trade and project type
   - Compares actual state to required state for each standard
   - Each gap becomes a finding

3. **Generates findings via AI:**
   - Sends the gap analysis data to Claude with the mock inspection prompt
   - Claude formats findings in OSHA citation style
   - Each finding includes: standard, observed condition, requirement, severity classification, recommended action, estimated penalty

4. **Scores the inspection:**
   - Weighted scoring: documentation (25%), training (25%), field conditions (25%), recordkeeping (15%), program management (10%)
   - Each category scored 0-100 based on findings
   - Overall score is weighted average
   - Grade: A (90-100), B (80-89), C (70-79), D (60-69), F (0-59)

5. **Stores results** and triggers notification to company owner.

Execution time: 60-180 seconds. Always async.

### 3.7 The Morning Brief Engine

Data sources and assembly:

```
1. WeatherService.get_forecast(project.site_coordinates)
   → Temperature, conditions, alerts, precipitation
   → Maps to: heat illness triggers, cold stress triggers, wind speed limits

2. WorkerService.get_expiring_certifications(company_id, days_ahead=7)
   → Filtered to workers assigned to this project
   → Maps to: cert alerts with worker names and cert types

3. InspectionService.list_inspections(project_id, yesterday)
   → Open corrective actions, failed items
   → Maps to: items requiring follow-up

4. HazardReportService.list_open(project_id)
   → Unresolved hazards
   → Maps to: active hazards

5. IncidentService.list_recent(project_id, days=7)
   → Recent incidents
   → Maps to: incident follow-up items

6. ToolboxTalkService.suggest_topic(project_id)
   → Based on weather, scheduled tasks, recent incidents, topic rotation
   → Maps to: recommended talk

7. RiskScoringService.calculate_project_risk(project_id)
   → Combines all signals into 0-10 risk score
   → Maps to: overall risk assessment
```

The brief is assembled server-side (not AI-generated for each request). AI is used only for the risk narrative and topic suggestion. Latency target: under 3 seconds.

### 3.8 The Predictive Risk Scoring Engine (Phase 3)

Signals:
- Weather forecast (temperature extremes, precipitation, wind)
- Day of week (Monday = higher incident rate industry-wide)
- Project phase (demolition, excavation, steel erection = higher risk)
- Inspection findings trend (increasing failures = rising risk)
- Certification gaps (expired certs on site)
- Incident recency (recent incident = elevated awareness but also pattern indicator)
- Hazard report frequency (sudden increase = potential systemic issue)
- Anonymized cross-customer data (same trade, same region, same season)

Model: Initially a weighted heuristic (no ML). Weights tuned from OSHA fatality data and BLS statistics. Phase 3 introduces a trained model using anonymized customer data.

Output: 0-10 score per project per day, with top 3-5 contributing factors.

### 3.9 Background Job Processing

Architecture: **Google Cloud Tasks** for one-off async work, **Cloud Scheduler** for recurring jobs.

| Job | Trigger | Service | SLA |
|-----|---------|---------|-----|
| Document generation | API request | Cloud Tasks | 60s |
| PDF generation | API request | Cloud Tasks | 30s |
| Photo analysis | API request (after upload) | Cloud Tasks | 15s |
| Voice transcription | API request (after upload) | Cloud Tasks | 20s |
| Mock inspection | API request or scheduled | Cloud Tasks | 180s |
| Morning brief pre-generation | Cloud Scheduler (daily 4:30 AM per timezone) | Cloud Tasks | 30s |
| Cert expiry check | Cloud Scheduler (daily 6:00 AM UTC) | Cloud Tasks | 60s |
| Compliance score recalculation | Cloud Scheduler (hourly) | Cloud Tasks | 120s |
| Regulatory change monitoring | Cloud Scheduler (weekly) | Cloud Tasks | 300s |
| OSHA 300 log auto-update | After incident creation/update | Cloud Tasks | 10s |
| Notification dispatch | Event-driven | Cloud Tasks | 5s |

Implementation: Each Cloud Tasks job hits an internal `/internal/jobs/{job_type}` endpoint protected by IAM (not exposed publicly). The endpoint deserializes the task payload and calls the appropriate service.

### 3.10 Caching Strategy

| Data | Cache Layer | TTL | Invalidation |
|------|-------------|-----|-------------|
| Regulatory standards | In-memory (lru_cache) | 24 hours | Restart or scheduled refresh |
| Templates | In-memory (lru_cache) | 1 hour | On write |
| Weather forecasts | Redis (Memorystore) | 30 minutes | TTL |
| Company settings | Request-scoped | Request lifetime | N/A |
| Dashboard aggregations | Redis | 5 minutes | On underlying data write |
| Prompt templates | In-memory | 1 hour | Restart |
| Checklist templates | In-memory | 1 hour | On write |

Note: For the first 6 months (under 1,000 customers), in-memory caching on Cloud Run instances is sufficient. Redis (Memorystore) is introduced when dashboard query latency exceeds 500ms p95.

---

## 4. AI/LLM ARCHITECTURE

### 4.1 AI Capability Map

| Capability | Model | Input | Output | Avg Tokens | Avg Latency |
|------------|-------|-------|--------|------------|-------------|
| Document generation | Claude Sonnet | Text (company + project context) | JSON (structured document) | 4K-8K out | 15-45s |
| Toolbox talk generation | Claude Sonnet | Text (topic + project context) | JSON (talk content) | 2K-4K out | 10-20s |
| Photo hazard analysis | Claude Sonnet (vision) | Image + text context | JSON (hazard analysis) | 500-1K out | 5-10s |
| Voice transcription | Whisper API (OpenAI) | Audio (WebM/M4A) | Text transcript | N/A | 3-10s |
| Incident report structuring | Claude Haiku | Text (transcript) | JSON (structured report) | 1K-2K out | 3-8s |
| Mock inspection analysis | Claude Sonnet | Text (aggregated data, 10K-20K context) | JSON (findings) | 4K-8K out | 30-60s |
| Morning brief risk narrative | Claude Haiku | Text (risk factors) | Text (2-3 sentences) | 200-400 out | 2-4s |
| Translation | Claude Haiku | Text (source content) | Text (translated content) | 1:1 ratio | 5-15s |
| OSHA form generation | Claude Haiku | Text (incident data) | JSON (form fields) | 1K-2K out | 3-8s |
| Document gap analysis | Claude Sonnet | Text (uploaded doc + standards) | JSON (gap report) | 2K-4K out | 15-30s |

### 4.2 Prompt Management Strategy

Prompts are NOT hardcoded in service files (the current `generation_service.py` pattern must be migrated).

```
backend/
  prompts/
    v1/
      document_generation/
        sssp.md
        jha.md
        toolbox_talk.md
        fall_protection.md
        hazcom.md
        ... (one file per document type)
      photo_analysis/
        hazard_assessment.md
      mock_inspection/
        finding_generator.md
        scoring_rubric.md
      morning_brief/
        risk_narrative.md
        topic_suggestion.md
      incident/
        report_structuring.md
        osha_form_301.md
        root_cause_analysis.md
      translation/
        safety_content.md
    v2/
      ... (new versions as prompts are refined)
```

Each prompt file contains:
- System prompt (the main instruction)
- Input template (variable placeholders)
- Output schema (JSON Schema for validation)
- Test cases (example input/output pairs for regression testing)

```python
class PromptRegistry:
    """Loads and manages versioned prompt templates.

    Prompts are loaded from the filesystem on startup and cached in memory.
    A version parameter allows A/B testing and rollback.
    """

    def __init__(self, prompts_dir: str = "prompts") -> None: ...
    def get_system_prompt(self, capability: str, document_type: str, version: str = "latest") -> str: ...
    def get_output_schema(self, capability: str, document_type: str, version: str = "latest") -> dict: ...
    def list_versions(self, capability: str, document_type: str) -> list[str]: ...
```

### 4.3 Model Selection Per Task

| Task | Model | Reasoning |
|------|-------|-----------|
| Document generation | Claude Sonnet | Complex structured output, regulatory accuracy critical |
| Photo analysis | Claude Sonnet | Vision capability, safety-critical output |
| Mock inspection | Claude Sonnet | Large context window needed, complex analysis |
| Incident structuring | Claude Haiku | Simpler transformation, latency-sensitive |
| Translation | Claude Haiku | Straightforward task, high volume |
| Brief narrative | Claude Haiku | Short output, latency-critical (field use) |
| OSHA form generation | Claude Haiku | Template-filling, deterministic structure |

### 4.4 Cost Management

**Caching:**
- Toolbox talks for common topics (top 50) are pre-generated and cached. Re-generation only on prompt version change.
- Checklist templates are generated once per (project_type, inspection_type, trade) combination and cached.
- Regulatory standard lookups are cached in-memory.

**Model routing:**
- Use Haiku for all tasks where Sonnet is not required (see table above).
- Haiku is roughly 1/10th the cost per token.

**Batch processing:**
- Morning briefs are pre-generated during off-peak (4:30 AM local) via Cloud Scheduler, not on-demand.
- Mock inspections are scheduled monthly, not generated on every page load.

**Token budget tracking:**
- Each generation logs input/output token counts to Firestore (`ai_usage` collection).
- Monthly rollup per company for cost attribution.
- Alert at 80% of monthly budget per tier.

**Projected costs per customer per month (at scale):**
- Starter: ~$2-4 (3-5 doc generations, daily talks from cache)
- Professional: ~$8-15 (unlimited docs, mock inspection, morning briefs, photo analysis)
- Business: ~$15-25 (heavier mock inspection, predictive analytics)

### 4.5 Quality Assurance

**Output validation:**
- Every AI response is validated against the expected JSON schema before storage.
- If validation fails, retry once with a more explicit prompt. If second attempt fails, return error to user.
- Confidence scoring: the AI is prompted to self-assess confidence (0.0-1.0). Scores below 0.7 trigger a warning banner in the UI.

**OSHA standard citation verification:**
- After generation, extract all CFR references from the output.
- Verify each reference exists in the `regulatory_standards` collection.
- Flag any unrecognized references as potential hallucinations.
- This check runs synchronously before returning the response.

**Regression testing:**
- Each prompt version includes test cases (input/expected output).
- CI pipeline runs prompt regression tests on every prompt file change.
- Tests check: JSON validity, schema compliance, presence of required sections, OSHA citation accuracy.

### 4.6 The Regulatory Knowledge Base

The `regulatory_standards` collection is the structured knowledge base. It is:

- **Seeded** from a curated dataset of OSHA 29 CFR 1926 (construction) and relevant 1910 (general industry) standards.
- **Indexed** by trade, project type, hazard type, and keyword for fast lookup.
- **Versioned** with `last_amended` date and change history.
- **Monitored** by a weekly job that checks the Federal Register API for OSHA rulemaking activity.
- **Used** by: generation prompts (included as context), mock inspection engine (compliance checking), morning brief (risk factor mapping), and photo analysis (hazard-to-standard mapping).

Initial seed: approximately 200 standards covering the OSHA Focus Four (falls, struck-by, electrocution, caught-in/between) plus trade-specific standards for all supported trades. Full 29 CFR 1926 coverage by end of Phase 2.

---

## 5. FILE STORAGE

### 5.1 Cloud Storage Buckets

| Bucket | Purpose | Access |
|--------|---------|--------|
| `kerf-documents` | Generated PDFs, uploaded documents, cert proofs | Private (signed URLs) |
| `kerf-photos` | Inspection photos, hazard report photos, incident photos | Private (signed URLs) |
| `kerf-audio` | Voice notes, voice reports | Private (signed URLs) |
| `kerf-signatures` | Toolbox talk attendance signatures | Private (signed URLs) |
| `kerf-exports` | Temporary export files (OSHA logs, training matrices) | Private (signed URLs, 24h expiry) |

### 5.2 Naming Conventions

```
kerf-photos/
  {company_id}/
    inspections/
      {inspection_id}/
        {checklist_item_id}_{sequence}.jpg
        {checklist_item_id}_{sequence}_thumb.jpg
    hazard-reports/
      {report_id}/
        ph_{sequence}.jpg
        ph_{sequence}_thumb.jpg
    incidents/
      {incident_id}/
        ph_{sequence}.jpg

kerf-audio/
  {company_id}/
    inspections/
      {inspection_id}/
        vn_{sequence}.webm
    hazard-reports/
      {report_id}/
        voice.webm
    incidents/
      {incident_id}/
        voice.webm

kerf-documents/
  {company_id}/
    projects/
      {project_id}/
        {document_id}/
          v{version}.pdf
    certs/
      {cert_id}.pdf
    exports/
      osha_300_{year}.pdf
      training_matrix_{date}.pdf

kerf-signatures/
  {talk_id}/
    {worker_id}.png
```

### 5.3 Access Control

- All buckets are private (no public access).
- Access is via **signed URLs** generated by `StorageService`, with configurable expiry (default 60 minutes).
- Signed URLs are generated on-demand when the API returns a URL to the client.
- The backend service account has `storage.objectAdmin` on all buckets.
- No direct client-to-bucket uploads. All uploads go through the API (validates file type, size, and company ownership).

### 5.4 Lifecycle Policies

| Bucket | Policy |
|--------|--------|
| `kerf-documents` | Move to Nearline after 1 year. Move to Coldline after 3 years. Delete after 8 years. |
| `kerf-photos` | Move to Nearline after 1 year. Delete after 8 years. |
| `kerf-audio` | Move to Nearline after 90 days. Move to Coldline after 1 year. Delete after 8 years. |
| `kerf-signatures` | Move to Nearline after 1 year. Delete after 6 years. |
| `kerf-exports` | Delete after 7 days. |

### 5.5 Upload Limits

| File Type | Max Size | Allowed MIME Types |
|-----------|----------|-------------------|
| Photo | 10 MB | image/jpeg, image/png, image/heic |
| Voice note | 25 MB | audio/webm, audio/mp4, audio/m4a, audio/mpeg |
| Document upload | 50 MB | application/pdf, image/jpeg, image/png |
| Signature | 500 KB | image/png |

All uploads are validated server-side by reading the file header (not trusting the Content-Type header).

---

## 6. BACKGROUND JOBS

### 6.1 Architecture

```
API Request (async trigger)
  → Cloud Tasks queue
    → POST /internal/jobs/{job_type}
      → JobRouter dispatches to appropriate service
      → Service executes
      → Result stored in Firestore
      → NotificationService sends completion notice

Cloud Scheduler (recurring)
  → Cloud Tasks queue
    → Same internal endpoint
```

### 6.2 Job Definitions

```python
class JobType(str, Enum):
    DOCUMENT_GENERATION = "document_generation"
    PDF_GENERATION = "pdf_generation"
    PHOTO_ANALYSIS = "photo_analysis"
    VOICE_TRANSCRIPTION = "voice_transcription"
    MOCK_INSPECTION = "mock_inspection"
    MORNING_BRIEF = "morning_brief"
    CERT_EXPIRY_CHECK = "cert_expiry_check"
    COMPLIANCE_SCORE_UPDATE = "compliance_score_update"
    REGULATORY_CHANGE_CHECK = "regulatory_change_check"
    OSHA_300_UPDATE = "osha_300_update"
    NOTIFICATION_DISPATCH = "notification_dispatch"
    TRANSLATION = "translation"
```

### 6.3 Cloud Tasks Queues

| Queue | Max Concurrent | Rate Limit | Retry | Purpose |
|-------|---------------|------------|-------|---------|
| `ai-generation` | 10 | 20/min | 2 retries, exponential backoff | Document gen, mock inspection |
| `pdf-generation` | 5 | 30/min | 2 retries | PDF creation |
| `media-processing` | 5 | 20/min | 2 retries | Photo analysis, voice transcription |
| `scheduled-jobs` | 3 | 10/min | 1 retry | Morning briefs, cert checks, compliance updates |
| `notifications` | 10 | 60/min | 3 retries | Push notifications, email |

### 6.4 Cloud Scheduler Jobs

| Job | Schedule | Timezone Handling | Queue |
|-----|----------|-------------------|-------|
| Morning brief pre-generation | `30 4 * * *` per timezone bucket | Groups companies by timezone, dispatches batch | `scheduled-jobs` |
| Cert expiry check | `0 6 * * *` UTC | All companies | `scheduled-jobs` |
| Compliance score recalculation | `0 * * * *` (hourly) | All active projects | `scheduled-jobs` |
| Regulatory change monitoring | `0 8 * * 1` (Monday 8 AM UTC) | Global | `scheduled-jobs` |
| Soft-delete cleanup | `0 2 * * 0` (Sunday 2 AM UTC) | Purge records past retention | `scheduled-jobs` |

### 6.5 Internal Jobs Router

```python
router = APIRouter(prefix="/internal/jobs", tags=["internal"])

@router.post("/{job_type}")
async def execute_job(
    job_type: JobType,
    payload: dict[str, Any],
    request: Request,
) -> dict:
    """Execute a background job. Protected by IAM — not exposed publicly."""
    # Verify the request comes from Cloud Tasks (check OIDC token)
    verify_cloud_tasks_origin(request)

    handler = JOB_HANDLERS[job_type]
    result = await handler(payload)
    return {"status": "completed", "result": result}
```

---

## 7. SECURITY

### 7.1 Auth Architecture

```
Client (React SPA)
  → Firebase Auth (signup, login, token refresh)
    → Firebase ID Token (JWT, 1 hour expiry)
      → API request with Authorization: Bearer <token>
        → Backend: verify_id_token() via Firebase Admin SDK
          → Extract uid, email, email_verified
          → Check company membership (created_by match or members subcollection)
          → Proceed or 401/403
```

**User roles (Phase 4):**

| Role | Scope | Permissions |
|------|-------|-------------|
| `owner` | Company | Full access. Manage billing, settings, workers, all CRUD. |
| `admin` | Company | Everything except billing and company deletion. |
| `foreman` | Project(s) | Create/edit inspections, talks, hazard reports, incidents for assigned projects. Read documents. |
| `worker` | Project(s) | Submit hazard reports (including anonymous). View toolbox talks. Sign attendance. Read-only for most resources. |
| `gc_viewer` | Company (external) | Read-only access to compliance scores, documents, inspections, training records. Phase 4 GC portal. |

Roles are stored in `companies/{cid}/members/{uid}`:
```json
{
  "uid": "firebase_uid_marco",
  "role": "foreman",
  "assigned_projects": ["proj_b2c3d4..."],
  "added_at": "2026-02-01T09:00:00Z",
  "added_by": "firebase_uid_abc"
}
```

Until Phase 4, the simple `created_by == uid` check is sufficient. The members subcollection is introduced when multi-user access is needed.

### 7.2 Company-Level Data Isolation (Multi-Tenancy)

- Every Firestore query includes `company_id` in the document path.
- The `_verify_company_access` pattern (already in codebase) is applied to every router.
- Firestore security rules enforce path-based isolation as defense-in-depth.
- Cloud Storage paths are prefixed with `company_id`.
- No cross-company queries are possible from the API layer (except for anonymized analytics in Phase 3, which uses a separate read-only aggregation pipeline).

### 7.3 API Rate Limiting

Implemented via middleware on Cloud Run:

| Scope | Limit | Window |
|-------|-------|--------|
| Per user (auth token) | 100 requests | 1 minute |
| Per user AI generation | 10 requests | 1 minute |
| Per user file upload | 20 requests | 1 minute |
| Per IP (unauthenticated) | 20 requests | 1 minute |
| Webhook endpoint | 100 requests | 1 minute |

Implementation: Cloud Run + Cloud Armor (WAF) for IP-based limiting. Application-level middleware for user-based limiting using a Redis counter (or in-memory with sliding window for early stage).

### 7.4 File Upload Security

1. **Size validation:** Enforced in both API middleware (request body limit) and StorageService.
2. **MIME type validation:** Read file magic bytes (first 8 bytes), do not trust Content-Type header.
3. **Image sanitization:** Strip EXIF data from photos (preserve GPS coordinates in a separate field, not in the image file).
4. **Filename sanitization:** Discard original filename. Generate new name using the naming convention.
5. **Virus scanning:** Phase 2 -- integrate Cloud Storage malware scanning (Google Cloud's built-in scanning for uploaded objects).
6. **Content moderation:** Photos are analyzed by Claude Vision for hazard assessment, which inherently checks content.

### 7.5 PII Handling

| Data Type | Storage | Access | Notes |
|-----------|---------|--------|-------|
| Worker names | Firestore (encrypted at rest) | Company members only | Required for training records and OSHA forms |
| Worker phone/email | Firestore | Company owner/admin only | Used for notifications |
| Worker emergency contacts | Firestore | Company owner/admin/foreman | Required for site safety |
| Signatures | Cloud Storage (signed URLs) | Company members only | Attendance verification |
| Voice recordings | Cloud Storage | Company members only | Transcript retained; audio deleted after 1 year |
| Photos with faces | Cloud Storage | Company members only | No facial recognition. EXIF stripped. |

Anonymous hazard reporting: When `anonymous: true`, the `reporter_uid` and `reporter_name` fields are set to `"anonymous"`. The original reporter identity is not stored anywhere.

### 7.6 Audit Logging

Every write operation is logged to a `companies/{cid}/audit_log` subcollection:

```json
{
  "id": "audit_...",
  "timestamp": "2026-03-30T14:22:00Z",
  "user_uid": "firebase_uid_abc",
  "action": "document.create",
  "resource_type": "document",
  "resource_id": "doc_e5f6...",
  "details": {
    "document_type": "fall_protection",
    "project_id": "proj_b2c3..."
  },
  "ip_address": "203.0.113.42"
}
```

Audit logs are append-only. No deletion, no modification. Retained for 7 years.

---

## 8. SCALABILITY

### 8.1 Firestore Scaling Considerations

**Hot spot prevention:**
- Document IDs use `{prefix}_{random_hex}` pattern (already in codebase), which distributes writes evenly.
- Avoid monotonically increasing IDs (no auto-increment, no timestamp-prefix IDs).
- The `companies` collection is the root -- each company's subcollections are isolated, so no single subcollection becomes a hot spot unless one company has extreme volume.

**Compound indexes:**
- Required for all multi-field queries (listed per collection above).
- Deploy indexes via `firestore.indexes.json` in CI.
- Total index count estimate: approximately 40-50 compound indexes.

**Query patterns to avoid:**
- Collection group queries across all companies (use only for admin/analytics with pagination).
- Queries returning more than 1,000 documents in a single request (paginate all list endpoints).
- Inequality filters on more than one field in a single query (Firestore limitation).

**Estimated document counts at scale:**

| Collection | Per Company (avg) | At 1,000 Customers | At 10,000 Customers |
|------------|-------------------|--------------------|--------------------|
| companies | 1 | 1,000 | 10,000 |
| projects | 5 | 5,000 | 50,000 |
| documents | 50 | 50,000 | 500,000 |
| inspections | 500/year | 500,000 | 5,000,000 |
| toolbox_talks | 250/year | 250,000 | 2,500,000 |
| hazard_reports | 50/year | 50,000 | 500,000 |
| incidents | 5/year | 5,000 | 50,000 |
| workers | 30 | 30,000 | 300,000 |
| certifications | 120 | 120,000 | 1,200,000 |
| training_records | 2,000/year | 2,000,000 | 20,000,000 |

Firestore handles this volume without architectural changes. The `training_records` subcollection is the highest volume -- paginate all queries against it.

### 8.2 Cloud Run Autoscaling

```yaml
# cloud-run-service.yaml
spec:
  template:
    metadata:
      annotations:
        autoscaling.knative.dev/minScale: "1"      # Always warm (avoid cold starts)
        autoscaling.knative.dev/maxScale: "20"      # Scale ceiling
    spec:
      containerConcurrency: 80                       # Requests per instance
      timeoutSeconds: 300                            # 5 min for AI generation
      containers:
        - resources:
            limits:
              cpu: "2"
              memory: "1Gi"
```

**Scaling triggers:**
- CPU utilization > 60% triggers scale-up.
- Request queue depth > 10 triggers scale-up.
- Scale-down after 5 minutes of low utilization.

**Cost at scale:**
- 100 customers: 1-2 instances, approximately $50-100/month
- 1,000 customers: 3-5 instances, approximately $200-500/month
- 10,000 customers: 10-20 instances, approximately $1,000-2,500/month

### 8.3 LLM API Rate Limits and Queuing

Anthropic API rate limits (as of current tier):
- Tokens per minute: 40,000 (Haiku), 40,000 (Sonnet)
- Requests per minute: 50 (Haiku), 50 (Sonnet)

**Mitigation:**
- Cloud Tasks queues enforce rate limits (configured per queue).
- The `ai-generation` queue limits to 20 requests/minute, well under API limits.
- Exponential backoff on 429 responses (built into the Anthropic SDK).
- At 10,000 customers, request an API tier upgrade from Anthropic (enterprise tier).

### 8.4 Cost Projections

| Component | 100 Customers | 1,000 Customers | 10,000 Customers |
|-----------|--------------|-----------------|------------------|
| Cloud Run | $75/mo | $350/mo | $2,000/mo |
| Firestore | $25/mo | $200/mo | $1,500/mo |
| Cloud Storage | $10/mo | $100/mo | $800/mo |
| Anthropic API (Claude) | $200/mo | $2,000/mo | $18,000/mo |
| OpenAI API (Whisper) | $20/mo | $150/mo | $1,200/mo |
| Cloud Tasks / Scheduler | $5/mo | $20/mo | $100/mo |
| Redis (Memorystore) | $0 (not needed) | $50/mo | $150/mo |
| Weather API | $10/mo | $50/mo | $200/mo |
| **Total infrastructure** | **$345/mo** | **$2,920/mo** | **$23,950/mo** |
| **Revenue (est.)** | **$20,000/mo** | **$250,000/mo** | **$3,000,000/mo** |
| **Gross margin** | **98.3%** | **98.8%** | **99.2%** |

Note: The largest cost driver is the Anthropic API. Caching common outputs (toolbox talks, checklists) and using Haiku for lightweight tasks keeps this under control. The per-customer AI cost at Professional tier ($8-15/mo) against $299/mo revenue yields strong unit economics.

---

## 9. MIGRATION PLAN

### 9.1 Changes to Existing Codebase

| Area | Current State | Target State | Breaking Change? |
|------|---------------|--------------|-----------------|
| Document storage path | `companies/{cid}/documents/{did}` | `companies/{cid}/projects/{pid}/documents/{did}` | Yes (data migration) |
| Company schema | Basic fields | Full schema with settings, features, EMR | No (additive) |
| Document types | 5 types | 20+ types | No (additive) |
| Generation prompts | Hardcoded in `generation_service.py` | File-based `prompts/` directory | No (internal refactor) |
| Service instantiation | New instance per request in router | Dependency injection via FastAPI `Depends` | No (internal refactor) |
| Company access check | `created_by == uid` | Members subcollection check | No (additive, backward compatible) |
| Subscription tiers | Binary (free/pro) | 4 tiers (starter/professional/business/enterprise) | No (additive) |

### 9.2 Data Migration: Documents to Projects

This is the only breaking change. Migration strategy:

**Phase A (backward compatible):**
1. Deploy the new `projects` collection and all project endpoints.
2. Keep the existing `companies/{cid}/documents/{did}` path working.
3. New documents must be created under a project.
4. Add a "Default Project" auto-created for each company to hold existing documents.

**Phase B (data migration):**
1. Run a one-time migration script that:
   - Creates a "Default Project" for each company (if not already created).
   - Copies all existing documents from `companies/{cid}/documents/{did}` to `companies/{cid}/projects/{default_pid}/documents/{did}`.
   - Adds a `project_id` field to each document.
   - Marks the original documents with `migrated: true`.
2. The old endpoints continue to work, proxying to the default project.

**Phase C (deprecation):**
1. After 90 days, deprecate the old `/companies/{cid}/documents` endpoints.
2. Clients must update to use `/companies/{cid}/projects/{pid}/documents`.
3. After 180 days, remove old endpoints.

### 9.3 Incremental Build Order

This is the recommended implementation sequence. Each phase is independently deployable and valuable.

**Sprint 1-2: Foundation (Phase 1 support)**
1. Project model and CRUD service + endpoints
2. Data migration (documents under projects)
3. Company schema expansion (settings, features)
4. Prompt registry (extract prompts from generation_service.py)
5. Expanded document types (hazcom, excavation_safety, scaffolding, ppe_program, electrical_safety, lockout_tagout)

**Sprint 3-4: Field Operations (Phase 1 core)**
6. Worker model and CRUD service + endpoints
7. Certification model and CRUD + expiry checking
8. Inspection model and CRUD + checklist templates
9. Toolbox talk model and CRUD + attendance + training record creation
10. Storage service (photo upload, voice upload, signature upload)
11. PDF generation for inspections and toolbox talks

**Sprint 5-6: Intelligence Layer (Phase 2 core)**
12. Hazard report model and CRUD
13. Photo analysis service (Claude Vision)
14. Voice service (Whisper transcription + structuring)
15. Incident model and CRUD + investigation workflow
16. OSHA 300 log management
17. Background job infrastructure (Cloud Tasks queues)

**Sprint 7-8: AI Director (Phase 2 advanced)**
18. Morning brief service + scheduled pre-generation
19. Mock inspection service + async execution
20. Translation service (bilingual content)
21. Risk scoring engine (heuristic v1)
22. Dashboard and analytics endpoints
23. Notification service (cert expiry, compliance alerts)

**Sprint 9-10: Data and Network (Phase 3)**
24. Equipment model and CRUD
25. Predictive risk scoring (ML v1)
26. EMR impact modeling
27. Anonymized data pipeline (analytics aggregation)
28. Prequalification data export

**Sprint 11-12: Platform (Phase 4)**
29. Multi-user roles (members subcollection, role-based access)
30. GC portal (read-only external access)
31. State-specific compliance engine
32. API keys for third-party integrations

### 9.4 What Cannot Be Built Incrementally

These require upfront design decisions that affect everything built on top:

1. **The project hierarchy** -- documents, inspections, talks, hazards, and incidents are all scoped to projects. This must be the first change.
2. **The storage service** -- photos, voice notes, and signatures all need the same storage patterns. Build once, use everywhere.
3. **The background job infrastructure** -- mock inspections, morning briefs, and compliance scoring all need async execution. Build the Cloud Tasks pipeline before the first async feature.
4. **The prompt registry** -- all new AI capabilities depend on versioned, file-based prompts. Extract from hardcoded strings before adding new document types.

Everything else can be built incrementally, one collection and one set of endpoints at a time.

---

*This document is the source of truth for backend architecture decisions. All implementation work must trace to the schemas, endpoints, and service signatures defined here. If something needs to change, update this document first, then implement.*
