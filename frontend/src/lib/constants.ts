export const ROUTES = {
  LANDING: '/',
  LOGIN: '/login',
  SIGNUP: '/signup',
  FORGOT_PASSWORD: '/forgot-password',
  ONBOARDING: '/onboarding',
  DASHBOARD: '/dashboard',
  PROJECTS: '/projects',
  PROJECT_DETAIL: (id: string) => `/projects/${id}`,
  PROJECT_NEW: '/projects/new',
  INSPECTIONS: (projectId: string) => `/projects/${projectId}/inspections`,
  INSPECTION_NEW: (projectId: string) => `/projects/${projectId}/inspections/new`,
  INSPECTION_DETAIL: (projectId: string, id: string) => `/projects/${projectId}/inspections/${id}`,
  TOOLBOX_TALKS: (projectId: string) => `/projects/${projectId}/toolbox-talks`,
  TOOLBOX_TALK_NEW: (projectId: string) => `/projects/${projectId}/toolbox-talks/new`,
  TOOLBOX_TALK_DELIVER: (projectId: string, id: string) => `/projects/${projectId}/toolbox-talks/${id}/deliver`,
  TOOLBOX_TALK_DETAIL: (projectId: string, id: string) => `/projects/${projectId}/toolbox-talks/${id}`,
  DOCUMENTS: '/documents',
  DOCUMENT_NEW: '/documents/new',
  DOCUMENT_EDIT: (id: string) => `/documents/${id}`,
  TEMPLATES: '/templates',
  SETTINGS: '/settings',
  BILLING: '/billing',
  WORKERS: '/workers',
  WORKER_NEW: '/workers/new',
  WORKER_DETAIL: (id: string) => `/workers/${id}`,
  CERTIFICATION_MATRIX: '/workers/certification-matrix',
  OSHA_LOG: '/osha-log',
  MOCK_INSPECTION: '/mock-inspection',
  MOCK_INSPECTION_RESULT: (id: string) => `/mock-inspection/results/${id}`,
  HAZARD_REPORT_NEW: (projectId: string) => `/projects/${projectId}/hazard-report/new`,
  HAZARD_REPORT_DETAIL: (projectId: string, id: string) => `/projects/${projectId}/hazard-reports/${id}`,
  MORNING_BRIEF: (projectId: string) => `/projects/${projectId}/morning-brief`,
  INCIDENT_NEW: (projectId: string) => `/projects/${projectId}/incidents/new`,
  INCIDENT_DETAIL: (projectId: string, id: string) => `/projects/${projectId}/incidents/${id}`,
  ANALYTICS: '/analytics',
  PREQUALIFICATION: '/prequalification',
  GC_PORTAL: '/gc-portal',
  STATE_COMPLIANCE: '/state-compliance',
  ENVIRONMENTAL: '/environmental',
  EQUIPMENT: '/equipment',
  EQUIPMENT_NEW: '/equipment/new',
  EQUIPMENT_DETAIL: (id: string) => `/equipment/${id}`,
  INSPECTIONS_LIST: '/inspections',
  INCIDENTS_LIST: '/incidents',
  TOOLBOX_TALKS_LIST: '/toolbox-talks',
  TEAM: '/team',
} as const;

export interface DocumentTypeConfig {
  id: string;
  name: string;
  description: string;
  icon: string;
  fields: TemplateField[];
}

export interface TemplateField {
  id: string;
  label: string;
  type: 'text' | 'textarea' | 'select' | 'date' | 'number';
  placeholder?: string;
  required: boolean;
  options?: { value: string; label: string }[];
}

