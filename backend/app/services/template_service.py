"""Static template definitions for safety document types."""

from app.models.template import FieldDefinition, SectionDefinition, Template

# -- Shared field definitions --

_SITE_ADDRESS_FIELD = FieldDefinition(
    name="site_address",
    label="Job Site Address",
    field_type="textarea",
    required=True,
    placeholder="123 Construction Ave, City, State ZIP",
    description="Full address of the construction site",
)

_PROJECT_NAME_FIELD = FieldDefinition(
    name="project_name",
    label="Project Name",
    field_type="text",
    required=True,
    placeholder="Downtown Office Renovation",
    description="Name or identifier for this project",
)

_PROJECT_START_DATE_FIELD = FieldDefinition(
    name="project_start_date",
    label="Project Start Date",
    field_type="date",
    required=True,
    placeholder="",
    description="Anticipated or actual start date",
)

_PROJECT_END_DATE_FIELD = FieldDefinition(
    name="project_end_date",
    label="Estimated Completion Date",
    field_type="date",
    required=True,
    placeholder="",
    description="Anticipated project completion date",
)

_SCOPE_OF_WORK_FIELD = FieldDefinition(
    name="scope_of_work",
    label="Scope of Work",
    field_type="textarea",
    required=True,
    placeholder="Describe the work to be performed...",
    description="Detailed description of the work activities",
)

_SITE_SUPERVISOR_FIELD = FieldDefinition(
    name="site_supervisor",
    label="Site Supervisor / Competent Person",
    field_type="text",
    required=True,
    placeholder="John Smith",
    description="Name of the designated competent person on site",
)

_EMERGENCY_CONTACT_FIELD = FieldDefinition(
    name="emergency_contact",
    label="Emergency Contact Number",
    field_type="phone",
    required=True,
    placeholder="(555) 123-4567",
    description="On-site emergency contact phone number",
)

_NUM_WORKERS_FIELD = FieldDefinition(
    name="num_workers",
    label="Number of Workers on Site",
    field_type="number",
    required=True,
    placeholder="15",
    description="Expected number of workers at the site",
)

# -- Template definitions --

SSSP_TEMPLATE = Template(
    template_id="sssp_v1",
    name="Site-Specific Safety Plan (SSSP)",
    description=(
        "A comprehensive safety plan required for most construction jobs. "
        "Covers hazard identification, emergency procedures, PPE requirements, "
        "and OSHA compliance for a specific job site."
    ),
    document_type="sssp",
    required_fields=[
        _PROJECT_NAME_FIELD,
        _SITE_ADDRESS_FIELD,
        _PROJECT_START_DATE_FIELD,
        _PROJECT_END_DATE_FIELD,
        _SCOPE_OF_WORK_FIELD,
        _SITE_SUPERVISOR_FIELD,
        _EMERGENCY_CONTACT_FIELD,
        _NUM_WORKERS_FIELD,
        FieldDefinition(
            name="general_contractor",
            label="General Contractor",
            field_type="text",
            required=False,
            placeholder="ABC Construction LLC",
            description="General contractor name if you are a subcontractor",
        ),
        FieldDefinition(
            name="nearby_hospital",
            label="Nearest Hospital / Medical Facility",
            field_type="text",
            required=True,
            placeholder="City General Hospital — 2.3 miles",
            description="Name and approximate distance of the nearest hospital",
        ),
    ],
    sections=[
        SectionDefinition(
            section_id="project_overview",
            title="Project Overview",
            description="General project information, participants, and schedule",
        ),
        SectionDefinition(
            section_id="hazard_assessment",
            title="Hazard Assessment",
            description="Identification of site-specific hazards and risk ratings",
        ),
        SectionDefinition(
            section_id="hazard_controls",
            title="Hazard Prevention and Control Measures",
            description="Engineering controls, administrative controls, and PPE for each hazard",
        ),
        SectionDefinition(
            section_id="ppe_requirements",
            title="Personal Protective Equipment Requirements",
            description="Required PPE by work area and activity",
        ),
        SectionDefinition(
            section_id="emergency_procedures",
            title="Emergency Action Plan",
            description="Procedures for fire, medical, weather, and evacuation emergencies",
        ),
        SectionDefinition(
            section_id="training_requirements",
            title="Training Requirements",
            description="Required safety training and certifications for site workers",
        ),
        SectionDefinition(
            section_id="communication_plan",
            title="Safety Communication Plan",
            description="Toolbox talks, signage, and reporting procedures",
        ),
        SectionDefinition(
            section_id="inspection_schedule",
            title="Site Inspection Schedule",
            description="Frequency and scope of safety inspections",
        ),
    ],
    osha_references=[
        "29 CFR 1926.20 — General Safety and Health Provisions",
        "29 CFR 1926.21 — Safety Training and Education",
        "29 CFR 1926.28 — Personal Protective Equipment",
        "29 CFR 1926.32 — Definitions (Competent Person)",
        "29 CFR 1926.35 — Employee Emergency Action Plans",
        "29 CFR 1926.50 — Medical Services and First Aid",
        "29 CFR 1926.52 — Occupational Noise Exposure",
        "29 CFR 1926.55 — Gases, Vapors, Fumes, Dusts, and Mists",
    ],
    estimated_generation_time_seconds=45,
)


