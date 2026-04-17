import { toast } from 'sonner';
import { DEMO_DOCUMENTS, DEMO_COMPANY, DEMO_STATS, DEMO_PROJECTS, DEMO_INSPECTIONS, DEMO_TOOLBOX_TALKS, DEMO_WORKERS, DEMO_OSHA_ENTRIES, DEMO_OSHA_SUMMARY, DEMO_MOCK_INSPECTION, DEMO_MOCK_INSPECTION_RESULTS, DEMO_HAZARD_REPORTS, DEMO_MORNING_BRIEF, DEMO_MORNING_BRIEF_HISTORY, DEMO_INCIDENTS, DEMO_ANALYTICS, DEMO_PREQUAL_PACKAGES, DEMO_PREQUAL_REQUIREMENTS, DEMO_GC_RELATIONSHIPS, DEMO_SUB_COMPLIANCE, DEMO_AVAILABLE_STATES, DEMO_STATE_REQUIREMENTS, DEMO_STATE_COMPLIANCE_RESULTS, DEMO_ENVIRONMENTAL_PROGRAMS, DEMO_EXPOSURE_RECORDS, DEMO_SWPPP_INSPECTIONS, DEMO_EQUIPMENT, DEMO_EQUIPMENT_INSPECTIONS, DEMO_PROJECT_ASSIGNMENTS, DEMO_DAILY_LOGS } from './demo-data';
import { DAILY_SITE_INSPECTION_TEMPLATE, CERTIFICATION_TYPES } from './constants';
import type { Certification } from './constants';

export const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

interface ApiOptions extends Omit<RequestInit, 'body'> {
  body?: unknown;
}

class ApiError extends Error {
  status: number;
  data: unknown;

  constructor(status: number, message: string, data?: unknown) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.data = data;
  }
}

export function isDemoMode(): boolean {
  return sessionStorage.getItem('kerf_demo') === 'true';
}