export const DOCUMENT_TYPES: DocumentTypeConfig[] = [
  {
    id: 'sssp',
    name: 'Site-Specific Safety Plan (SSSP)',
    description: 'Comprehensive safety plan for a construction site, covering hazard identification, emergency procedures, and worker responsibilities.',
    icon: 'ShieldCheck',
    fields: [
      { id: 'project_name', label: 'Project Name', type: 'text', placeholder: 'e.g., Downtown Office Tower', required: true },
      { id: 'project_address', label: 'Project Address', type: 'text', placeholder: '123 Main St, City, State', required: true },
      { id: 'client_name', label: 'Client / Owner', type: 'text', placeholder: 'ABC Development Corp', required: true },
      { id: 'project_type', label: 'Project Type', type: 'select', required: true, options: [
        { value: 'commercial', label: 'Commercial' },
        { value: 'residential', label: 'Residential' },
        { value: 'industrial', label: 'Industrial' },
        { value: 'infrastructure', label: 'Infrastructure' },
        { value: 'renovation', label: 'Renovation' },
      ]},
      { id: 'start_date', label: 'Estimated Start Date', type: 'date', required: true },
      { id: 'end_date', label: 'Estimated End Date', type: 'date', required: true },
      { id: 'num_workers', label: 'Expected Number of Workers', type: 'number', placeholder: '25', required: true },
      { id: 'special_hazards', label: 'Special Hazards / Considerations', type: 'textarea', placeholder: 'e.g., Confined spaces, working at height above 30ft, proximity to live traffic', required: false },
    ],
  },
  {
    id: 'jha',
    name: 'Job Hazard Analysis',
    description: 'Detailed analysis of specific job tasks, identifying hazards and establishing preventive measures for each step.',
    icon: 'AlertTriangle',
    fields: [
      { id: 'job_title', label: 'Job / Task Title', type: 'text', placeholder: 'e.g., Roof Truss Installation', required: true },
      { id: 'location', label: 'Job Location', type: 'text', placeholder: 'Building A, Level 3', required: true },
      { id: 'trade', label: 'Trade / Discipline', type: 'select', required: true, options: [
        { value: 'general', label: 'General Labor' },
        { value: 'carpentry', label: 'Carpentry' },
        { value: 'electrical', label: 'Electrical' },
        { value: 'plumbing', label: 'Plumbing' },
        { value: 'welding', label: 'Welding' },
        { value: 'roofing', label: 'Roofing' },
        { value: 'concrete', label: 'Concrete' },
        { value: 'demolition', label: 'Demolition' },
        { value: 'excavation', label: 'Excavation' },
        { value: 'painting', label: 'Painting' },
        { value: 'hvac', label: 'HVAC' },
        { value: 'steelwork', label: 'Structural Steel' },
      ]},
      { id: 'equipment_used', label: 'Equipment / Tools Used', type: 'textarea', placeholder: 'e.g., Crane, harnesses, power drill, scaffolding', required: true },
      { id: 'task_description', label: 'Brief Task Description', type: 'textarea', placeholder: 'Describe the steps involved in this job', required: true },
      { id: 'ppe_required', label: 'PPE Required', type: 'textarea', placeholder: 'e.g., Hard hat, safety glasses, fall harness, steel-toe boots', required: true },
    ],
  },
  {
    id: 'toolbox_talk',
    name: 'Toolbox Talk',
    description: 'Short safety briefing focused on a specific hazard or topic, designed for daily or weekly crew meetings.',
    icon: 'MessageSquare',
    fields: [
      { id: 'topic', label: 'Talk Topic', type: 'text', placeholder: 'e.g., Fall Protection Best Practices', required: true },
      { id: 'target_audience', label: 'Target Audience', type: 'select', required: true, options: [
        { value: 'all_workers', label: 'All Workers' },
        { value: 'new_hires', label: 'New Hires' },
        { value: 'supervisors', label: 'Supervisors' },
        { value: 'specific_trade', label: 'Specific Trade' },
      ]},
      { id: 'duration', label: 'Estimated Duration (minutes)', type: 'number', placeholder: '15', required: true },
      { id: 'key_points', label: 'Key Points to Cover', type: 'textarea', placeholder: 'List the main safety points you want addressed', required: false },
      { id: 'recent_incidents', label: 'Related Recent Incidents (if any)', type: 'textarea', placeholder: 'Describe any relevant incidents that prompted this talk', required: false },
    ],
  },
  {
    id: 'incident_report',
    name: 'Incident Report',
    description: 'Formal documentation of a workplace incident including root cause analysis and corrective actions.',
    icon: 'FileWarning',
    fields: [
      { id: 'incident_date', label: 'Date of Incident', type: 'date', required: true },
      { id: 'incident_time', label: 'Time of Incident', type: 'text', placeholder: '2:30 PM', required: true },
      { id: 'incident_location', label: 'Location of Incident', type: 'text', placeholder: 'Building B, East Wing, Level 2', required: true },
      { id: 'incident_type', label: 'Incident Type', type: 'select', required: true, options: [
        { value: 'injury', label: 'Worker Injury' },
        { value: 'near_miss', label: 'Near Miss' },
        { value: 'property_damage', label: 'Property Damage' },
        { value: 'environmental', label: 'Environmental' },
        { value: 'equipment_failure', label: 'Equipment Failure' },
      ]},
      { id: 'description', label: 'Incident Description', type: 'textarea', placeholder: 'Provide a detailed account of what happened', required: true },
      { id: 'persons_involved', label: 'Persons Involved', type: 'textarea', placeholder: 'Names and roles of all persons involved', required: true },
      { id: 'witnesses', label: 'Witnesses', type: 'textarea', placeholder: 'Names and contact info of witnesses', required: false },
      { id: 'immediate_actions', label: 'Immediate Actions Taken', type: 'textarea', placeholder: 'What actions were taken immediately after the incident', required: true },
    ],
  },
  {
    id: 'fall_protection',
    name: 'Fall Protection Plan',
    description: 'Site-specific fall protection procedures covering anchor points, equipment requirements, and rescue protocols.',
    icon: 'Siren',
    fields: [
      { id: 'site_name', label: 'Site Name', type: 'text', placeholder: 'Riverside Commercial Complex', required: true },
      { id: 'site_address', label: 'Site Address', type: 'text', placeholder: '456 River Road, City, State', required: true },
      { id: 'max_height', label: 'Maximum Working Height (ft)', type: 'number', placeholder: '40', required: true },
      { id: 'fall_hazard_areas', label: 'Fall Hazard Areas', type: 'textarea', placeholder: 'e.g., Roof edges, open floor holes, scaffolding', required: true },
      { id: 'anchor_points', label: 'Available Anchor Points', type: 'textarea', placeholder: 'e.g., Structural steel beams rated for 5000 lbs', required: true },
      { id: 'site_supervisor', label: 'Site Supervisor Name', type: 'text', placeholder: 'John Smith', required: true },
      { id: 'supervisor_phone', label: 'Supervisor Phone', type: 'text', placeholder: '(555) 123-4567', required: true },
      { id: 'rescue_plan', label: 'Rescue Plan Details', type: 'textarea', placeholder: 'Describe the rescue procedures for fallen workers', required: false },
    ],
  },
];