JHA_TEMPLATE = Template(
    template_id="jha_v1",
    name="Job Hazard Analysis (JHA)",
    description=(
        "A step-by-step analysis of a specific work task to identify hazards "
        "and determine the best way to perform the job safely. "
        "Required per OSHA for each task on a construction site."
    ),
    document_type="jha",
    required_fields=[
        _PROJECT_NAME_FIELD,
        _SITE_ADDRESS_FIELD,
        FieldDefinition(
            name="task_name",
            label="Task / Activity Name",
            field_type="text",
            required=True,
            placeholder="Concrete Pouring — Foundation",
            description="The specific task being analyzed",
        ),
        FieldDefinition(
            name="task_description",
            label="Task Description",
            field_type="textarea",
            required=True,
            placeholder="Describe the task step by step...",
            description="Detailed description of the task and its steps",
        ),
        FieldDefinition(
            name="equipment_used",
            label="Equipment and Tools Used",
            field_type="textarea",
            required=True,
            placeholder="Concrete mixer, vibrator, power trowel, hand tools...",
            description="List all equipment and tools involved in this task",
        ),
        FieldDefinition(
            name="materials_used",
            label="Materials and Substances",
            field_type="textarea",
            required=False,
            placeholder="Ready-mix concrete, rebar, form release agent...",
            description="Materials and chemical substances involved",
        ),
        _SITE_SUPERVISOR_FIELD,
        FieldDefinition(
            name="date_of_analysis",
            label="Date of Analysis",
            field_type="date",
            required=True,
            placeholder="",
            description="Date this JHA is being prepared",
        ),
    ],
    sections=[
        SectionDefinition(
            section_id="task_steps",
            title="Task Steps Breakdown",
            description="Sequential steps to complete the task",
        ),
        SectionDefinition(
            section_id="hazard_identification",
            title="Hazard Identification per Step",
            description="Potential hazards for each step of the task",
        ),
        SectionDefinition(
            section_id="control_measures",
            title="Control Measures",
            description="Specific controls to eliminate or reduce each identified hazard",
        ),
        SectionDefinition(
            section_id="ppe_requirements",
            title="Required PPE",
            description="Personal protective equipment required for this task",
        ),
        SectionDefinition(
            section_id="training_required",
            title="Training and Competency Requirements",
            description="Required training before performing this task",
        ),
        SectionDefinition(
            section_id="emergency_procedures",
            title="Task-Specific Emergency Procedures",
            description="What to do if an incident occurs during this task",
        ),
    ],
    osha_references=[
        "29 CFR 1926.20(b) — Accident Prevention Programs",
        "29 CFR 1926.21(b)(2) — Employee Training for Hazardous Conditions",
        "OSHA 3071 — Job Hazard Analysis (Guidance Document)",
        "29 CFR 1926.28 — Personal Protective Equipment",
    ],
    estimated_generation_time_seconds=30,
)