// Demo mode API responses — kept for offline fallback.
// Exported so it remains available if the backend is unreachable.
export function handleDemoRequest<T>(endpoint: string, method: string, body?: unknown): T {
  // ---- Daily Log Routes ----

  // Submit daily log
  const dailyLogSubmitMatch = endpoint.match(/\/me\/projects\/[^/]+\/daily-logs\/([^/]+)\/submit$/);
  if (dailyLogSubmitMatch && method === 'POST') {
    const idx = DEMO_DAILY_LOGS.findIndex(d => d.id === dailyLogSubmitMatch[1]);
    if (idx !== -1) {
      DEMO_DAILY_LOGS[idx].status = 'submitted';
      DEMO_DAILY_LOGS[idx].submitted_at = new Date().toISOString();
      DEMO_DAILY_LOGS[idx].submitted_by = 'demo_user_001';
      DEMO_DAILY_LOGS[idx].updated_at = new Date().toISOString();
      return DEMO_DAILY_LOGS[idx] as T;
    }
    return {} as T;
  }

  // Approve daily log
  const dailyLogApproveMatch = endpoint.match(/\/me\/projects\/[^/]+\/daily-logs\/([^/]+)\/approve$/);
  if (dailyLogApproveMatch && method === 'POST') {
    const idx = DEMO_DAILY_LOGS.findIndex(d => d.id === dailyLogApproveMatch[1]);
    if (idx !== -1) {
      DEMO_DAILY_LOGS[idx].status = 'approved';
      DEMO_DAILY_LOGS[idx].approved_at = new Date().toISOString();
      DEMO_DAILY_LOGS[idx].approved_by = 'demo_user_001';
      DEMO_DAILY_LOGS[idx].updated_at = new Date().toISOString();
      return DEMO_DAILY_LOGS[idx] as T;
    }
    return {} as T;
  }

  // Single daily log — GET, PATCH, DELETE
  const dailyLogMatch = endpoint.match(/\/me\/projects\/[^/]+\/daily-logs\/([^/?]+)$/);
  if (dailyLogMatch && (method === 'GET' || method === 'PATCH' || method === 'DELETE')) {
    if (method === 'DELETE') {
      const idx = DEMO_DAILY_LOGS.findIndex(d => d.id === dailyLogMatch[1]);
      if (idx !== -1) DEMO_DAILY_LOGS.splice(idx, 1);
      return undefined as T;
    }
    if (method === 'PATCH') {
      const idx = DEMO_DAILY_LOGS.findIndex(d => d.id === dailyLogMatch[1]);
      if (idx !== -1) {
        const payload = body as Record<string, unknown>;
        DEMO_DAILY_LOGS[idx] = { ...DEMO_DAILY_LOGS[idx], ...payload, updated_at: new Date().toISOString() } as typeof DEMO_DAILY_LOGS[0];
        return DEMO_DAILY_LOGS[idx] as T;
      }
    }
    const log = DEMO_DAILY_LOGS.find(d => d.id === dailyLogMatch[1]);
    if (log) return log as T;
    return DEMO_DAILY_LOGS[0] as T;
  }

  // Daily log list
  const dailyLogListMatch = endpoint.match(/\/me\/projects\/([^/]+)\/daily-logs(?:\?|$)/);
  if (dailyLogListMatch && method === 'GET') {
    const projectId = dailyLogListMatch[1];
    const url = new URL(endpoint, 'http://localhost');
    const statusFilter = url.searchParams.get('status');
    let items = DEMO_DAILY_LOGS.filter(d => d.project_id === projectId && !d.deleted);
    if (statusFilter) items = items.filter(d => d.status === statusFilter);
    return { daily_logs: items, total: items.length } as T;
  }

  // Create daily log
  const dailyLogCreateMatch = endpoint.match(/\/me\/projects\/([^/]+)\/daily-logs/);
  if (dailyLogCreateMatch && method === 'POST') {
    const payload = body as Record<string, unknown>;
    const newLog = {
      id: 'dlog_' + Date.now(),
      project_id: dailyLogCreateMatch[1],
      company_id: 'demo_company_001',
      log_date: (payload.log_date as string) || new Date().toISOString().split('T')[0],
      superintendent_name: (payload.superintendent_name as string) || '',
      status: 'draft' as const,
      weather: (payload.weather as typeof DEMO_DAILY_LOGS[0]['weather']) || { conditions: '', temperature_high: '', temperature_low: '', wind: '', precipitation: '' },
      workers_on_site: (payload.workers_on_site as number) || 0,
      work_performed: (payload.work_performed as string) || '',
      materials_delivered: (payload.materials_delivered as typeof DEMO_DAILY_LOGS[0]['materials_delivered']) || [],
      delays: (payload.delays as typeof DEMO_DAILY_LOGS[0]['delays']) || [],
      visitors: (payload.visitors as typeof DEMO_DAILY_LOGS[0]['visitors']) || [],
      safety_incidents: (payload.safety_incidents as string) || '',
      equipment_used: (payload.equipment_used as string) || '',
      notes: (payload.notes as string) || '',
      inspections_summary: [],
      toolbox_talks_summary: [],
      incidents_summary: [],
      created_at: new Date().toISOString(),
      created_by: 'demo_user_001',
      updated_at: new Date().toISOString(),
      updated_by: 'demo_user_001',
      submitted_at: null,
      submitted_by: null,
      approved_at: null,
      approved_by: null,
      deleted: false,
    };
    DEMO_DAILY_LOGS.unshift(newLog as typeof DEMO_DAILY_LOGS[0]);
    return newLog as T;
  }

  // ---- Voice Routes ----

  // Transcribe audio
  if (endpoint.match(/\/me\/voice\/transcribe/) && method === 'POST') {
    return {
      transcript: 'Scaffolding on level 2 looks good, guardrails in place, planking secure. Moving to electrical — I see an open junction box near the east stairwell, no cover plate. Housekeeping is good, walkways are clear.',
    } as T;
  }

  // Parse inspection from transcript
  if (endpoint.match(/\/me\/voice\/parse-inspection/) && method === 'POST') {
    return {
      items: [
        { item_id: 'ds_01', category: 'Scaffolding', description: 'Scaffolding on level 2', status: 'pass', notes: 'Guardrails in place, planking secure' },
        { item_id: 'ds_02', category: 'Electrical', description: 'Junction box near east stairwell', status: 'fail', notes: 'Open junction box, no cover plate' },
        { item_id: 'ds_03', category: 'Housekeeping', description: 'Walkways and work areas', status: 'pass', notes: 'Walkways clear' },
      ],
      notes: 'Level 2 inspection complete. One electrical issue found.',
      corrective_actions: 'Install cover plate on junction box near east stairwell before end of shift.',
    } as T;
  }

  // Parse incident from transcript
  if (endpoint.match(/\/me\/voice\/parse-incident/) && method === 'POST') {
    return {
      location: 'Level 3, near the HVAC shaft',
      severity: 'near_miss',
      description: 'A wrench fell approximately 15 feet from the scaffold platform. No workers were in the drop zone at the time. The tool was not tethered.',
      persons_involved: 'James Wilson (scaffold crew)',
      witnesses: 'Maria Rodriguez (site supervisor)',
      immediate_actions_taken: 'Area cordoned off, tool tethering policy reviewed with scaffold crew, all tools inspected for tethering.',
    } as T;
  }

  // ---- Environmental Compliance Routes ----

  // Environmental programs list
  if (endpoint.match(/\/me\/environmental\/programs/) && method === 'GET') {
    return { programs: DEMO_ENVIRONMENTAL_PROGRAMS, total: DEMO_ENVIRONMENTAL_PROGRAMS.length } as T;
  }

  // Create environmental program
  if (endpoint.match(/\/me\/environmental\/programs/) && method === 'POST') {
    const payload = body as Record<string, unknown>;
    const newProg = {
      id: 'env_prog_' + Date.now(),
      program_type: (payload.program_type as string) || '',
      title: (payload.title as string) || '',
      content: (payload.content as Record<string, unknown>) || {},
      status: 'active' as const,
      last_reviewed: new Date().toISOString().split('T')[0],
      next_review_due: null,
      created_at: new Date().toISOString(),
    };
    DEMO_ENVIRONMENTAL_PROGRAMS.push(newProg);
    return newProg as T;
  }

  // Exposure records (project-scoped)
  if (endpoint.match(/\/me\/projects\/[^/]+\/exposure-records(?!\/)/) && method === 'GET') {
    return { records: DEMO_EXPOSURE_RECORDS, total: DEMO_EXPOSURE_RECORDS.length } as T;
  }

  // Create exposure record (project-scoped)
  if (endpoint.match(/\/me\/projects\/[^/]+\/exposure-records/) && method === 'POST') {
    const payload = body as Record<string, unknown>;
    const newRec = {
      id: 'exp_' + Date.now(),
      project_id: (payload.project_id as string) || '',
      monitoring_type: (payload.monitoring_type as string) || '',
      monitoring_date: (payload.monitoring_date as string) || new Date().toISOString().split('T')[0],
      location: (payload.location as string) || '',
      worker_name: (payload.worker_name as string) || '',
      sample_type: (payload.sample_type as string) || 'personal',
      duration_hours: (payload.duration_hours as number) || 8,
      result_value: (payload.result_value as number) || 0,
      result_unit: (payload.result_unit as string) || '',
      action_level: (payload.action_level as number) || 0,
      pel: (payload.pel as number) || 0,
      exceeds_action_level: ((payload.result_value as number) || 0) > ((payload.action_level as number) || 0),
      exceeds_pel: ((payload.result_value as number) || 0) > ((payload.pel as number) || 0),
      controls_in_place: (payload.controls_in_place as string) || '',
      created_at: new Date().toISOString(),
    };
    DEMO_EXPOSURE_RECORDS.unshift(newRec as typeof DEMO_EXPOSURE_RECORDS[0]);
    return newRec as T;
  }

  // Exposure summary (project-scoped)
  if (endpoint.match(/\/me\/projects\/[^/]+\/exposure-records\/summary/) && method === 'GET') {
    const grouped: Record<string, typeof DEMO_EXPOSURE_RECORDS> = {};
    for (const r of DEMO_EXPOSURE_RECORDS) {
      (grouped[r.monitoring_type] ??= []).push(r);
    }
    const summaries = Object.entries(grouped).map(([agent, recs]) => ({
      agent_name: agent,
      total_samples: recs.length,
      above_action_level: recs.filter(r => r.exceeds_action_level).length,
      above_pel: recs.filter(r => r.exceeds_pel).length,
      average_exposure: recs.reduce((s, r) => s + r.result_value, 0) / recs.length,
    }));
    return { summaries, total_samples: DEMO_EXPOSURE_RECORDS.length } as T;
  }

  // SWPPP inspections (project-scoped)
  if (endpoint.match(/\/me\/projects\/[^/]+\/swppp-inspections/) && method === 'GET') {
    return { inspections: DEMO_SWPPP_INSPECTIONS, total: DEMO_SWPPP_INSPECTIONS.length } as T;
  }

  // Create SWPPP inspection (project-scoped)
  if (endpoint.match(/\/me\/projects\/[^/]+\/swppp-inspections/) && method === 'POST') {
    const payload = body as Record<string, unknown>;
    const bmpItems = (payload.bmp_items as Array<{name: string; status: string; notes: string}>) || [];
    const failCount = bmpItems.filter(i => i.status === 'fail').length;
    const newInsp = {
      id: 'swppp_' + Date.now(),
      project_id: (payload.project_id as string) || '',
      inspection_date: (payload.inspection_date as string) || new Date().toISOString().split('T')[0],
      inspector_name: (payload.inspector_name as string) || '',
      inspection_type: (payload.inspection_type as string) || 'Weekly routine',
      precipitation_last_24h: (payload.precipitation_last_24h as number) || 0,
      bmp_items: bmpItems,
      corrective_actions: (payload.corrective_actions as string) || '',
      overall_status: failCount === 0 ? 'pass' : failCount === bmpItems.length ? 'fail' : 'partial',
      created_at: new Date().toISOString(),
    };
    DEMO_SWPPP_INSPECTIONS.unshift(newInsp as typeof DEMO_SWPPP_INSPECTIONS[0]);
    return newInsp as T;
  }

  // Environmental compliance overview
  if (endpoint.match(/\/me\/environmental\/compliance-status/) && method === 'GET') {
    const programsNeedReview = DEMO_ENVIRONMENTAL_PROGRAMS.filter(p => p.status === 'needs_review').length;
    return {
      overall_status: programsNeedReview > 0 ? 'needs_attention' : 'compliant',
      areas: DEMO_ENVIRONMENTAL_PROGRAMS.map(p => ({
        area: p.program_type,
        status: p.status,
        details: p.title,
      })),
      total_programs: DEMO_ENVIRONMENTAL_PROGRAMS.length,
    } as T;
  }

  // ---- Equipment & Fleet Routes ----

  // Equipment inspection logs for a piece of equipment
  const equipInspMatch = endpoint.match(/\/me\/equipment\/([^/]+)\/inspections$/);
  if (equipInspMatch && method === 'GET') {
    const logs = DEMO_EQUIPMENT_INSPECTIONS.filter(i => i.equipment_id === equipInspMatch[1]);
    return { logs, total: logs.length } as T;
  }

  // Create equipment inspection
  const equipInspCreateMatch = endpoint.match(/\/me\/equipment\/([^/]+)\/inspections$/);
  if (equipInspCreateMatch && method === 'POST') {
    const payload = body as Record<string, unknown>;
    const items = (payload.items as Array<{item: string; status: string; notes: string}>) || [];
    const failCount = items.filter(i => i.status === 'fail').length;
    const newLog = {
      id: 'equip_insp_' + Date.now(),
      equipment_id: equipInspCreateMatch[1],
      inspection_date: (payload.inspection_date as string) || new Date().toISOString().split('T')[0],
      inspector_name: (payload.inspector_name as string) || '',
      inspection_type: (payload.inspection_type as string) || 'Routine',
      items,
      overall_status: failCount > 0 ? 'fail' : 'pass',
      deficiencies_found: (payload.deficiencies_found as string) || '',
      out_of_service: (payload.out_of_service as boolean) || false,
      created_at: new Date().toISOString(),
    };
    DEMO_EQUIPMENT_INSPECTIONS.unshift(newLog as typeof DEMO_EQUIPMENT_INSPECTIONS[0]);
    // Update equipment last inspection date
    const eIdx = DEMO_EQUIPMENT.findIndex(e => e.id === equipInspCreateMatch[1]);
    if (eIdx !== -1) {
      DEMO_EQUIPMENT[eIdx].last_inspection_date = newLog.inspection_date;
      DEMO_EQUIPMENT[eIdx].updated_at = new Date().toISOString();
      if (newLog.out_of_service) {
        DEMO_EQUIPMENT[eIdx].status = 'out_of_service';
      }
    }
    return newLog as T;
  }

  // Equipment summary
  if (endpoint.match(/\/me\/equipment\/summary/) && method === 'GET') {
    const total = DEMO_EQUIPMENT.length;
    const now = new Date();
    const overdueInsp = DEMO_EQUIPMENT.filter(e => e.next_inspection_due && new Date(e.next_inspection_due) < now).length;
    const byType: Record<string, number> = {};
    const byStatus: Record<string, number> = {};
    for (const e of DEMO_EQUIPMENT) {
      byType[e.equipment_type] = (byType[e.equipment_type] || 0) + 1;
      byStatus[e.status] = (byStatus[e.status] || 0) + 1;
    }
    return { total_equipment: total, by_type: byType, by_status: byStatus, overdue_inspections: overdueInsp, overdue_maintenance: 0 } as T;
  }

  // DOT compliance
  if (endpoint.match(/\/me\/equipment\/dot-compliance/) && method === 'GET') {
    const vehicles = DEMO_EQUIPMENT.filter(e => e.dot_number).map(v => ({
      equipment_id: v.id,
      name: v.name,
      dot_number: v.dot_number,
      last_inspection_date: v.dot_inspection_date,
      next_inspection_due: v.dot_inspection_due,
      status: v.dot_inspection_due && new Date(v.dot_inspection_due) > new Date() ? 'compliant' : 'overdue',
    }));
    const compliant = vehicles.filter(v => v.status === 'compliant').length;
    const overdue = vehicles.filter(v => v.status === 'overdue').length;
    return { vehicles, total: vehicles.length, compliant, overdue, missing: 0 } as T;
  }

  // Overdue inspections
  if (endpoint.match(/\/me\/equipment\/overdue-inspections/) && method === 'GET') {
    const now = new Date();
    const overdue = DEMO_EQUIPMENT
      .filter(e => e.next_inspection_due && new Date(e.next_inspection_due) < now)
      .map(e => ({
        equipment_id: e.id,
        name: e.name,
        equipment_type: e.equipment_type,
        last_inspection_date: e.last_inspection_date,
        next_inspection_due: e.next_inspection_due,
        days_overdue: Math.floor((now.getTime() - new Date(e.next_inspection_due!).getTime()) / (1000 * 60 * 60 * 24)),
      }));
    return { equipment: overdue, total: overdue.length } as T;
  }

  // Single equipment — GET, PATCH, DELETE
  const equipMatch = endpoint.match(/\/me\/equipment\/([^/?]+)$/);
  if (equipMatch && (method === 'GET' || method === 'PATCH' || method === 'DELETE')) {
    if (method === 'DELETE') {
      const idx = DEMO_EQUIPMENT.findIndex(e => e.id === equipMatch[1]);
      if (idx !== -1) DEMO_EQUIPMENT.splice(idx, 1);
      return undefined as T;
    }
    if (method === 'PATCH') {
      const idx = DEMO_EQUIPMENT.findIndex(e => e.id === equipMatch[1]);
      if (idx !== -1) {
        const payload = body as Record<string, unknown>;
        DEMO_EQUIPMENT[idx] = { ...DEMO_EQUIPMENT[idx], ...payload, updated_at: new Date().toISOString() } as typeof DEMO_EQUIPMENT[0];
        return DEMO_EQUIPMENT[idx] as T;
      }
    }
    const equip = DEMO_EQUIPMENT.find(e => e.id === equipMatch[1]);
    if (equip) return equip as T;
    return DEMO_EQUIPMENT[0] as T;
  }

  // Equipment list
  if (endpoint.match(/\/me\/equipment/) && method === 'GET') {
    const url = new URL(endpoint, 'http://localhost');
    const status = url.searchParams.get('status');
    const type = url.searchParams.get('type');
    const projectId = url.searchParams.get('project_id');
    let items = [...DEMO_EQUIPMENT];
    if (status) items = items.filter(e => e.status === status);
    if (type) items = items.filter(e => e.equipment_type === type);
    if (projectId) items = items.filter(e => e.current_project_id === projectId);
    return { equipment: items, total: items.length } as T;
  }

  // Create equipment
  if (endpoint.match(/\/me\/equipment/) && method === 'POST') {
    const payload = body as Record<string, unknown>;
    const newEquip = {
      id: 'equip_' + Date.now(),
      company_id: 'demo_company_001',
      name: (payload.name as string) || '',
      equipment_type: (payload.equipment_type as string) || 'other',
      make: (payload.make as string) || '',
      model: (payload.model as string) || '',
      year: (payload.year as number) || null,
      serial_number: (payload.serial_number as string) || '',
      vin: (payload.vin as string) || '',
      license_plate: (payload.license_plate as string) || '',
      current_project_id: (payload.current_project_id as string) || null,
      status: 'active' as const,
      last_inspection_date: null,
      next_inspection_due: null,
      inspection_frequency: (payload.inspection_frequency as string) || 'Monthly',
      annual_inspection_date: null,
      annual_inspection_due: null,
      dot_inspection_date: null,
      dot_inspection_due: null,
      dot_number: (payload.dot_number as string) || '',
      required_certifications: (payload.required_certifications as string[]) || [],
      notes: (payload.notes as string) || '',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };
    DEMO_EQUIPMENT.unshift(newEquip as typeof DEMO_EQUIPMENT[0]);
    return newEquip as T;
  }

  // ---- Project Assignments ----

  // Single assignment GET/PATCH/DELETE
  const asgnMatch = endpoint.match(/\/me\/assignments\/([^/?]+)$/);
  if (asgnMatch && (method === 'GET' || method === 'PATCH' || method === 'DELETE')) {
    if (method === 'DELETE') {
      const idx = DEMO_PROJECT_ASSIGNMENTS.findIndex(a => a.id === asgnMatch[1]);
      if (idx !== -1) DEMO_PROJECT_ASSIGNMENTS.splice(idx, 1);
      return undefined as T;
    }
    if (method === 'PATCH') {
      const payload = body as Record<string, unknown>;
      const idx = DEMO_PROJECT_ASSIGNMENTS.findIndex(a => a.id === asgnMatch[1]);
      if (idx !== -1) {
        DEMO_PROJECT_ASSIGNMENTS[idx] = { ...DEMO_PROJECT_ASSIGNMENTS[idx], ...payload, updated_at: new Date().toISOString() } as typeof DEMO_PROJECT_ASSIGNMENTS[0];
        return DEMO_PROJECT_ASSIGNMENTS[idx] as T;
      }
    }
    const asgn = DEMO_PROJECT_ASSIGNMENTS.find(a => a.id === asgnMatch[1]);
    if (asgn) return asgn as T;
    return DEMO_PROJECT_ASSIGNMENTS[0] as T;
  }

  // List assignments (global or per-project)
  if ((endpoint.match(/\/me\/assignments/) || endpoint.match(/\/me\/projects\/[^/]+\/assignments/)) && method === 'GET') {
    const url = new URL(endpoint, 'http://localhost');
    const projectId = url.searchParams.get('project_id') || endpoint.match(/\/me\/projects\/([^/]+)\/assignments/)?.[1];
    const resourceType = url.searchParams.get('resource_type');
    const resourceId = url.searchParams.get('resource_id');
    const statusFilter = url.searchParams.get('status');
    let items = [...DEMO_PROJECT_ASSIGNMENTS];
    if (projectId) items = items.filter(a => a.project_id === projectId);
    if (resourceType) items = items.filter(a => a.resource_type === resourceType);
    if (resourceId) items = items.filter(a => a.resource_id === resourceId);
    if (statusFilter) items = items.filter(a => a.status === statusFilter);
    return { assignments: items, total: items.length } as T;
  }

  // Create assignment
  if (endpoint.match(/\/me\/assignments/) && method === 'POST') {
    const payload = body as Record<string, unknown>;
    const newAsgn = {
      id: 'asgn_' + Date.now(),
      company_id: 'demo_company_001',
      resource_type: (payload.resource_type as string) || 'worker',
      resource_id: (payload.resource_id as string) || '',
      project_id: (payload.project_id as string) || '',
      role: (payload.role as string) || null,
      start_date: (payload.start_date as string) || new Date().toISOString().split('T')[0],
      end_date: (payload.end_date as string) || null,
      status: (payload.status as string) || 'active',
      notes: (payload.notes as string) || null,
      created_at: new Date().toISOString(),
      created_by: 'demo_user_001',
      updated_at: new Date().toISOString(),
      updated_by: 'demo_user_001',
    };
    DEMO_PROJECT_ASSIGNMENTS.unshift(newAsgn as typeof DEMO_PROJECT_ASSIGNMENTS[0]);
    return newAsgn as T;
  }

  // ---- Analytics Routes ----

  // Analytics dashboard
  if (endpoint.match(/\/me\/analytics\/dashboard/) && method === 'GET') {
    return DEMO_ANALYTICS as T;
  }

  // EMR estimate
  if (endpoint.match(/\/me\/analytics\/emr-estimate/) && method === 'POST') {
    const payload = body as Record<string, unknown>;
    const currentEmr = (payload?.current_emr as number) || 1.0;
    const annualPayroll = (payload?.annual_payroll as number) || 500000;
    const wcRate = (payload?.wc_rate as number) || 15;
    const premiumBase = (annualPayroll / 100) * wcRate;
    const currentPremium = premiumBase * currentEmr;
    const projectedEmr = Math.max(0.7, currentEmr - 0.15);
    const projectedPremium = premiumBase * projectedEmr;
    return {
      current_emr: currentEmr,
      projected_emr: projectedEmr,
      premium_base: premiumBase,
      current_premium: currentPremium,
      projected_premium: projectedPremium,
      potential_savings: currentPremium - projectedPremium,
      recommendations: [
        'Reduce TRIR below industry average of 3.0 to demonstrate safety improvement trend',
        'Close all open hazard reports within 48 hours to show proactive hazard management',
        'Increase toolbox talk frequency to weekly minimum per project',
        'Ensure 100% of workers have current certifications — expired certs signal compliance gaps',
        'Document all near-misses and corrective actions to show strong safety culture to insurers',
      ],
    } as T;
  }

  // ---- Prequalification Routes ----

  // Generate package
  if (endpoint.match(/\/me\/prequalification\/generate/) && method === 'POST') {
    const payload = body as Record<string, unknown>;
    const platform = (payload?.platform as string) || 'isnetworld';
    const clientName = (payload?.client_name as string) || 'Unknown Client';
    // Return existing demo package with overridden platform/client
    const pkg = { ...DEMO_PREQUAL_PACKAGES[0], platform, client_name: clientName, id: 'prequal_' + Date.now(), created_at: new Date().toISOString() };
    return pkg as T;
  }

  // List packages
  if (endpoint.match(/\/me\/prequalification\/packages/) && method === 'GET') {
    return DEMO_PREQUAL_PACKAGES as T;
  }

  // Single package
  const prequalPkgMatch = endpoint.match(/\/me\/prequalification\/packages\/([^/]+)$/);
  if (prequalPkgMatch && method === 'GET') {
    const pkg = DEMO_PREQUAL_PACKAGES.find(p => p.id === prequalPkgMatch[1]);
    return (pkg || DEMO_PREQUAL_PACKAGES[0]) as T;
  }

  // Requirements for platform
  const prequalReqMatch = endpoint.match(/\/me\/prequalification\/requirements\?platform=(\w+)/);
  if (prequalReqMatch || (endpoint.match(/\/me\/prequalification\/requirements/) && method === 'GET')) {
    const platform = prequalReqMatch?.[1] || 'isnetworld';
    return (DEMO_PREQUAL_REQUIREMENTS[platform] || DEMO_PREQUAL_REQUIREMENTS['isnetworld']) as T;
  }

  // ---- GC Portal Routes ----

  // My subs (as GC)
  if (endpoint.match(/\/me\/gc-portal\/my-subs/) && method === 'GET') {
    return DEMO_GC_RELATIONSHIPS as T;
  }

  // My GCs (as sub)
  if (endpoint.match(/\/me\/gc-portal\/my-gcs/) && method === 'GET') {
    return [] as T;
  }

  // Sub compliance
  const subComplianceMatch = endpoint.match(/\/me\/gc-portal\/my-subs\/([^/]+)\/compliance/);
  if (subComplianceMatch && method === 'GET') {
    const sub = DEMO_SUB_COMPLIANCE.find(s => s.sub_company_id === subComplianceMatch[1]);
    return (sub || DEMO_SUB_COMPLIANCE[0]) as T;
  }

  // GC dashboard
  if (endpoint.match(/\/me\/gc-portal\/dashboard/) && method === 'GET') {
    return { relationships: DEMO_GC_RELATIONSHIPS, compliance: DEMO_SUB_COMPLIANCE } as T;
  }

  // Invite sub
  if (endpoint.match(/\/me\/gc-portal\/invite/) && method === 'POST') {
    const payload = body as Record<string, unknown>;
    const newRel = {
      id: 'gcrel_' + Date.now(),
      gc_company_id: 'demo_company_001',
      sub_company_id: 'sub_new_' + Date.now(),
      gc_company_name: 'SafeBuild Construction LLC',
      sub_company_name: (payload?.email as string) || 'New Sub',
      project_name: (payload?.project_name as string) || 'New Project',
      status: 'pending' as const,
      created_at: new Date().toISOString(),
    };
    return newRel as T;
  }

  // ---- State Compliance Routes ----

  // List available states
  if (endpoint === '/me/state-compliance/states' && method === 'GET') {
    return { states: DEMO_AVAILABLE_STATES, total: DEMO_AVAILABLE_STATES.length } as T;
  }

  // Get requirements for a state (path param: /requirements/{stateCode})
  const stateReqMatch = endpoint.match(/\/me\/state-compliance\/requirements\/([^/?]+)/);
  if (stateReqMatch && method === 'GET') {
    const stateCode = decodeURIComponent(stateReqMatch[1]).toUpperCase();
    return (DEMO_STATE_REQUIREMENTS[stateCode] || []) as T;
  }

  // Check compliance for a state (path param: /check/{stateCode})
  const stateCheckMatch = endpoint.match(/\/me\/state-compliance\/check\/([^/?]+)/);
  if (stateCheckMatch && method === 'GET') {
    const stateCode = decodeURIComponent(stateCheckMatch[1]).toUpperCase();
    return (DEMO_STATE_COMPLIANCE_RESULTS[stateCode] || { state: stateCode, total_requirements: 0, met_requirements: 0, compliance_percentage: 0, gaps: [] }) as T;
  }

  // ---- Incident Routes ----

  // AI investigation for incident
  const incidentInvestigateMatch = endpoint.match(/\/me\/projects\/[^/]+\/incidents\/([^/]+)\/investigate$/);
  if (incidentInvestigateMatch && method === 'POST') {
    const idx = DEMO_INCIDENTS.findIndex(i => i.id === incidentInvestigateMatch[1]);
    if (idx !== -1) {
      DEMO_INCIDENTS[idx].ai_analysis = {
        immediate_cause: 'Analysis based on incident description and site conditions. The immediate cause appears to be a failure in standard safety protocols for the specific work activity.',
        contributing_factors: [
          'Insufficient pre-task planning for the specific work conditions',
          'Gap in supervisor oversight during the activity',
          'Environmental or site conditions not adequately addressed',
        ],
        root_causes: [
          'Training gap for the specific hazard encountered',
          'Safety procedure not updated for current site conditions',
          'Lack of job hazard analysis for the specific task',
        ],
        corrective_action_recommendations: [
          'Conduct targeted safety training for the identified hazard',
          'Update job hazard analysis to include the specific risk factors',
          'Implement additional engineering controls or administrative safeguards',
          'Schedule follow-up inspection to verify corrective actions are effective',
        ],
        severity_assessment: 'Analysis complete. Review the findings and corrective action recommendations below.',
      };
      DEMO_INCIDENTS[idx].updated_at = new Date().toISOString();
      return DEMO_INCIDENTS[idx] as T;
    }
    return {} as T;
  }

  // Single incident — GET, PATCH, DELETE
  const incidentMatch = endpoint.match(/\/me\/projects\/[^/]+\/incidents\/([^/?]+)$/);
  if (incidentMatch && (method === 'GET' || method === 'PATCH' || method === 'DELETE')) {
    if (method === 'DELETE') {
      const idx = DEMO_INCIDENTS.findIndex(i => i.id === incidentMatch[1]);
      if (idx !== -1) DEMO_INCIDENTS.splice(idx, 1);
      return undefined as T;
    }
    if (method === 'PATCH') {
      const idx = DEMO_INCIDENTS.findIndex(i => i.id === incidentMatch[1]);
      if (idx !== -1) {
        const payload = body as Record<string, unknown>;
        DEMO_INCIDENTS[idx] = { ...DEMO_INCIDENTS[idx], ...payload, updated_at: new Date().toISOString() } as typeof DEMO_INCIDENTS[0];
        return DEMO_INCIDENTS[idx] as T;
      }
    }
    const incident = DEMO_INCIDENTS.find(i => i.id === incidentMatch[1]);
    if (incident) return incident as T;
    return DEMO_INCIDENTS[0] as T;
  }

  // Incident list
  if (endpoint.match(/\/me\/projects\/[^/]+\/incidents/) && method === 'GET') {
    const url = new URL(endpoint, 'http://localhost');
    const projectId = url.searchParams.get('project_id');
    let filtered = [...DEMO_INCIDENTS];
    if (projectId) {
      filtered = filtered.filter(i => i.project_id === projectId);
    }
    return { incidents: filtered, total: filtered.length } as T;
  }

  // Create incident
  const incidentCreateMatch = endpoint.match(/\/me\/projects\/([^/]+)\/incidents/);
  if (incidentCreateMatch && method === 'POST') {
    const payload = body as Record<string, unknown>;
    const severity = (payload.severity as string) || 'near_miss';
    const oshaRecordable = ['fatality', 'hospitalization', 'medical_treatment'].includes(severity);
    const oshaReportable = ['fatality', 'hospitalization'].includes(severity);
    const newIncident = {
      id: 'demo_incident_new_' + Date.now(),
      company_id: 'demo_company_001',
      project_id: incidentCreateMatch[1],
      incident_date: (payload.incident_date as string) || new Date().toISOString().split('T')[0],
      incident_time: (payload.incident_time as string) || new Date().toTimeString().slice(0, 5),
      location: (payload.location as string) || '',
      severity: severity,
      description: (payload.description as string) || '',
      persons_involved: (payload.persons_involved as string) || '',
      witnesses: (payload.witnesses as string) || '',
      immediate_actions_taken: (payload.immediate_actions_taken as string) || '',
      root_cause: '',
      corrective_actions: '',
      status: 'reported' as const,
      osha_recordable: oshaRecordable,
      osha_reportable: oshaReportable,
      ai_analysis: {},
      photo_urls: (payload.photo_urls as string[]) || [],
      created_at: new Date().toISOString(),
      created_by: 'demo_user_001',
      updated_at: new Date().toISOString(),
    };
    DEMO_INCIDENTS.unshift(newIncident as typeof DEMO_INCIDENTS[0]);
    return newIncident as T;
  }

  // ---- Photo Hazard Analysis Route ----
  if (endpoint.match(/\/me\/analyze-photo/) && method === 'POST') {
    return {
      identified_hazards: [
        {
          hazard_id: 'h_new_' + Date.now(),
          description: 'Unsecured ladder leaning against wall at approximately 60-degree angle without tie-off at the top. Worker ascending without three points of contact.',
          severity: 'high' as const,
          osha_standard: '29 CFR 1926.1053(b)(1)',
          category: 'Ladder Safety',
          recommended_action: 'Secure ladder at top and bottom. Ensure proper 4:1 angle ratio. Workers must maintain three points of contact at all times.',
          location_in_image: 'Center of image',
        },
        {
          hazard_id: 'h_new2_' + Date.now(),
          description: 'Construction debris and loose materials scattered across walking path creating tripping hazards.',
          severity: 'medium' as const,
          osha_standard: '29 CFR 1926.25(a)',
          category: 'Housekeeping',
          recommended_action: 'Clear all debris from walkways immediately. Establish regular housekeeping schedule. Provide designated material staging areas.',
          location_in_image: 'Lower portion of image, walkway area',
        },
      ],
      hazard_count: 2,
      highest_severity: 'high',
      scene_description: 'Construction work area with active renovation. Ladder access point visible with worker ascending. Ground level shows scattered construction materials and debris.',
      positive_observations: ['Workers are wearing hard hats', 'Temporary lighting is adequate'],
      summary: 'Two hazards identified: an unsecured ladder with improper use and housekeeping violations along the main walkway. Immediate corrective action recommended for the ladder hazard.',
    } as T;
  }

  // ---- Hazard Report Routes ----

  // Single hazard report — GET, PATCH
  const hazardReportMatch = endpoint.match(/\/me\/projects\/[^/]+\/hazard-reports\/([^/?]+)$/);
  if (hazardReportMatch && (method === 'GET' || method === 'PATCH')) {
    if (method === 'PATCH') {
      const idx = DEMO_HAZARD_REPORTS.findIndex(r => r.id === hazardReportMatch[1]);
      if (idx !== -1) {
        const payload = body as Record<string, unknown>;
        DEMO_HAZARD_REPORTS[idx] = { ...DEMO_HAZARD_REPORTS[idx], ...payload } as typeof DEMO_HAZARD_REPORTS[0];
        return DEMO_HAZARD_REPORTS[idx] as T;
      }
    }
    const report = DEMO_HAZARD_REPORTS.find(r => r.id === hazardReportMatch[1]);
    if (report) return report as T;
    return DEMO_HAZARD_REPORTS[0] as T;
  }

  // Hazard report list
  if (endpoint.match(/\/me\/projects\/[^/]+\/hazard-reports/) && method === 'GET') {
    const url = new URL(endpoint, 'http://localhost');
    const projectId = url.searchParams.get('project_id');
    let filtered = [...DEMO_HAZARD_REPORTS];
    if (projectId) {
      filtered = filtered.filter(r => r.project_id === projectId);
    }
    return { reports: filtered, total: filtered.length } as T;
  }

  // Create hazard report
  if (endpoint.match(/\/me\/projects\/[^/]+\/hazard-reports/) && method === 'POST') {
    const payload = body as Record<string, unknown>;
    const newReport = {
      id: 'demo_hazard_new_' + Date.now(),
      company_id: 'demo_company_001',
      project_id: (payload.project_id as string) || '',
      photo_url: (payload.photo_url as string) || '',
      description: (payload.description as string) || '',
      location: (payload.location as string) || '',
      gps_latitude: null,
      gps_longitude: null,
      ai_analysis: (payload.ai_analysis as Record<string, unknown>) || {},
      identified_hazards: (payload.identified_hazards as unknown[]) || [],
      hazard_count: (payload.hazard_count as number) || 0,
      highest_severity: (payload.highest_severity as string) || null,
      status: 'open' as const,
      corrective_action_taken: '',
      corrected_at: null,
      created_at: new Date().toISOString(),
      created_by: 'demo_user_001',
    };
    DEMO_HAZARD_REPORTS.unshift(newReport as typeof DEMO_HAZARD_REPORTS[0]);
    return newReport as T;
  }

  // ---- Morning Brief Routes ----

  // Morning brief (today) for a project
  if (endpoint.match(/\/me\/projects\/[^/]+\/morning-brief$/) && method === 'GET') {
    const url = new URL(endpoint, 'http://localhost');
    const projectId = url.searchParams.get('project_id') || '';
    if (DEMO_MORNING_BRIEF.project_id === projectId) {
      return DEMO_MORNING_BRIEF as T;
    }
    // Return a generic brief for other projects
    return { ...DEMO_MORNING_BRIEF, project_id: projectId, id: 'brief_' + projectId } as T;
  }

  // Morning brief history for a project
  if (endpoint.match(/\/me\/projects\/[^/]+\/morning-briefs/) && method === 'GET') {
    const url = new URL(endpoint, 'http://localhost');
    const projectId = url.searchParams.get('project_id') || '';
    const briefs = DEMO_MORNING_BRIEF_HISTORY.filter(b => b.project_id === projectId);
    return { briefs, total: briefs.length } as T;
  }

  // ---- Mock Inspection Routes ----

  // Run mock inspection
  if (endpoint.match(/\/me\/projects\/[^/]+\/inspections\/[^/]+\/run-mock/) && method === 'POST') {
    const payload = body as Record<string, unknown> | undefined;
    const newResult = {
      ...DEMO_MOCK_INSPECTION,
      id: 'mock_' + Date.now(),
      project_id: (payload?.project_id as string) || null,
      inspection_date: new Date().toISOString(),
      created_at: new Date().toISOString(),
    };
    DEMO_MOCK_INSPECTION_RESULTS.unshift(newResult);
    return newResult as T;
  }

  // Single mock inspection result
  const mockResultMatch = endpoint.match(/\/me\/mock-inspection\/results\/([^/?]+)$/);
  if (mockResultMatch && method === 'GET') {
    const result = DEMO_MOCK_INSPECTION_RESULTS.find(r => r.id === mockResultMatch[1]);
    if (result) return result as T;
    return DEMO_MOCK_INSPECTION as T;
  }

  // List mock inspection results
  if (endpoint.match(/\/me\/mock-inspection\/results/) && method === 'GET') {
    return DEMO_MOCK_INSPECTION_RESULTS as T;
  }

  // ---- OSHA Log Routes ----

  // Certify summary
  if (endpoint.match(/\/me\/osha-log\/summary\/certify/) && method === 'POST') {
    const payload = body as Record<string, unknown>;
    DEMO_OSHA_SUMMARY.certified_by = (payload?.certified_by as string) || 'Demo User';
    DEMO_OSHA_SUMMARY.certified_date = new Date().toISOString().split('T')[0];
    DEMO_OSHA_SUMMARY.posted = true;
    return DEMO_OSHA_SUMMARY as T;
  }

  // OSHA 300 Summary
  if (endpoint.match(/\/me\/osha-log\/summary/) && method === 'GET') {
    return DEMO_OSHA_SUMMARY as T;
  }

  // Single OSHA entry — GET, PATCH, DELETE
  const oshaEntryMatch = endpoint.match(/\/me\/osha-log\/entries\/([^/?]+)$/);
  if (oshaEntryMatch && (method === 'GET' || method === 'PATCH' || method === 'DELETE')) {
    if (method === 'DELETE') {
      const idx = DEMO_OSHA_ENTRIES.findIndex(e => e.id === oshaEntryMatch[1]);
      if (idx !== -1) DEMO_OSHA_ENTRIES.splice(idx, 1);
      return undefined as T;
    }
    if (method === 'PATCH') {
      const idx = DEMO_OSHA_ENTRIES.findIndex(e => e.id === oshaEntryMatch[1]);
      if (idx !== -1) {
        const payload = body as Record<string, unknown>;
        DEMO_OSHA_ENTRIES[idx] = { ...DEMO_OSHA_ENTRIES[idx], ...payload, updated_at: new Date().toISOString() } as typeof DEMO_OSHA_ENTRIES[0];
        return DEMO_OSHA_ENTRIES[idx] as T;
      }
    }
    const entry = DEMO_OSHA_ENTRIES.find(e => e.id === oshaEntryMatch[1]);
    if (entry) return entry as T;
    return {} as T;
  }

  // OSHA entries list
  if (endpoint.match(/\/me\/osha-log\/entries/) && method === 'GET') {
    const url = new URL(endpoint, 'http://localhost');
    const year = url.searchParams.get('year');
    let entries = [...DEMO_OSHA_ENTRIES];
    if (year) {
      entries = entries.filter(e => e.date_of_injury.startsWith(year));
    }
    return { entries, total: entries.length } as T;
  }

  // Create OSHA entry
  if (endpoint.match(/\/me\/osha-log\/entries/) && method === 'POST') {
    const payload = body as Record<string, unknown>;
    const maxCase = DEMO_OSHA_ENTRIES.reduce((max, e) => Math.max(max, e.case_number), 0);
    const newEntry = {
      id: 'osha_entry_new_' + Date.now(),
      case_number: maxCase + 1,
      employee_name: (payload.employee_name as string) || '',
      job_title: (payload.job_title as string) || '',
      date_of_injury: (payload.date_of_injury as string) || new Date().toISOString().split('T')[0],
      where_event_occurred: (payload.where_event_occurred as string) || '',
      description: (payload.description as string) || '',
      classification: (payload.classification as string) || 'other_recordable',
      injury_type: (payload.injury_type as string) || 'injury',
      days_away_from_work: (payload.days_away_from_work as number) || 0,
      days_of_restricted_work: (payload.days_of_restricted_work as number) || 0,
      died: (payload.died as boolean) || false,
      privacy_case: (payload.privacy_case as boolean) || false,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };
    DEMO_OSHA_ENTRIES.push(newEntry as typeof DEMO_OSHA_ENTRIES[0]);
    return newEntry as T;
  }

  // ---- Worker & Certification Routes ----

  // Certification matrix
  if (endpoint.match(/\/me\/workers\/certification-matrix/) && method === 'GET') {
    const matrix = DEMO_WORKERS.filter(w => w.status === 'active').map(w => {
      const row: Record<string, string> = { worker_id: w.id, worker_name: `${w.first_name} ${w.last_name}`, role: w.role, trade: w.trade };
      for (const ct of CERTIFICATION_TYPES) {
        const cert = w.certifications.find(c => c.certification_type === ct.id);
        row[ct.id] = cert ? cert.status : 'missing';
      }
      return row;
    });
    return { matrix, total: matrix.length } as T;
  }

  // Expiring certifications
  if (endpoint.match(/\/me\/workers\/expiring-certifications/) && method === 'GET') {
    const url = new URL(endpoint, 'http://localhost');
    const days = parseInt(url.searchParams.get('days') || '30', 10);
    const now = new Date();
    const cutoff = new Date(now.getTime() + days * 24 * 60 * 60 * 1000);
    const results: Array<{ worker_id: string; worker_name: string; certification: Certification }> = [];
    for (const w of DEMO_WORKERS) {
      for (const c of w.certifications) {
        if (c.expiry_date) {
          const exp = new Date(c.expiry_date);
          if (exp <= cutoff) {
            results.push({ worker_id: w.id, worker_name: `${w.first_name} ${w.last_name}`, certification: c });
          }
        }
      }
    }
    return { certifications: results, total: results.length } as T;
  }

  // Single worker certification — PATCH or DELETE
  const certMatch = endpoint.match(/\/me\/workers\/([^/]+)\/certifications\/([^/?]+)$/);
  if (certMatch && (method === 'PATCH' || method === 'DELETE')) {
    const wIdx = DEMO_WORKERS.findIndex(w => w.id === certMatch[1]);
    if (wIdx !== -1) {
      if (method === 'DELETE') {
        DEMO_WORKERS[wIdx].certifications = DEMO_WORKERS[wIdx].certifications.filter(c => c.id !== certMatch[2]);
        DEMO_WORKERS[wIdx].total_certifications = DEMO_WORKERS[wIdx].certifications.length;
        DEMO_WORKERS[wIdx].expired = DEMO_WORKERS[wIdx].certifications.filter(c => c.status === 'expired').length;
        DEMO_WORKERS[wIdx].expiring_soon = DEMO_WORKERS[wIdx].certifications.filter(c => c.status === 'expiring_soon').length;
        return undefined as T;
      }
      const cIdx = DEMO_WORKERS[wIdx].certifications.findIndex(c => c.id === certMatch[2]);
      if (cIdx !== -1) {
        const payload = body as Record<string, unknown>;
        DEMO_WORKERS[wIdx].certifications[cIdx] = { ...DEMO_WORKERS[wIdx].certifications[cIdx], ...payload } as Certification;
        return DEMO_WORKERS[wIdx].certifications[cIdx] as T;
      }
    }
    return {} as T;
  }

  // Add certification to worker
  const addCertMatch = endpoint.match(/\/me\/workers\/([^/]+)\/certifications$/);
  if (addCertMatch && method === 'POST') {
    const wIdx = DEMO_WORKERS.findIndex(w => w.id === addCertMatch[1]);
    if (wIdx !== -1) {
      const payload = body as Record<string, unknown>;
      const newCert: Certification = {
        id: 'cert_new_' + Date.now(),
        certification_type: (payload.certification_type as string) || 'other',
        custom_name: (payload.custom_name as string) || '',
        issued_date: (payload.issued_date as string) || new Date().toISOString().split('T')[0],
        expiry_date: (payload.expiry_date as string | null) || null,
        issuing_body: (payload.issuing_body as string) || '',
        certificate_number: (payload.certificate_number as string) || '',
        proof_document_url: null,
        status: (payload.status as 'valid' | 'expired' | 'expiring_soon') || 'valid',
        notes: (payload.notes as string) || '',
      };
      DEMO_WORKERS[wIdx].certifications.push(newCert);
      DEMO_WORKERS[wIdx].total_certifications = DEMO_WORKERS[wIdx].certifications.length;
      DEMO_WORKERS[wIdx].expired = DEMO_WORKERS[wIdx].certifications.filter(c => c.status === 'expired').length;
      DEMO_WORKERS[wIdx].expiring_soon = DEMO_WORKERS[wIdx].certifications.filter(c => c.status === 'expiring_soon').length;
      DEMO_WORKERS[wIdx].updated_at = new Date().toISOString();
      return newCert as T;
    }
    return {} as T;
  }

  // Single worker — GET, PATCH, DELETE
  const workerMatch = endpoint.match(/\/me\/workers\/([^/?]+)$/);
  if (workerMatch && (method === 'GET' || method === 'PATCH' || method === 'DELETE')) {
    if (method === 'DELETE') {
      const idx = DEMO_WORKERS.findIndex(w => w.id === workerMatch[1]);
      if (idx !== -1) DEMO_WORKERS.splice(idx, 1);
      return undefined as T;
    }
    if (method === 'PATCH') {
      const idx = DEMO_WORKERS.findIndex(w => w.id === workerMatch[1]);
      if (idx !== -1) {
        const payload = body as Record<string, unknown>;
        DEMO_WORKERS[idx] = { ...DEMO_WORKERS[idx], ...payload, updated_at: new Date().toISOString() } as typeof DEMO_WORKERS[0];
        return DEMO_WORKERS[idx] as T;
      }
    }
    const worker = DEMO_WORKERS.find(w => w.id === workerMatch[1]);
    if (worker) return worker as T;
    return {} as T;
  }

  // Workers list
  if (endpoint.match(/\/me\/workers/) && method === 'GET') {
    const url = new URL(endpoint, 'http://localhost');
    const status = url.searchParams.get('status');
    const role = url.searchParams.get('role');
    const trade = url.searchParams.get('trade');
    const search = url.searchParams.get('search');
    let workers = [...DEMO_WORKERS];
    if (status) workers = workers.filter(w => w.status === status);
    if (role) workers = workers.filter(w => w.role === role);
    if (trade) workers = workers.filter(w => w.trade === trade);
    if (search) {
      const s = search.toLowerCase();
      workers = workers.filter(w => `${w.first_name} ${w.last_name}`.toLowerCase().includes(s));
    }
    return { workers, total: workers.length } as T;
  }

  // Create worker
  if (endpoint.match(/\/me\/workers/) && method === 'POST') {
    const payload = body as Record<string, unknown>;
    const newWorker = {
      id: 'demo_wkr_new_' + Date.now(),
      company_id: 'demo_company_001',
      first_name: (payload.first_name as string) || '',
      last_name: (payload.last_name as string) || '',
      email: (payload.email as string) || '',
      phone: (payload.phone as string) || '',
      role: (payload.role as string) || 'laborer',
      trade: (payload.trade as string) || 'general',
      language_preference: (payload.language_preference as 'en' | 'es' | 'both') || 'en',
      emergency_contact_name: (payload.emergency_contact_name as string) || '',
      emergency_contact_phone: (payload.emergency_contact_phone as string) || '',
      hire_date: (payload.hire_date as string) || null,
      notes: (payload.notes as string) || '',
      status: 'active' as const,
      certifications: [],
      total_certifications: 0,
      expiring_soon: 0,
      expired: 0,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };
    DEMO_WORKERS.unshift(newWorker as typeof DEMO_WORKERS[0]);
    return newWorker as T;
  }

  // Toolbox talk complete
  const talkCompleteMatch = endpoint.match(/\/me\/projects\/[^/]+\/toolbox-talks\/([^/]+)\/complete$/);
  if (talkCompleteMatch && method === 'POST') {
    const idx = DEMO_TOOLBOX_TALKS.findIndex((t) => t.id === talkCompleteMatch[1]);
    if (idx !== -1) {
      DEMO_TOOLBOX_TALKS[idx] = {
        ...DEMO_TOOLBOX_TALKS[idx],
        status: 'completed',
        presented_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      };
      return DEMO_TOOLBOX_TALKS[idx] as T;
    }
    return {} as T;
  }

  // Toolbox talk attend
  const talkAttendMatch = endpoint.match(/\/me\/projects\/[^/]+\/toolbox-talks\/([^/]+)\/attend$/);
  if (talkAttendMatch && method === 'POST') {
    const idx = DEMO_TOOLBOX_TALKS.findIndex((t) => t.id === talkAttendMatch[1]);
    if (idx !== -1) {
      const payload = body as Record<string, unknown>;
      const attendee = {
        worker_name: (payload?.worker_name as string) || '',
        signature_data: 'signed',
        signed_at: new Date().toISOString(),
        language_preference: (payload?.language_preference as 'en' | 'es') || 'en',
      };
      DEMO_TOOLBOX_TALKS[idx].attendees.push(attendee);
      DEMO_TOOLBOX_TALKS[idx].updated_at = new Date().toISOString();
      return DEMO_TOOLBOX_TALKS[idx] as T;
    }
    return {} as T;
  }

  // Single toolbox talk — GET, PATCH, DELETE
  const talkMatch = endpoint.match(/\/me\/projects\/[^/]+\/toolbox-talks\/([^/?]+)$/);
  if (talkMatch && (method === 'GET' || method === 'PATCH' || method === 'DELETE')) {
    if (method === 'DELETE') {
      const idx = DEMO_TOOLBOX_TALKS.findIndex((t) => t.id === talkMatch[1]);
      if (idx !== -1) DEMO_TOOLBOX_TALKS.splice(idx, 1);
      return undefined as T;
    }
    if (method === 'PATCH') {
      const idx = DEMO_TOOLBOX_TALKS.findIndex((t) => t.id === talkMatch[1]);
      if (idx !== -1) {
        const payload = body as Record<string, unknown>;
        DEMO_TOOLBOX_TALKS[idx] = { ...DEMO_TOOLBOX_TALKS[idx], ...payload, updated_at: new Date().toISOString() } as typeof DEMO_TOOLBOX_TALKS[0];
        return DEMO_TOOLBOX_TALKS[idx] as T;
      }
    }
    const talk = DEMO_TOOLBOX_TALKS.find((t) => t.id === talkMatch[1]);
    if (talk) return talk as T;
    return DEMO_TOOLBOX_TALKS[0] as T;
  }

  // Toolbox talk list
  if (endpoint.match(/\/me\/projects\/[^/]+\/toolbox-talks/) && method === 'GET') {
    const url = new URL(endpoint, 'http://localhost');
    const projectId = url.searchParams.get('project_id');
    let filtered = [...DEMO_TOOLBOX_TALKS];
    if (projectId) {
      filtered = filtered.filter((t) => t.project_id === projectId);
    }
    return { toolbox_talks: filtered, total: filtered.length } as T;
  }

  // Create toolbox talk
  if (endpoint.match(/\/me\/projects\/[^/]+\/toolbox-talks/) && method === 'POST') {
    const payload = body as Record<string, unknown>;
    const newTalk = {
      id: 'demo_talk_new_' + Date.now(),
      company_id: 'demo_company_001',
      project_id: (payload.project_id as string) || '',
      topic: (payload?.topic as string) || 'New Talk',
      scheduled_date: new Date().toISOString().split('T')[0],
      target_audience: (payload?.target_audience as string) || 'all_workers',
      target_trade: (payload?.target_trade as string) || null,
      duration_minutes: (payload?.duration_minutes as number) || 15,
      custom_points: (payload?.custom_points as string) || '',
      content_en: {
        topic_overview: 'AI-generated content will appear here in production. This is a demo placeholder for the topic: ' + ((payload?.topic as string) || 'New Talk'),
        key_points: [
          { point_title: 'Key Safety Point 1', explanation: 'Detailed explanation will be generated by AI based on the topic and your site conditions.', osha_reference: 'Relevant OSHA Standard' },
          { point_title: 'Key Safety Point 2', explanation: 'Another important safety point covering best practices and regulatory requirements.', osha_reference: 'Relevant OSHA Standard' },
          { point_title: 'Key Safety Point 3', explanation: 'A third key point covering practical implementation steps for the crew.', osha_reference: 'Relevant OSHA Standard' },
        ],
        discussion_questions: ['What are the main hazards related to this topic on our site?', 'Has anyone had experience with this type of situation?', 'What can we do differently to improve safety?'],
        safety_reminders: ['Always follow established safety procedures', 'Report any concerns to your supervisor immediately', 'Look out for your coworkers'],
        osha_references: ['Relevant OSHA Standards will be listed here'],
      },
      content_es: {
        topic_overview: 'El contenido generado por IA aparecera aqui en produccion. Este es un marcador de posicion de demostracion para el tema: ' + ((payload?.topic as string) || 'Nueva Charla'),
        key_points: [
          { point_title: 'Punto Clave de Seguridad 1', explanation: 'La explicacion detallada sera generada por IA basada en el tema y las condiciones de su sitio.', osha_reference: 'Estandar OSHA Relevante' },
          { point_title: 'Punto Clave de Seguridad 2', explanation: 'Otro punto importante de seguridad cubriendo mejores practicas y requisitos regulatorios.', osha_reference: 'Estandar OSHA Relevante' },
          { point_title: 'Punto Clave de Seguridad 3', explanation: 'Un tercer punto clave cubriendo pasos practicos de implementacion para el equipo.', osha_reference: 'Estandar OSHA Relevante' },
        ],
        discussion_questions: ['Cuales son los principales peligros relacionados con este tema en nuestro sitio?', 'Alguien ha tenido experiencia con este tipo de situacion?', 'Que podemos hacer diferente para mejorar la seguridad?'],
        safety_reminders: ['Siempre siga los procedimientos de seguridad establecidos', 'Reporte cualquier preocupacion a su supervisor inmediatamente', 'Cuide a sus companeros de trabajo'],
        osha_references: ['Los Estandares OSHA Relevantes se listaran aqui'],
      },
      status: 'scheduled' as const,
      attendees: [],
      overall_notes: '',
      presented_at: null,
      presented_by: '',
      created_at: new Date().toISOString(),
      created_by: 'demo_user_001',
      updated_at: new Date().toISOString(),
      updated_by: 'demo_user_001',
    };
    DEMO_TOOLBOX_TALKS.unshift(newTalk as typeof DEMO_TOOLBOX_TALKS[0]);
    return newTalk as T;
  }

  // Inspection templates — return items array (matching real API response shape)
  if (endpoint.match(/\/me\/inspection-templates\//) && method === 'GET') {
    return DAILY_SITE_INSPECTION_TEMPLATE.items as T;
  }

  // Single inspection — GET, PATCH, DELETE
  const inspMatch = endpoint.match(/\/me\/projects\/[^/]+\/inspections\/([^/?]+)$/);
  if (inspMatch && (method === 'GET' || method === 'PATCH' || method === 'DELETE')) {
    if (method === 'DELETE') {
      const idx = DEMO_INSPECTIONS.findIndex((i) => i.id === inspMatch[1]);
      if (idx !== -1) DEMO_INSPECTIONS.splice(idx, 1);
      return undefined as T;
    }
    if (method === 'PATCH') {
      const idx = DEMO_INSPECTIONS.findIndex((i) => i.id === inspMatch[1]);
      if (idx !== -1) {
        const payload = body as Record<string, unknown>;
        DEMO_INSPECTIONS[idx] = { ...DEMO_INSPECTIONS[idx], ...payload, updated_at: new Date().toISOString() } as typeof DEMO_INSPECTIONS[0];
        return DEMO_INSPECTIONS[idx] as T;
      }
    }
    const insp = DEMO_INSPECTIONS.find((i) => i.id === inspMatch[1]);
    if (insp) return insp as T;
    return DEMO_INSPECTIONS[0] as T;
  }

  // Inspection list
  if (endpoint.match(/\/me\/projects\/[^/]+\/inspections/) && method === 'GET') {
    const url = new URL(endpoint, 'http://localhost');
    const projectId = url.searchParams.get('project_id');
    let filtered = [...DEMO_INSPECTIONS];
    if (projectId) {
      filtered = filtered.filter((i) => i.project_id === projectId);
    }
    return { inspections: filtered, total: filtered.length } as T;
  }

  // Create inspection
  if (endpoint.match(/\/me\/projects\/[^/]+\/inspections/) && method === 'POST') {
    const payload = body as Record<string, unknown>;
    const newInsp = {
      id: 'demo_insp_new_' + Date.now(),
      company_id: 'demo_company_001',
      project_id: (payload.project_id as string) || '',
      inspection_type: (payload?.inspection_type as string) || 'daily_site',
      inspection_date: (payload?.inspection_date as string) || new Date().toISOString().split('T')[0],
      inspector_name: (payload?.inspector_name as string) || 'Demo Inspector',
      weather_conditions: (payload?.weather_conditions as string) || '',
      temperature: (payload?.temperature as string) || '',
      wind_conditions: (payload?.wind_conditions as string) || '',
      workers_on_site: (payload?.workers_on_site as number) || 0,
      items: (payload?.items as unknown[]) || [],
      overall_notes: (payload?.overall_notes as string) || '',
      corrective_actions_needed: (payload?.corrective_actions_needed as string) || '',
      overall_status: (payload?.overall_status as string) || 'pass',
      gps_latitude: null,
      gps_longitude: null,
      created_at: new Date().toISOString(),
      created_by: 'demo_user_001',
      updated_at: new Date().toISOString(),
      updated_by: 'demo_user_001',
    };
    DEMO_INSPECTIONS.unshift(newInsp as typeof DEMO_INSPECTIONS[0]);
    return newInsp as T;
  }

  // Single project — GET, PATCH, DELETE (must match before project list)
  const projMatch = endpoint.match(/\/me\/projects\/([^/?]+)$/);
  if (projMatch && (method === 'GET' || method === 'PATCH' || method === 'DELETE')) {
    if (method === 'DELETE') {
      const idx = DEMO_PROJECTS.findIndex((p) => p.id === projMatch[1]);
      if (idx !== -1) DEMO_PROJECTS.splice(idx, 1);
      return undefined as T;
    }
    if (method === 'PATCH') {
      const idx = DEMO_PROJECTS.findIndex((p) => p.id === projMatch[1]);
      if (idx !== -1) {
        const payload = body as Record<string, unknown>;
        DEMO_PROJECTS[idx] = { ...DEMO_PROJECTS[idx], ...payload, updated_at: new Date().toISOString() } as typeof DEMO_PROJECTS[0];
        return DEMO_PROJECTS[idx] as T;
      }
    }
    const proj = DEMO_PROJECTS.find((p) => p.id === projMatch[1]);
    if (proj) return proj as T;
    return DEMO_PROJECTS[0] as T;
  }

  // Projects list
  if (endpoint.match(/\/me\/projects/) && method === 'GET') {
    const url = new URL(endpoint, 'http://localhost');
    const status = url.searchParams.get('status');
    let projects = [...DEMO_PROJECTS];
    if (status) projects = projects.filter((p) => p.status === status);
    return { projects, total: projects.length } as T;
  }

  // Create project
  if (endpoint.match(/\/me\/projects/) && method === 'POST') {
    const payload = body as Record<string, unknown>;
    const newProj = {
      id: 'demo_proj_new_' + Date.now(),
      company_id: 'demo_company_001',
      name: (payload?.name as string) || 'New Project',
      address: (payload?.address as string) || '',
      client_name: (payload?.client_name as string) || '',
      project_type: (payload?.project_type as string) || 'commercial',
      trade_types: (payload?.trade_types as string[]) || [],
      start_date: (payload?.start_date as string) || null,
      end_date: (payload?.end_date as string) || null,
      estimated_workers: (payload?.estimated_workers as number) || 0,
      description: (payload?.description as string) || '',
      special_hazards: (payload?.special_hazards as string) || '',
      nearest_hospital: (payload?.nearest_hospital as string) || '',
      emergency_contact_name: (payload?.emergency_contact_name as string) || '',
      emergency_contact_phone: (payload?.emergency_contact_phone as string) || '',
      status: 'active' as const,
      compliance_score: 0,
      created_at: new Date().toISOString(),
      created_by: 'demo_user_001',
      updated_at: new Date().toISOString(),
      updated_by: 'demo_user_001',
    };
    DEMO_PROJECTS.unshift(newProj as typeof DEMO_PROJECTS[0]);
    return newProj as T;
  }

  // Document stats — check before generic documents match
  if (endpoint.match(/\/me\/documents\/stats/) && method === 'GET') {
    return DEMO_STATS as T;
  }

  // PDF export
  if (endpoint.match(/\/me\/documents\/[^/]+\/pdf/) && method === 'GET') {
    // Can't produce a real blob in demo mode — caller handles this
    return { demo: true, message: 'PDF export available in production mode' } as T;
  }

  // Generate (demo)
  if (endpoint.match(/\/me\/documents\/[^/]+\/generate/) && method === 'POST') {
    return { status: 'generated', message: 'Demo generation complete' } as T;
  }

  // Single document — PATCH or GET
  const docMatch = endpoint.match(/\/me\/documents\/([^/?]+)$/);
  if (docMatch && (method === 'GET' || method === 'PATCH' || method === 'DELETE')) {
    if (method === 'DELETE') {
      const idx = DEMO_DOCUMENTS.findIndex((d) => d.id === docMatch[1]);
      if (idx !== -1) DEMO_DOCUMENTS.splice(idx, 1);
      return undefined as T;
    }
    if (method === 'PATCH') {
      const idx = DEMO_DOCUMENTS.findIndex((d) => d.id === docMatch[1]);
      if (idx !== -1) {
        const payload = body as Record<string, unknown>;
        DEMO_DOCUMENTS[idx] = {
          ...DEMO_DOCUMENTS[idx],
          ...payload,
          updated_at: new Date().toISOString(),
        } as typeof DEMO_DOCUMENTS[0];
        return DEMO_DOCUMENTS[idx] as T;
      }
    }
    const doc = DEMO_DOCUMENTS.find((d) => d.id === docMatch[1]);
    if (doc) return doc as T;
    return DEMO_DOCUMENTS[0] as T;
  }

  // Documents list with pagination params
  if (endpoint.match(/\/me\/documents/) && method === 'GET') {
    // Parse query params for filtering
    const url = new URL(endpoint, 'http://localhost');
    const type = url.searchParams.get('type');
    const status = url.searchParams.get('status');
    const limit = parseInt(url.searchParams.get('limit') || '20', 10);
    const sort = url.searchParams.get('sort');

    let docs = [...DEMO_DOCUMENTS];
    if (type) docs = docs.filter((d) => d.document_type === type);
    if (status) docs = docs.filter((d) => d.status === status);
    if (sort === 'created_at:desc') {
      docs.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());
    }
    const sliced = docs.slice(0, limit);
    return { documents: sliced, total: sliced.length } as T;
  }

  // Create document (demo)
  if (endpoint.match(/\/me\/documents/) && method === 'POST') {
    const payload = body as Record<string, unknown>;
    const newDoc = {
      id: 'demo_doc_new_' + Date.now(),
      company_id: 'demo_company_001',
      title: (payload?.title as string) || 'New Document',
      document_type: (payload?.document_type as string) || 'sssp',
      status: 'draft' as const,
      content: {
        generating: 'In demo mode, document generation is simulated. In production, this calls the AI to generate OSHA-compliant content based on your project details.',
      },
      project_info: (payload?.project_info as Record<string, string>) || {},
      created_at: new Date().toISOString(),
      created_by: 'demo_user_001',
      updated_at: new Date().toISOString(),
      updated_by: 'demo_user_001',
    };
    DEMO_DOCUMENTS.unshift(newDoc as typeof DEMO_DOCUMENTS[0]);
    return newDoc as T;
  }

  // Company
  if (endpoint.match(/\/me\/company/) && method === 'GET') {
    return DEMO_COMPANY as T;
  }
  if (endpoint.match(/\/me\/company/) && method === 'PATCH') {
    Object.assign(DEMO_COMPANY, body);
    return DEMO_COMPANY as T;
  }

  // Subscription
  if (endpoint.match(/\/me\/subscription/)) {
    return {
      status: 'free',
      plan_id: null,
      plan_name: 'Free',
      max_projects: 1,
      renewal_date: null,
      features: ['Limited document generation'],
      is_trial: true,
      trial_days_remaining: 12,
      trial_end_date: new Date(Date.now() + 12 * 24 * 60 * 60 * 1000).toISOString(),
    } as T;
  }

  // Templates
  if (endpoint.includes('/templates') && method === 'GET') {
    return [] as T;
  }

  // Members
  if (endpoint.match(/\/me\/members\/invitations/) && method === 'GET') {
    return [] as T;
  }
  if (endpoint.match(/\/me\/members/) && method === 'GET') {
    return [
      {
        id: 'mem_001',
        company_id: 'demo_company',
        uid: 'demo_user_001',
        email: 'demo@kerf.build',
        display_name: 'Demo Contractor',
        role: 'owner',
        invited_by: null,
        joined_at: '2026-03-15T10:00:00Z',
        created_at: '2026-03-15T10:00:00Z',
        updated_at: '2026-03-15T10:00:00Z',
      },
    ] as T;
  }

  // Default fallback
  return {} as T;
}