export const DOCUMENT_STATUS = {
  DRAFT: 'draft',
  FINAL: 'final',
} as const;

export type DocumentStatus = typeof DOCUMENT_STATUS[keyof typeof DOCUMENT_STATUS];

export interface Document {
  id: string;
  company_id: string;
  title: string;
  document_type: string;
  status: DocumentStatus;
  content: Record<string, unknown>;
  project_info: Record<string, string>;
  created_at: string;
  created_by: string;
  updated_at: string;
  updated_by: string;
}

/** @deprecated Use Document.content (Record<string, unknown>) instead */
export interface DocumentContent {
  sections: DocumentSection[];
}

/** @deprecated Use structured content keys instead */
export interface DocumentSection {
  id: string;
  title: string;
  content: string;
}

export interface Company {
  id: string;
  name: string;
  address: string;
  license_number: string;
  trade_type: string;
  owner_name: string;
  phone: string;
  email: string;
  ein: string | null;
  safety_officer: string | null;
  safety_officer_phone: string | null;
  logo_url: string | null;
  subscription_status: 'free' | 'active' | 'cancelled' | 'past_due' | 'paused';
  subscription_id: string | null;
  created_at: string;
  created_by: string;
  updated_at: string;
  updated_by: string;
}

export interface Subscription {
  status: 'free' | 'active' | 'cancelled' | 'past_due' | 'paused';
  plan_id: string | null;
  plan_name: string;
  max_projects: number;
  renewal_date: string | null;
  features: string[];
  is_trial?: boolean;
  trial_days_remaining?: number | null;
  trial_end_date?: string | null;
}

export const SUBSCRIPTION_TIERS = [
  {
    id: 'starter',
    name: 'Starter',
    price: 99,
    maxProjects: 2,
    features: [
      '2 projects',
      'All document generation',
      'Inspections',
      'Toolbox talks',
      'Bilingual support',
      'PDF export',
      'Email support',
    ],
  },
  {
    id: 'professional',
    name: 'Professional',
    price: 299,
    maxProjects: 8,
    features: [
      '8 projects',
      'Everything in Starter',
      'Mock OSHA Inspection',
      'Morning Brief',
      'Photo assessment',
      'Certification tracking',
      'Voice input',
      'Priority support',
    ],
  },
  {
    id: 'business',
    name: 'Business',
    price: 499,
    maxProjects: 20,
    features: [
      '20 projects',
      'Everything in Professional',
      'Prequalification automation',
      'EMR modeling',
      'Predictive scoring',
      'GC portal',
      'Dedicated account manager',
    ],
  },
  {
    id: 'enterprise',
    name: 'Enterprise',
    price: -1,
    maxProjects: -1,
    features: [
      'Unlimited projects',
      'Everything in Business',
      'Custom templates',
      'White-label branding',
      'API access',
      'SSO integration',
      'Custom integrations',
    ],
  },
] as const;