TOOLBOX_TALK_TEMPLATE = Template(
    template_id="toolbox_talk_v1",
    name="Toolbox Talk Record",
    description=(
        "Weekly safety meeting documentation covering a specific safety topic. "
        "Used to record attendance and discussion points for OSHA compliance."
    ),
    document_type="toolbox_talk",
    required_fields=[
        _PROJECT_NAME_FIELD,
        _SITE_ADDRESS_FIELD,
        FieldDefinition(
            name="talk_date",
            label="Date of Toolbox Talk",
            field_type="date",
            required=True,
            placeholder="",
            description="Date the toolbox talk will be or was conducted",
        ),
        FieldDefinition(
            name="topic",
            label="Safety Topic",
            field_type="select",
            required=True,
            placeholder="",
            options=[
                "Fall Protection",
                "Electrical Safety",
                "Trenching and Excavation",
                "Scaffold Safety",
                "Heat Illness Prevention",
                "Cold Stress Prevention",
                "Hazard Communication (HazCom)",
                "Lockout/Tagout (LOTO)",
                "Confined Space Entry",
                "Fire Prevention",
                "Hand and Power Tool Safety",
                "Crane and Rigging Safety",
                "Personal Protective Equipment",
                "Housekeeping and Slip/Trip/Fall Prevention",
                "Silica Dust Exposure",
                "Lead Safety",
                "Ladder Safety",
                "Struck-By Hazards",
                "Caught-In/Between Hazards",
                "Other",
            ],
            description="Select the safety topic for this talk",
        ),
        FieldDefinition(
            name="custom_topic",
            label="Custom Topic (if Other selected)",
            field_type="text",
            required=False,
            placeholder="Describe the custom topic...",
            description="Specify the topic if 'Other' was selected above",
        ),
        FieldDefinition(
            name="presenter_name",
            label="Presenter Name",
            field_type="text",
            required=True,
            placeholder="Jane Doe",
            description="Person conducting the toolbox talk",
        ),
    ],
    sections=[
        SectionDefinition(
            section_id="topic_overview",
            title="Topic Overview",
            description="Introduction and importance of the safety topic",
        ),
        SectionDefinition(
            section_id="key_points",
            title="Key Safety Points",
            description="Main safety points to discuss with the crew",
        ),
        SectionDefinition(
            section_id="osha_requirements",
            title="Relevant OSHA Requirements",
            description="Applicable OSHA standards and requirements",
        ),
        SectionDefinition(
            section_id="discussion_questions",
            title="Discussion Questions",
            description="Questions to engage the crew in safety discussion",
        ),
        SectionDefinition(
            section_id="attendance_record",
            title="Attendance Record",
            description="Sign-in sheet for attendees",
            ai_generated=False,
        ),
    ],
    osha_references=[
        "29 CFR 1926.21(b)(2) — Safety Training and Education",
        "29 CFR 1926.20(b)(1) — Accident Prevention Programs",
        "29 CFR 1903.2(a)(1) — Posting of OSHA Notices",
    ],
    estimated_generation_time_seconds=20,
)