/**
 * Token getter injected by the auth provider at runtime.
 * This avoids a circular dependency between api.ts and Clerk hooks.
 */
let _tokenGetter: (() => Promise<string | null>) | null = null;

export function setTokenGetter(getter: () => Promise<string | null>): void {
  _tokenGetter = getter;
}

export async function getAuthToken(): Promise<string | null> {
  // Always defer to the registered token getter when present. The auth
  // providers register an alias-aware getter (demo-token-<alias>) for demo
  // mode AND a Clerk JWT getter for real auth, so this single path covers
  // both. Falling back to a hardcoded "demo-token" here would silently
  // ignore the active demo-user alias and break tenant isolation.
  if (_tokenGetter) return _tokenGetter();
  if (isDemoMode()) return `demo-token-${sessionStorage.getItem('kerf_demo_user') || 'gp04'}`;
  return null;
}

async function request<T>(endpoint: string, options: ApiOptions = {}): Promise<T> {
  // All requests (including demo mode) hit the real backend.
  // The demo-token is accepted by the backend in development mode.
  const { body, headers: customHeaders, ...rest } = options;
  const token = await getAuthToken();

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...customHeaders as Record<string, string>,
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const config: RequestInit = {
    ...rest,
    headers,
  };

  if (body !== undefined) {
    config.body = JSON.stringify(body);
  }

  let response: Response;
  try {
    response = await fetch(`${BASE_URL}${endpoint}`, config);
  } catch {
    toast.error('Unable to connect to server');
    throw new ApiError(0, 'Network error: Unable to connect to server');
  }

  if (!response.ok) {
    if (response.status === 401) {
      window.location.href = '/login';
      throw new ApiError(401, 'Unauthorized');
    }
    if (response.status === 403) {
      window.location.href = '/billing';
      throw new ApiError(403, 'Subscription required');
    }

    let errorData: unknown;
    try {
      errorData = await response.json();
    } catch {
      errorData = null;
    }

    let errorMessage = `API Error: ${response.statusText}`;
    if (errorData && typeof errorData === 'object' && 'detail' in errorData) {
      const detail = (errorData as { detail: unknown }).detail;
      if (typeof detail === 'string') {
        errorMessage = detail;
      } else if (Array.isArray(detail)) {
        // FastAPI validation errors return [{msg, loc, type}, ...]
        errorMessage = detail.map((e: { msg?: string }) => e.msg || String(e)).join(', ');
      } else {
        errorMessage = JSON.stringify(detail);
      }
    }

    if (response.status === 402) {
      toast.error('Please upgrade your plan to access this feature');
    } else if (response.status >= 500) {
      toast.error('Something went wrong, please try again');
    } else {
      toast.error(errorMessage);
    }

    throw new ApiError(response.status, errorMessage, errorData);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json();
}

export const api = {
  get: <T>(endpoint: string, options?: ApiOptions) =>
    request<T>(endpoint, { ...options, method: 'GET' }),

  post: <T>(endpoint: string, body?: unknown, options?: ApiOptions) =>
    request<T>(endpoint, { ...options, method: 'POST', body }),

  put: <T>(endpoint: string, body?: unknown, options?: ApiOptions) =>
    request<T>(endpoint, { ...options, method: 'PUT', body }),

  patch: <T>(endpoint: string, body?: unknown, options?: ApiOptions) =>
    request<T>(endpoint, { ...options, method: 'PATCH', body }),

  delete: <T>(endpoint: string, options?: ApiOptions) =>
    request<T>(endpoint, { ...options, method: 'DELETE' }),
};

export { ApiError };