export interface Project {
  id: string;
  company_id: string;
  name: string;
  address: string;
  client_name: string;
  project_type: string;
  trade_types: string[];
  start_date: string | null;
  end_date: string | null;
  estimated_workers: number;
  description: string;
  special_hazards: string;
  nearest_hospital: string;
  emergency_contact_name: string;
  emergency_contact_phone: string;
  status: 'active' | 'completed' | 'on_hold';
  compliance_score: number;
  created_at: string;
  created_by: string;
  updated_at: string;
  updated_by: string;
}

export interface InspectionItem {
  item_id: string;
  category: string;
  description: string;
  status: 'pass' | 'fail' | 'na';
  notes: string;
  photo_url: string | null;
}

export interface Inspection {
  id: string;
  company_id: string;
  project_id: string;
  inspection_type: string;
  inspection_date: string;
  inspector_name: string;
  weather_conditions: string;
  temperature: string;
  wind_conditions: string;
  workers_on_site: number;
  items: InspectionItem[];
  overall_notes: string;
  corrective_actions_needed: string;
  overall_status: 'pass' | 'fail' | 'partial';
  gps_latitude: number | null;
  gps_longitude: number | null;
  created_at: string;
  created_by: string;
  updated_at: string;
  updated_by: string;
}

export const INSPECTION_TYPES = [
  { id: 'daily_site', name: 'Daily Site Inspection', icon: 'ClipboardCheck' },
  { id: 'scaffold', name: 'Scaffold Inspection', icon: 'Building' },
  { id: 'excavation', name: 'Excavation Inspection', icon: 'Shovel' },
  { id: 'fall_protection', name: 'Fall Protection Inspection', icon: 'ArrowDown' },
  { id: 'electrical', name: 'Electrical Inspection', icon: 'Zap' },
  { id: 'housekeeping', name: 'Housekeeping Inspection', icon: 'Brush' },
  { id: 'equipment', name: 'Equipment Inspection', icon: 'Wrench' },
  { id: 'fire_safety', name: 'Fire Safety Inspection', icon: 'Flame' },
] as const;

export const PROJECT_TYPES = [
  { value: 'commercial', label: 'Commercial' },
  { value: 'residential', label: 'Residential' },
  { value: 'industrial', label: 'Industrial' },
  { value: 'infrastructure', label: 'Infrastructure' },
  { value: 'renovation', label: 'Renovation' },
] as const;

export const TRADE_TYPES = [
  { value: 'general_contractor', label: 'General Contractor' },
  { value: 'electrical', label: 'Electrical' },
  { value: 'plumbing', label: 'Plumbing' },
  { value: 'hvac', label: 'HVAC' },
  { value: 'carpentry', label: 'Carpentry' },
  { value: 'concrete', label: 'Concrete' },
  { value: 'roofing', label: 'Roofing' },
  { value: 'painting', label: 'Painting' },
  { value: 'welding', label: 'Welding' },
  { value: 'demolition', label: 'Demolition' },
  { value: 'excavation', label: 'Excavation' },
  { value: 'steelwork', label: 'Structural Steel' },
  { value: 'masonry', label: 'Masonry' },
  { value: 'landscaping', label: 'Landscaping' },
] as const;

export interface Attendee {
  worker_name: string;
  signature_data: string;
  signed_at: string | null;
  language_preference: 'en' | 'es';
}

export interface ToolboxTalkContent {
  topic_overview: string;
  key_points: Array<{
    point_title: string;
    explanation: string;
    real_world_example?: string;
    osha_reference?: string;
  }>;
  discussion_questions: string[];
  safety_reminders: string[];
  osha_references: string[];
}

export interface ToolboxTalk {
  id: string;
  company_id: string;
  project_id: string;
  topic: string;
  scheduled_date: string;
  target_audience: string;
  target_trade: string | null;
  duration_minutes: number;
  custom_points: string;
  content_en: ToolboxTalkContent;
  content_es: ToolboxTalkContent;
  status: 'scheduled' | 'in_progress' | 'completed';
  attendees: Attendee[];
  overall_notes: string;
  presented_at: string | null;
  presented_by: string;
  created_at: string;
  created_by: string;
  updated_at: string;
  updated_by: string;
}

export interface InspectionTemplate {
  type: string;
  items: { item_id: string; category: string; description: string }[];
}