INCIDENT_REPORT_TEMPLATE = Template(
    template_id="incident_report_v1",
    name="Incident Report",
    description=(
        "Required within 24 hours of any workplace incident. Documents the event, "
        "injuries, root cause analysis, and corrective actions."
    ),
    document_type="incident_report",
    required_fields=[
        _PROJECT_NAME_FIELD,
        _SITE_ADDRESS_FIELD,
        FieldDefinition(
            name="incident_date",
            label="Date of Incident",
            field_type="date",
            required=True,
            placeholder="",
            description="Date the incident occurred",
        ),
        FieldDefinition(
            name="incident_time",
            label="Time of Incident",
            field_type="text",
            required=True,
            placeholder="2:30 PM",
            description="Approximate time the incident occurred",
        ),
        FieldDefinition(
            name="incident_type",
            label="Type of Incident",
            field_type="select",
            required=True,
            placeholder="",
            options=[
                "Near Miss",
                "First Aid",
                "Medical Treatment",
                "Lost Time Injury",
                "Fatality",
                "Property Damage",
                "Environmental Release",
                "Fire",
                "Equipment Failure",
            ],
            description="Classification of the incident",
        ),
        FieldDefinition(
            name="incident_description",
            label="Description of Incident",
            field_type="textarea",
            required=True,
            placeholder="Describe what happened in detail...",
            description="Detailed narrative of the incident",
        ),
        FieldDefinition(
            name="injured_person_name",
            label="Injured Person Name (if applicable)",
            field_type="text",
            required=False,
            placeholder="",
            description="Name of any injured person",
        ),
        FieldDefinition(
            name="injury_description",
            label="Description of Injury (if applicable)",
            field_type="textarea",
            required=False,
            placeholder="Laceration to left forearm, approximately 3 inches...",
            description="Nature and extent of any injuries",
        ),
        FieldDefinition(
            name="witnesses",
            label="Witness Names",
            field_type="textarea",
            required=False,
            placeholder="List witness names, one per line...",
            description="Names of any witnesses to the incident",
        ),
        FieldDefinition(
            name="immediate_actions_taken",
            label="Immediate Actions Taken",
            field_type="textarea",
            required=True,
            placeholder="First aid administered, area secured, supervisor notified...",
            description="What was done immediately after the incident",
        ),
    ],
    sections=[
        SectionDefinition(
            section_id="incident_summary",
            title="Incident Summary",
            description="Concise summary of the incident for management review",
        ),
        SectionDefinition(
            section_id="timeline",
            title="Timeline of Events",
            description="Chronological sequence of events leading to and following the incident",
        ),
        SectionDefinition(
            section_id="root_cause_analysis",
            title="Root Cause Analysis",
            description="Investigation findings and contributing factors",
        ),
        SectionDefinition(
            section_id="corrective_actions",
            title="Corrective Actions",
            description="Immediate and long-term corrective actions with assigned responsibilities",
        ),
        SectionDefinition(
            section_id="osha_reporting",
            title="OSHA Reporting Requirements",
            description="Whether OSHA reporting is required and what has been filed",
        ),
        SectionDefinition(
            section_id="prevention_measures",
            title="Preventive Measures",
            description="Steps to prevent recurrence of similar incidents",
        ),
    ],
    osha_references=[
        "29 CFR 1904.7 — General Recording Criteria for Cases",
        "29 CFR 1904.39 — Reporting Fatalities, Hospitalizations, Amputations, and Eye Loss",
        "29 CFR 1926.20(b)(1) — Accident Prevention Programs",
        "29 CFR 1926.50(a) — Duty to Provide Medical Services and First Aid",
    ],
    estimated_generation_time_seconds=30,
)


