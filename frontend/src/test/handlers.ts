import { http, HttpResponse } from 'msw'

const BASE = 'http://localhost:8000/api/v1'

export const handlers = [
  // Auth
  http.post(`${BASE}/auth/verify-token`, () =>
    HttpResponse.json({
      user: { uid: 'test-uid', email: 'test@example.com', email_verified: true },
      company: { id: 'comp_test', name: 'Test Co' },
      is_new_user: false,
    }),
  ),

  // Company
  http.get(`${BASE}/me/company`, () =>
    HttpResponse.json({ id: 'comp_test', name: 'Test Co', trade_type: 'general' }),
  ),

  // Documents
  http.get(`${BASE}/me/documents`, () =>
    HttpResponse.json({ documents: [{ id: 'doc_1', title: 'Test Doc', document_type: 'sssp', status: 'draft' }], total: 1 }),
  ),
  http.get(`${BASE}/me/documents/stats`, () =>
    HttpResponse.json({ total: 5, this_month: 2, monthly_limit: 10, by_type: {}, by_status: {} }),
  ),
  http.get(`${BASE}/me/documents/:id`, ({ params }) =>
    HttpResponse.json({ id: params.id, title: 'Test Doc', document_type: 'sssp', status: 'draft' }),
  ),
  http.post(`${BASE}/me/documents`, () =>
    HttpResponse.json({ id: 'doc_new', title: 'New Doc', document_type: 'sssp', status: 'draft' }, { status: 201 }),
  ),

  // Projects
  http.get(`${BASE}/me/projects`, () =>
    HttpResponse.json({ projects: [{ id: 'proj_1', name: 'Test Project', status: 'active' }], total: 1 }),
  ),
  http.get(`${BASE}/me/projects/:id`, ({ params }) =>
    HttpResponse.json({ id: params.id, name: 'Test Project', status: 'active' }),
  ),
  http.post(`${BASE}/me/projects`, () =>
    HttpResponse.json({ id: 'proj_new', name: 'New Project', status: 'active' }, { status: 201 }),
  ),

  // Inspections (nested under projects)
  http.get(`${BASE}/me/projects/:projectId/inspections`, () =>
    HttpResponse.json({ inspections: [{ id: 'insp_1', inspection_type: 'daily', overall_status: 'pass' }], total: 1 }),
  ),
  http.get(`${BASE}/me/projects/:projectId/inspections/:id`, ({ params }) =>
    HttpResponse.json({ id: params.id, inspection_type: 'daily', overall_status: 'pass' }),
  ),
  http.post(`${BASE}/me/projects/:projectId/inspections`, () =>
    HttpResponse.json({ id: 'insp_new', inspection_type: 'daily', overall_status: 'pass' }, { status: 201 }),
  ),

  // Toolbox Talks (nested under projects)
  http.get(`${BASE}/me/projects/:projectId/toolbox-talks`, () =>
    HttpResponse.json({ toolbox_talks: [{ id: 'talk_1', topic: 'Safety', status: 'scheduled' }], total: 1 }),
  ),
  http.get(`${BASE}/me/projects/:projectId/toolbox-talks/:id`, ({ params }) =>
    HttpResponse.json({ id: params.id, topic: 'Safety', status: 'scheduled' }),
  ),
  http.post(`${BASE}/me/projects/:projectId/toolbox-talks`, () =>
    HttpResponse.json({ id: 'talk_new', topic: 'New Talk', status: 'scheduled' }, { status: 201 }),
  ),

  // Hazard Reports (nested under projects)
  http.get(`${BASE}/me/projects/:projectId/hazard-reports`, () =>
    HttpResponse.json({ reports: [{ id: 'hr_1', description: 'Test hazard', status: 'open' }], total: 1 }),
  ),
  http.post(`${BASE}/me/projects/:projectId/hazard-reports`, () =>
    HttpResponse.json({ id: 'hr_new', description: 'New hazard', status: 'open' }, { status: 201 }),
  ),

  // Incidents (nested under projects)
  http.get(`${BASE}/me/projects/:projectId/incidents`, () =>
    HttpResponse.json({ incidents: [{ id: 'inc_1', description: 'Test incident', severity: 'minor' }], total: 1 }),
  ),
  http.post(`${BASE}/me/projects/:projectId/incidents`, () =>
    HttpResponse.json({ id: 'inc_new', description: 'New incident', severity: 'minor' }, { status: 201 }),
  ),

  // Morning Briefs (nested under projects)
  http.get(`${BASE}/me/projects/:projectId/morning-brief`, () =>
    HttpResponse.json({ id: 'mb_1', date: '2026-04-03', summary: 'All clear' }),
  ),
  http.get(`${BASE}/me/projects/:projectId/morning-briefs`, () =>
    HttpResponse.json({ briefs: [{ id: 'mb_1', date: '2026-04-03', summary: 'All clear' }], total: 1 }),
  ),

  // Workers
  http.get(`${BASE}/me/workers`, () =>
    HttpResponse.json({ workers: [{ id: 'wrk_1', first_name: 'John', last_name: 'Doe', status: 'active' }], total: 1 }),
  ),
  http.get(`${BASE}/me/workers/expiring-certifications`, () =>
    HttpResponse.json({ certifications: [], total: 0 }),
  ),
  http.get(`${BASE}/me/workers/certification-matrix`, () =>
    HttpResponse.json({ matrix: [], total: 0 }),
  ),

  // OSHA Log
  http.get(`${BASE}/me/osha-log/entries`, () =>
    HttpResponse.json({ entries: [{ id: 'osha_1', employee_name: 'Jane Doe' }], total: 1 }),
  ),

  // Equipment
  http.get(`${BASE}/me/equipment`, () =>
    HttpResponse.json({ equipment: [{ id: 'eq_1', name: 'Excavator', status: 'active' }], total: 1 }),
  ),
  http.get(`${BASE}/me/equipment/summary`, () =>
    HttpResponse.json({ total_equipment: 5, by_type: {}, by_status: {}, overdue_inspections: 0, overdue_maintenance: 0 }),
  ),

  // Environmental
  http.get(`${BASE}/me/environmental/programs`, () =>
    HttpResponse.json({ programs: [{ id: 'env_1', program_type: 'silica', status: 'active' }], total: 1 }),
  ),
  http.get(`${BASE}/me/environmental/compliance-status`, () =>
    HttpResponse.json({ overall_status: 'compliant', areas: [], total_programs: 1 }),
  ),
]