export const DAILY_SITE_INSPECTION_TEMPLATE: InspectionTemplate = {
  type: 'daily_site',
  items: [
    { item_id: 'ds_01', category: 'General Site Conditions', description: 'Site access and egress routes are clear and unobstructed' },
    { item_id: 'ds_02', category: 'General Site Conditions', description: 'Perimeter fencing and signage are intact and visible' },
    { item_id: 'ds_03', category: 'General Site Conditions', description: 'Adequate lighting in all work areas' },
    { item_id: 'ds_04', category: 'Housekeeping', description: 'Work areas are clean and free of debris' },
    { item_id: 'ds_05', category: 'Housekeeping', description: 'Waste materials are properly contained and disposed' },
    { item_id: 'ds_06', category: 'Housekeeping', description: 'Walking surfaces are clear of tripping hazards' },
    { item_id: 'ds_07', category: 'Fall Protection', description: 'Guardrails and barriers are in place at all open edges' },
    { item_id: 'ds_08', category: 'Fall Protection', description: 'Floor openings are covered or guarded' },
    { item_id: 'ds_09', category: 'Fall Protection', description: 'Workers at height have proper fall protection equipment' },
    { item_id: 'ds_10', category: 'Electrical Safety', description: 'Temporary wiring and extension cords are in good condition' },
    { item_id: 'ds_11', category: 'Electrical Safety', description: 'GFCI protection is in use for all temporary power' },
    { item_id: 'ds_12', category: 'Fire Prevention', description: 'Fire extinguishers are accessible and inspection current' },
    { item_id: 'ds_13', category: 'Fire Prevention', description: 'Hot work permits are posted where applicable' },
    { item_id: 'ds_14', category: 'PPE Compliance', description: 'All workers wearing required PPE (hard hat, vest, boots, glasses)' },
    { item_id: 'ds_15', category: 'PPE Compliance', description: 'Task-specific PPE in use (respirators, harnesses, gloves)' },
    { item_id: 'ds_16', category: 'Equipment', description: 'Equipment daily inspections completed and documented' },
    { item_id: 'ds_17', category: 'Equipment', description: 'Equipment operators have valid certifications' },
  ],
};

export interface Certification {
  id: string;
  certification_type: string;
  custom_name: string;
  issued_date: string;
  expiry_date: string | null;
  issuing_body: string;
  certificate_number: string;
  proof_document_url: string | null;
  status: 'valid' | 'expired' | 'expiring_soon';
  notes: string;
}

export interface Worker {
  id: string;
  company_id: string;
  first_name: string;
  last_name: string;
  email: string;
  phone: string;
  role: string;
  trade: string;
  language_preference: 'en' | 'es' | 'both';
  emergency_contact_name: string;
  emergency_contact_phone: string;
  hire_date: string | null;
  notes: string;
  status: 'active' | 'inactive' | 'terminated';
  certifications: Certification[];
  total_certifications: number;
  expiring_soon: number;
  expired: number;
  created_at: string;
  updated_at: string;
}

export const CERTIFICATION_TYPES = [
  { id: 'osha_10', name: 'OSHA 10-Hour', expires: false },
  { id: 'osha_30', name: 'OSHA 30-Hour', expires: false },
  { id: 'fall_protection', name: 'Fall Protection Competent Person', expires: true, typical_years: 1 },
  { id: 'scaffold_competent', name: 'Scaffold Competent Person', expires: true, typical_years: 1 },
  { id: 'confined_space', name: 'Confined Space Entry', expires: true, typical_years: 1 },
  { id: 'excavation_competent', name: 'Excavation Competent Person', expires: true, typical_years: 1 },
  { id: 'forklift_operator', name: 'Forklift / PIT Operator', expires: true, typical_years: 3 },
  { id: 'crane_operator_nccco', name: 'Crane Operator (NCCCO)', expires: true, typical_years: 5 },
  { id: 'aerial_lift', name: 'Aerial Lift / MEWP', expires: true, typical_years: 3 },
  { id: 'first_aid_cpr', name: 'First Aid / CPR / AED', expires: true, typical_years: 2 },
  { id: 'hazcom_ghs', name: 'Hazard Communication (GHS)', expires: false },
  { id: 'silica_competent', name: 'Silica Competent Person', expires: true, typical_years: 1 },
  { id: 'respiratory_fit_test', name: 'Respiratory Fit Test', expires: true, typical_years: 1 },
  { id: 'rigging_signal', name: 'Rigging / Signal Person', expires: true, typical_years: 4 },
  { id: 'electrical_safety', name: 'Electrical Safety / NFPA 70E', expires: true, typical_years: 1 },
  { id: 'flagger', name: 'Flagger Certification', expires: true, typical_years: 3 },
  { id: 'hazwoper', name: 'HAZWOPER', expires: true, typical_years: 1 },
  { id: 'fire_watch', name: 'Fire Watch', expires: true, typical_years: 1 },
  { id: 'other', name: 'Other', expires: true },
] as const;

export const WORKER_ROLES = [
  { value: 'laborer', label: 'Laborer' },
  { value: 'apprentice', label: 'Apprentice' },
  { value: 'journeyman', label: 'Journeyman' },
  { value: 'foreman', label: 'Foreman' },
  { value: 'superintendent', label: 'Superintendent' },
  { value: 'operator', label: 'Equipment Operator' },
  { value: 'safety_officer', label: 'Safety Officer' },
] as const;