FALL_PROTECTION_TEMPLATE = Template(
    template_id="fall_protection_v1",
    name="Fall Protection Plan",
    description=(
        "Required for any construction work performed at heights of 6 feet or more. "
        "Details fall hazards, protection systems, rescue procedures, "
        "and worker training requirements."
    ),
    document_type="fall_protection",
    required_fields=[
        _PROJECT_NAME_FIELD,
        _SITE_ADDRESS_FIELD,
        _PROJECT_START_DATE_FIELD,
        _PROJECT_END_DATE_FIELD,
        _SCOPE_OF_WORK_FIELD,
        _SITE_SUPERVISOR_FIELD,
        _NUM_WORKERS_FIELD,
        FieldDefinition(
            name="max_working_height",
            label="Maximum Working Height (feet)",
            field_type="number",
            required=True,
            placeholder="24",
            description="Maximum height at which work will be performed",
        ),
        FieldDefinition(
            name="work_areas_at_height",
            label="Work Areas at Height",
            field_type="textarea",
            required=True,
            placeholder="Roof edge work, open floor holes, elevated platforms...",
            description="Describe all areas where workers will be at height",
        ),
        FieldDefinition(
            name="fall_protection_systems",
            label="Fall Protection Systems Available",
            field_type="textarea",
            required=True,
            placeholder="Guardrails, personal fall arrest systems, safety nets...",
            description="List all fall protection systems that will be used",
        ),
        FieldDefinition(
            name="anchor_points",
            label="Anchor Point Descriptions",
            field_type="textarea",
            required=True,
            placeholder="Steel I-beam tie-offs rated at 5,000 lbs per worker...",
            description="Describe anchor points and their rated capacities",
        ),
    ],
    sections=[
        SectionDefinition(
            section_id="site_assessment",
            title="Site Fall Hazard Assessment",
            description="Identification of all fall hazards at the work site",
        ),
        SectionDefinition(
            section_id="protection_systems",
            title="Fall Protection Systems",
            description="Detailed description of fall protection methods for each hazard",
        ),
        SectionDefinition(
            section_id="equipment_inspection",
            title="Equipment Inspection Requirements",
            description="Inspection schedules and criteria for fall protection equipment",
        ),
        SectionDefinition(
            section_id="rescue_plan",
            title="Fall Rescue Procedures",
            description="Procedures for rescuing a worker after a fall arrest",
        ),
        SectionDefinition(
            section_id="training_requirements",
            title="Fall Protection Training",
            description="Required training for all workers exposed to fall hazards",
        ),
        SectionDefinition(
            section_id="enforcement",
            title="Enforcement and Disciplinary Procedures",
            description="How fall protection compliance will be enforced",
        ),
    ],
    osha_references=[
        "29 CFR 1926.501 — Duty to Have Fall Protection",
        "29 CFR 1926.502 — Fall Protection Systems Criteria and Practices",
        "29 CFR 1926.503 — Training Requirements",
        "29 CFR 1926.500 — Scope, Application, and Definitions",
        "29 CFR 1926.502(d) — Personal Fall Arrest Systems",
        "29 CFR 1926.502(k) — Fall Protection Plan (for infeasible conventional protection)",
    ],
    estimated_generation_time_seconds=35,
)


# -- Template registry --

_TEMPLATES: dict[str, Template] = {
    "sssp": SSSP_TEMPLATE,
    "jha": JHA_TEMPLATE,
    "toolbox_talk": TOOLBOX_TALK_TEMPLATE,
    "incident_report": INCIDENT_REPORT_TEMPLATE,
    "fall_protection": FALL_PROTECTION_TEMPLATE,
}


class TemplateService:
    """Provides access to static document template definitions."""

    def list_templates(self) -> list[Template]:
        """Return all available templates.

        Returns:
            A list of all Template definitions.
        """
        return list(_TEMPLATES.values())

    def get_template(self, document_type: str) -> Template | None:
        """Get a specific template by document type.

        Args:
            document_type: The document type key (e.g., 'sssp', 'jha').

        Returns:
            The Template if found, None otherwise.
        """
        return _TEMPLATES.get(document_type)

    def get_template_fields(self, document_type: str) -> list[dict] | None:
        """Get the required fields for a template as dicts.

        Args:
            document_type: The document type key.

        Returns:
            A list of field definition dicts, or None if the template is not found.
        """
        template = _TEMPLATES.get(document_type)
        if template is None:
            return None
        return [field.model_dump() for field in template.required_fields]