export interface OshaLogEntry {
  id: string;
  case_number: number;
  employee_name: string;
  job_title: string;
  date_of_injury: string;
  where_event_occurred: string;
  description: string;
  classification: 'death' | 'days_away_from_work' | 'job_transfer_or_restriction' | 'other_recordable';
  injury_type: 'injury' | 'skin_disorder' | 'respiratory' | 'poisoning' | 'hearing_loss' | 'other_illness';
  days_away_from_work: number;
  days_of_restricted_work: number;
  died: boolean;
  privacy_case: boolean;
  created_at: string;
  updated_at: string;
}

export interface Osha300Summary {
  year: number;
  company_name: string;
  total_deaths: number;
  total_days_away: number;
  total_restricted: number;
  total_other_recordable: number;
  total_days_away_count: number;
  total_restricted_days_count: number;
  total_injuries: number;
  total_skin_disorders: number;
  total_respiratory: number;
  total_poisonings: number;
  total_hearing_loss: number;
  total_other_illnesses: number;
  trir: number;
  dart: number;
  annual_average_employees: number;
  total_hours_worked: number;
  certified_by: string;
  certified_date: string | null;
  posted: boolean;
}

export interface MockInspectionFinding {
  finding_id: string;
  severity: 'critical' | 'high' | 'medium' | 'low' | 'info';
  category: string;
  title: string;
  osha_standard: string;
  description: string;
  citation_language: string;
  corrective_action: string;
  estimated_penalty: string;
  can_auto_fix: boolean;
  auto_fix_action: string;
}

export interface MockInspectionResult {
  id: string;
  company_id: string;
  project_id: string | null;
  inspection_date: string;
  overall_score: number;
  grade: string;
  total_findings: number;
  critical_findings: number;
  high_findings: number;
  medium_findings: number;
  low_findings: number;
  findings: MockInspectionFinding[];
  documents_reviewed: number;
  training_records_reviewed: number;
  inspections_reviewed: number;
  areas_checked: string[];
  executive_summary: string;
  created_at: string;
}

export interface IdentifiedHazard {
  hazard_id: string;
  description: string;
  severity: 'imminent_danger' | 'high' | 'medium' | 'low';
  osha_standard: string;
  category: string;
  recommended_action: string;
  location_in_image: string;
}

export interface HazardReport {
  id: string;
  company_id: string;
  project_id: string;
  photo_url: string;
  description: string;
  location: string;
  gps_latitude: number | null;
  gps_longitude: number | null;
  ai_analysis: Record<string, unknown>;
  identified_hazards: IdentifiedHazard[];
  hazard_count: number;
  highest_severity: string | null;
  status: 'open' | 'in_progress' | 'corrected' | 'closed';
  corrective_action_taken: string;
  corrected_at: string | null;
  created_at: string;
  created_by: string;
}

export interface MorningBriefAlert {
  type: 'weather' | 'certification' | 'inspection' | 'toolbox_talk' | 'incident' | 'schedule';
  severity: 'critical' | 'warning' | 'info';
  title: string;
  description: string;
  action_url?: string;
  action_label?: string;
}

export interface MorningBrief {
  id: string;
  company_id: string;
  project_id: string;
  date: string;
  risk_score: number;
  risk_level: 'low' | 'moderate' | 'elevated' | 'high' | 'critical';
  weather: {
    temperature: number;
    condition: string;
    wind_speed: number;
    humidity: number;
    precipitation_chance: number;
    alerts: string[];
  };
  alerts: MorningBriefAlert[];
  recommended_toolbox_talk_topic: string;
  toolbox_talk_generated: boolean;
  summary: string;
  created_at: string;
}

export interface Incident {
  id: string;
  company_id: string;
  project_id: string;
  incident_date: string;
  incident_time: string;
  location: string;
  severity: 'fatality' | 'hospitalization' | 'medical_treatment' | 'first_aid' | 'near_miss' | 'property_damage';
  description: string;
  persons_involved: string;
  witnesses: string;
  immediate_actions_taken: string;
  root_cause: string;
  corrective_actions: string;
  status: 'reported' | 'investigating' | 'corrective_actions' | 'closed';
  osha_recordable: boolean;
  osha_reportable: boolean;
  ai_analysis: Record<string, unknown>;
  photo_urls: string[];
  created_at: string;
  created_by: string;
  updated_at: string;
}

export interface SafetyMetrics {
  total_projects: number;
  active_projects: number;
  total_inspections: number;
  inspections_this_month: number;
  total_toolbox_talks: number;
  talks_this_month: number;
  total_hazard_reports: number;
  open_hazard_reports: number;
  total_incidents: number;
  incidents_this_month: number;
  avg_compliance_score: number;
  total_workers: number;
  workers_with_expired_certs: number;
  workers_with_expiring_certs: number;
  trir: number;
  dart: number;
  last_mock_score: number | null;
  last_mock_grade: string | null;
}

export interface EmrEstimate {
  current_emr: number;
  projected_emr: number;
  premium_base: number;
  current_premium: number;
  projected_premium: number;
  potential_savings: number;
  recommendations: string[];
}

// ---- Environmental Compliance Types ----

export interface ExposureRecord {
  id: string;
  project_id: string;
  monitoring_type: string;
  monitoring_date: string;
  location: string;
  worker_name: string;
  sample_type: 'personal' | 'area';
  duration_hours: number;
  result_value: number;
  result_unit: string;
  action_level: number;
  pel: number;
  exceeds_action_level: boolean;
  exceeds_pel: boolean;
  controls_in_place: string;
  created_at: string;
}

export interface SwpppInspection {
  id: string;
  project_id: string;
  inspection_date: string;
  inspector_name: string;
  inspection_type: string;
  precipitation_last_24h: number;
  bmp_items: Array<{name: string; status: string; notes: string}>;
  corrective_actions: string;
  overall_status: 'pass' | 'fail' | 'partial';
  created_at: string;
}

export interface EnvironmentalProgram {
  id: string;
  program_type: string;
  title: string;
  content: Record<string, unknown>;
  status: 'active' | 'needs_review' | 'expired';
  last_reviewed: string | null;
  next_review_due: string | null;
  created_at: string;
}

export const ENVIRONMENTAL_PROGRAMS = [
  { id: 'silica_exposure_control', name: 'Silica Exposure Control Plan', standard: '29 CFR 1926.1153' },
  { id: 'lead_compliance', name: 'Lead Compliance Plan', standard: '29 CFR 1926.62' },
  { id: 'asbestos_management', name: 'Asbestos Management Plan', standard: '29 CFR 1926.1101' },
  { id: 'stormwater_swppp', name: 'Stormwater Pollution Prevention Plan (SWPPP)', standard: 'EPA CGP' },
  { id: 'dust_control', name: 'Dust Control Plan', standard: 'Local/State' },
  { id: 'noise_monitoring', name: 'Noise Monitoring Program', standard: '29 CFR 1926.52' },
  { id: 'hazardous_waste', name: 'Hazardous Waste Management', standard: 'EPA RCRA' },
] as const;

export const EXPOSURE_LIMITS = {
  silica: { action_level: 25, pel: 50, unit: 'ug/m3' },
  lead: { action_level: 30, pel: 50, unit: 'ug/m3' },
  asbestos: { action_level: 0.1, pel: 0.1, unit: 'f/cc' },
  noise: { action_level: 85, pel: 90, unit: 'dBA' },
} as const;

export const SWPPP_BMP_ITEMS = [
  { id: 'silt_fence', name: 'Silt Fence' },
  { id: 'inlet_protection', name: 'Inlet Protection' },
  { id: 'stabilized_entrance', name: 'Stabilized Construction Entrance' },
  { id: 'sediment_basin', name: 'Sediment Basin / Trap' },
  { id: 'erosion_blankets', name: 'Erosion Control Blankets' },
  { id: 'check_dams', name: 'Check Dams' },
  { id: 'concrete_washout', name: 'Concrete Washout Area' },
  { id: 'material_storage', name: 'Material Storage / Containment' },
  { id: 'dewatering', name: 'Dewatering Controls' },
  { id: 'vegetation', name: 'Temporary / Permanent Vegetation' },
] as const;

// ---- Equipment & Fleet Management Types ----

export interface Equipment {
  id: string;
  company_id: string;
  name: string;
  equipment_type: string;
  make: string;
  model: string;
  year: number | null;
  serial_number: string;
  vin: string;
  license_plate: string;
  current_project_id: string | null;
  status: 'active' | 'out_of_service' | 'maintenance' | 'retired';
  last_inspection_date: string | null;
  next_inspection_due: string | null;
  inspection_frequency: string;
  annual_inspection_date: string | null;
  annual_inspection_due: string | null;
  dot_inspection_date: string | null;
  dot_inspection_due: string | null;
  dot_number: string;
  required_certifications: string[];
  notes: string;
  created_at: string;
  updated_at: string;
}

export interface EquipmentInspectionLog {
  id: string;
  equipment_id: string;
  inspection_date: string;
  inspector_name: string;
  inspection_type: string;
  items: Array<{item: string; status: string; notes: string}>;
  overall_status: 'pass' | 'fail';
  deficiencies_found: string;
  out_of_service: boolean;
  created_at: string;
}

export const EQUIPMENT_TYPES = [
  { id: 'crane', name: 'Crane', icon: 'Construction' },
  { id: 'forklift', name: 'Forklift', icon: 'Forklift' },
  { id: 'aerial_lift', name: 'Aerial Lift', icon: 'ArrowUpFromLine' },
  { id: 'scissor_lift', name: 'Scissor Lift', icon: 'ArrowUpFromLine' },
  { id: 'excavator', name: 'Excavator', icon: 'Shovel' },
  { id: 'loader', name: 'Loader', icon: 'Truck' },
  { id: 'vehicle', name: 'Vehicle', icon: 'Car' },
  { id: 'generator', name: 'Generator', icon: 'Zap' },
  { id: 'scaffold_system', name: 'Scaffold System', icon: 'Building' },
  { id: 'other', name: 'Other', icon: 'Wrench' },
] as const;

export const EQUIPMENT_INSPECTION_ITEMS = {
  crane: [
    'Wire ropes and sheaves condition',
    'Hook and latch condition',
    'Load charts posted and legible',
    'Outriggers / stabilizers functional',
    'Boom and jib condition',
    'Hydraulic system - no leaks',
    'Safety devices operational (LMI, anti-two-block)',
    'Operator cab - controls and visibility',
    'Ground conditions adequate',
    'Swing / travel brakes functional',
  ],
  forklift: [
    'Tires and wheels condition',
    'Forks - not bent, cracked, or worn',
    'Mast and chains condition',
    'Hydraulic system - no leaks',
    'Horn, lights, and backup alarm',
    'Seatbelt functional',
    'Brakes - parking and service',
    'Steering responsive',
    'Overhead guard intact',
    'Load backrest extension',
  ],
  vehicle: [
    'Tires and wheels condition',
    'Lights - headlights, taillights, turn signals',
    'Horn functional',
    'Windshield wipers and washers',
    'Mirrors intact and adjusted',
    'Brakes functional',
    'Seatbelts functional',
    'Fluid levels adequate',
    'Fire extinguisher present and current',
    'First aid kit present',
  ],
  general: [
    'Overall structural integrity',
    'Guards and safety devices in place',
    'Emergency stop functional',
    'Hydraulic / pneumatic systems - no leaks',
    'Electrical connections secure',
    'Warning labels legible',
    'Operator controls functional',
    'Fluid levels adequate',
    'No visible damage or wear',
    'Documentation and tags current',
  ],
} as const;

// ---- Prequalification Types ----

export interface PrequalDocument {
  document_name: string;
  category: string;
  required: boolean;
  status: 'ready' | 'outdated' | 'missing' | 'na';
  source: string;
  source_id: string | null;
  notes: string;
}

export interface PrequalPackage {
  id: string;
  company_id: string;
  platform: 'isnetworld' | 'avetta' | 'browz' | 'generic';
  client_name: string;
  submission_deadline: string | null;
  overall_readiness: number;
  total_documents: number;
  ready_documents: number;
  outdated_documents: number;
  missing_documents: number;
  documents: PrequalDocument[];
  questionnaire: Record<string, unknown>;
  created_at: string;
}

// ---- GC/Sub Portal Types ----

export interface GcRelationship {
  id: string;
  gc_company_id: string;
  sub_company_id: string;
  gc_company_name?: string;
  sub_company_name?: string;
  project_name: string;
  status: 'active' | 'inactive' | 'pending';
  created_at: string;
}

export interface SubComplianceSummary {
  sub_company_id: string;
  sub_company_name: string;
  compliance_score: number;
  emr: number | null;
  trir: number | null;
  active_workers: number;
  expired_certifications: number;
  last_inspection_date: string | null;
  last_toolbox_talk_date: string | null;
  mock_inspection_score: number | null;
  mock_inspection_grade: string | null;
  inspection_current: boolean;
  talks_current: boolean;
  training_current: boolean;
  overall_status: 'compliant' | 'at_risk' | 'non_compliant';
}

// ---- State Compliance Types ----

export interface StateRequirement {
  id: string;
  state: string;
  requirement_name: string;
  description: string;
  state_standard: string;
  severity: 'mandatory' | 'recommended';
}

export interface StateComplianceResult {
  state: string;
  total_requirements: number;
  met_requirements: number;
  compliance_percentage: number;
  gaps: Array<{
    requirement: string;
    status: string;
    action_needed: string;
  }>;
}
